"""

Instances (ssh, cadvisor)
Services
ECS Tasks
ECS Containers (exec)

Monitored/Celery Tasks

Current State
"""
from collections import defaultdict
from datetime import datetime
import json
import functools

from flask import Flask, request, render_template, send_from_directory
import boto3
import aws_classes

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
            temp_cluster = aws_classes.Cluster(cluster['clusterArn'], cluster['clusterName'], None,
                                               None)
            clusters[cluster['clusterArn']] = temp_cluster
    return clusters
    # for arn in clusters.keys():
    #     if arn in arns:
    #         continue
    #     del clusters[arn]


def cluster_details(cluster_arn):
    tasks = {}
    instances = {}
    containers = {}
    task_defs = {}
    arns = ecs.list_tasks(cluster=cluster_arn)['taskArns']
    task_keys = []
    for arn in arns:
        if tasks.get(arn):
            continue
        task_keys.append(arn)
    if not task_keys:
        return None
    task_info = ecs.describe_tasks(cluster=cluster_arn, tasks=task_keys)['tasks']
    cont_inst_arn = defaultdict(list)
    task_dict = defaultdict(list)
    for task in task_info:
        for cont in task['containers']:
            containers[cont['containerArn']] = aws_classes.Container(cont['containerArn'],
                                                                     cont['name'],
                                                                     task['taskArn'])
        cont_inst_arn[task['containerInstanceArn']].append(task['taskArn'])
        tasks[task['taskArn']] = aws_classes.Task(task['taskArn'], task['taskDefinitionArn'],
                                                  containers.keys(),
                                                  cluster_arn, None)  # Needs instance ID
        task_dict[task['taskDefinitionArn']].append(task['taskArn'])

    for task_definition in task_dict.keys():
        task_def_info = get_task_definition(task_definition)
        task_defs[task_def_info['taskDefinitionArn']] = aws_classes.TaskDefinition(
            task_def_info['taskDefinitionArn'],
            task_def_info['family'],
            task_def_info['revision'],
            task_dict[task_definition])

    container_instances = ecs.describe_container_instances(cluster=cluster_arn,
                                                           containerInstances=cont_inst_arn.keys())[
        'containerInstances']
    instance_ids = {}
    for container in container_instances:
        instance_ids[container['ec2InstanceId']] = container['containerInstanceArn']
    auto_instances = auto_scaling.describe_auto_scaling_instances(InstanceIds=instance_ids.keys())[
        'AutoScalingInstances']
    for instance in auto_instances:
        instances[instance['InstanceId']] = aws_classes.Instance(instance['InstanceId'],
                                                                 instance_ids[
                                                                     instance['InstanceId']],
                                                                 instance['AutoScalingGroupName'],
                                                                 instance['LifecycleState'],
                                                                 cluster_arn,
                                                                 cont_inst_arn[instance_ids[
                                                                     instance['InstanceId']]])
        # Needs list of task arns
    for inst_id in instances.keys():
        for task_arn in instances[inst_id].tasks:
            tasks[task_arn].instance = inst_id
    return task_defs, tasks, containers, instances


def jp(j):
    print(
    json.dumps(j, indent=2, default=lambda x: str(x) if isinstance(x, datetime) else json.dumps(x)))


@functools.lru_cache(maxsize=None)
def get_task_definition(arn):
    return ecs.describe_task_definition(
        taskDefinition=arn
    )['taskDefinition']


def get_cluster_overview(cluster_name):
    instances = defaultdict(lambda: {'tasks': []})

    task_arns = ecs.list_tasks(
        cluster=cluster_name,
        desiredStatus='RUNNING'
    )['taskArns']

    if not task_arns:
        return "YOU GONE GANG BUSTERS"

    tasks = ecs.describe_tasks(cluster=cluster_name, tasks=task_arns)['tasks']

    families = defaultdict(list)

    for task in tasks:
        ci = task['containerInstanceArn']
        # containers = [{'arn': t['containerArn'] } for t in task['containers']]
        instances[ci]['tasks'].append(task)
        instances[ci]['arn'] = ci

        task['taskDefinition'] = get_task_definition(task['taskDefinitionArn'])
        family = task['taskDefinition']['family']
        families[family].append(task)

    instances = list(instances.values())

    cis = {ci["containerInstanceArn"]: ci for ci in ecs.describe_container_instances(
        cluster=cluster_name,
        containerInstances=[i['arn'] for i in instances]
    )['containerInstances']
           }

    for instance in instances:
        ci = cis[instance['arn']]
        instance['ec2InstanceId'] = ci['ec2InstanceId']
        instance['containerInstance'] = ci

    ec2InstanceIds = [ci['ec2InstanceId'] for ci in cis.values()]
    ec2Instances = {ec2Instance.instance_id: ec2Instance
                    for ec2Instance in ec2.instances.filter(InstanceIds=ec2InstanceIds)
                    }

    for instance in instances:
        ec2Instance = ec2Instances[instance['ec2InstanceId']]
        assert instance['ec2InstanceId'] == ec2Instance.instance_id
        tags = {tag['Key']: tag['Value'] for tag in ec2Instance.tags}
        name = tags.get('Name', '')
        instance['name'] = name
        instance['ec2Instance'] = ec2Instance

    instances.sort(key=lambda i: i['name'])

    families = list(families.items())
    families.sort(key=lambda x: x[0])

    return instances, families


app = Flask(__name__, static_url_path='')


@app.route('/cluster/<cluster_name>/', methods=['GET', 'POST'])
def overview(cluster_name):
    instances, families = get_cluster_overview(cluster_name)
    return render_template('overview.html', instances=instances, families=families,
                           cluster_name=cluster_name)


@app.route('/')
def index():
    clusters = create_clusters()
    clust = {cluster: clusters[cluster].name for cluster in clusters}
    return render_template('index.html', clusters=clust)


@app.route('/static/<path:path>')
def send_staticfles(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    clusters = create_clusters()
    cluster_details(clusters.keys()[0])
    app.run(debug=True)
