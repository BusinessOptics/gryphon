import boto3
# TODO from aws_classes import Task ......
from aws_classes import Task, TaskDefinition, Instance, Container, Cluster
from collections import defaultdict

boto3.setup_default_session(region_name='us-east-1')
ecs = boto3.client('ecs')
ec2 = boto3.resource('ec2')
auto_scaling = boto3.client('autoscaling')
insts = ec2.instances.filter(
    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])


def create_clusters():
    clusters = {}
    arns = ecs.list_clusters()['clusterArns']
    cluster_keys = []
    for arn in arns:
        if clusters.get(arn):
            continue
        cluster_keys.append(arn)
    if cluster_keys:
        cluster_info = ecs.describe_clusters(clusters=cluster_keys)['clusters']
        for cluster in cluster_info:
            c_arn = cluster['clusterArn']
            temp_cluster = Cluster(arn=c_arn, name=cluster['clusterName'])
            clusters[c_arn] = temp_cluster
    return clusters


def cluster_details(cluster_arn):
    tasks = {}
    instances = {}
    containers = {}
    task_defs = {}

    task_keys = ecs.list_tasks(cluster=cluster_arn)['taskArns']

    if not task_keys:
        return None

    task_info = ecs.describe_tasks(cluster=cluster_arn, tasks=task_keys)['tasks']
    cont_inst_arn = defaultdict(list)
    task_dict = defaultdict(list)
    for task in task_info:
        for cont in task['containers']:
            container_arn = cont['containerArn']
            containers[container_arn] = Container(arn=container_arn,
                                                              name=cont['name'],
                                                              task=task['taskArn'])
        task_arn = task['taskArn']
        cont_inst_arn[task['containerInstanceArn']].append(task['taskArn'])
        tasks[task_arn] = Task(arn=task_arn,
                                           definition=task['taskDefinitionArn'],
                                           containers=containers.keys(),
                                           cluster=cluster_arn,
                                           instance=None)
        task_dict[task['taskDefinitionArn']].append(task_arn)

    for task_def_arn, child_task_arns in task_dict.items():
        task_def_info = get_task_definition(task_def_arn)
        task_def_arn = task_def_info['taskDefinitionArn']
        # TODO use named_arguments everywhere
        task_defs[task_def_arn] = TaskDefinition(arn=task_def_arn,
                                                             family=task_def_info['family'],
                                                             revision=task_def_info['revision'],
                                                             tasks=child_task_arns)

    container_instances = ecs.describe_container_instances(
        cluster=cluster_arn,
        containerInstances=cont_inst_arn.keys()
    )['containerInstances']
    ec2_id_to_ci_arn = {}
    for container in container_instances:
        ec2_id_to_ci_arn[container['ec2InstanceId']] = container['containerInstanceArn']

    auto_instances = auto_scaling.describe_auto_scaling_instances(
        InstanceIds=ec2_id_to_ci_arn.keys()
    )['AutoScalingInstances']
    for instance in auto_instances:
        ec2_id = instance['InstanceId']
        ci_arn = ec2_id_to_ci_arn[ec2_id]
        instances[ec2_id] = Instance(
            id=ec2_id,
            container_instance_arn=ci_arn,
            auto_scaling_group=instance['AutoScalingGroupName'],
            life_cycle_state=instance['LifecycleState'],
            cluster=cluster_arn,
            tasks=cont_inst_arn[ci_arn])  # Needs list of task arns
    for inst_id in instances.keys():
        for task_arn in instances[inst_id].tasks:
            tasks[task_arn].instance = inst_id

    return task_defs, tasks, containers, instances


@functools.lru_cache(maxsize=None)
def get_task_definition(arn):
    return ecs.describe_task_definition(
        taskDefinition=arn
    )['taskDefinition']