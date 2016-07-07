from aws_classes import Task, TaskDefinition, Instance, Container, Cluster
from collections import defaultdict
import boto3

boto3.setup_default_session(region_name='us-east-1')
ecs = boto3.client('ecs')
ec2 = boto3.resource('ec2')
auto_scaling = boto3.client('autoscaling')
insts = ec2.instances.filter(
    Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

# change to create_clusters
def create_clusters():
    clusters = {}
    cluster_keys = ecs.list_clusters()['clusterArns']
    if not cluster_keys:
        return None
    cluster_info = ecs.describe_clusters(clusters=cluster_keys)['clusters']
    for cluster in cluster_info:
        c_arn = cluster['clusterArn']
        temp_cluster = Cluster(arn=c_arn, name=cluster['clusterName'])
        clusters[c_arn] = temp_cluster
    return clusters

# def get_cluster(cluster_name):
#     cluster_info = ecs.describe_clusters(clusters=[cluster_name])['clusters']
#     cluster = cluster(....)
#     setup_cluster(cluster)
#     return cluster

# TODO move setup_cluster to aws_classes as a member of cluster
def setup_cluster(cluster):
    tasks = {}
    instances = {}
    containers = {}
    task_defs = {}

    task_keys = ecs.list_tasks(cluster=cluster.arn)['taskArns']

    if not task_keys:
        return None

    task_info = ecs.describe_tasks(cluster=cluster.arn, tasks=task_keys)['tasks']
    cont_inst_arn = defaultdict(list)
    task_dict = defaultdict(list)
    for task in task_info:
        task_arn = task['taskArn']
        cont_inst_arn[task['containerInstanceArn']].append(task['taskArn'])
        tasks[task_arn] = Task(arn=task_arn,
                               cluster=cluster)
        task_dict[task['taskDefinitionArn']].append(tasks[task_arn])
        cont = []
        for cont in task['containers']:
            container_arn = cont['containerArn']
            containers[container_arn] = Container(arn=container_arn,
                                                  name=cont['name'],
                                                  task=tasks[task_arn])
            cont.append(containers[container_arn])
        tasks[task_arn].containers = cont

    for task_def_arn, child_task_arns in task_dict.items():
        task_def_info = get_task_definition(task_def_arn)
        task_def_arn = task_def_info['taskDefinitionArn']
        task_defs[task_def_arn] = TaskDefinition(arn=task_def_arn,
                                                 family=task_def_info['family'],
                                                 revision=task_def_info['revision'],
                                                 tasks=child_task_arns)
        for task in task_defs[task_def_arn]:
            task.definition = task_defs[task_def_arn]

    container_instances = ecs.describe_container_instances(cluster=cluster.arn,
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
        task_list = [tasks[task_arn] for task_arn in cont_inst_arn[ci_arn]]
        instances[ec2_id] = Instance(
            inst_id=ec2_id,
            container_instance_arn=ci_arn,
            auto_scaling_group=instance['AutoScalingGroupName'],
            life_cycle_state=instance['LifecycleState'],
            cluster=cluster,
            tasks=task_list)  # Needs list of task arns
    for inst in instances.values():
        for task_arn in inst.tasks:
            tasks[task_arn].instance = inst
    cluster.instances = instances.values()
    cluster.tasks = tasks.values()
    return cluster


# @functools.lru_cache(maxsize=None)
def get_task_definition(arn):
    return ecs.describe_task_definition(
        taskDefinition=arn
    )['taskDefinition']
