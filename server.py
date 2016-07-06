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

boto3.setup_default_session(region_name='us-east-1')
ecs = boto3.client('ecs')
ec2 = boto3.resource('ec2')

def jp(j):
    print(json.dumps(j, indent=2, default=lambda x: str(x) if isinstance(x, datetime) else json.dumps(x)))

@functools.lru_cache(maxsize=None)
def get_task_definition(arn):
    return ecs.describe_task_definition(
        taskDefinition=arn
    )['taskDefinition']

def get_cluster_overview(cluster_name):
    instances = defaultdict(lambda: {'tasks':[]})

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
        containers = [{ 'arn': t['containerArn'] } for t in task['containers']]
        instances[ci]['tasks'].append(task)
        instances[ci]['arn'] = ci

        task['taskDefinition'] = get_task_definition(task['taskDefinitionArn'])
        family = task['taskDefinition']['family']
        families[family].append(task)

    instances = list(instances.values())

    cis = { ci["containerInstanceArn"]: ci for ci in  ecs.describe_container_instances(
            cluster=cluster_name,
            containerInstances=[i['arn'] for i in instances]
            )['containerInstances']
          }

    for instance in instances:
        ci = cis[instance['arn']]
        instance['ec2InstanceId'] = ci['ec2InstanceId']
        instance['containerInstance'] = ci

    ec2InstanceIds = [ ci['ec2InstanceId'] for ci in cis.values() ]
    ec2Instances = { ec2Instance.instance_id:ec2Instance
                        for ec2Instance in ec2.instances.filter(InstanceIds=ec2InstanceIds)
                   }

    for instance in instances:
        ec2Instance = ec2Instances[instance['ec2InstanceId']]
        assert instance['ec2InstanceId'] == ec2Instance.instance_id
        tags = { tag['Key'] : tag['Value'] for tag in ec2Instance.tags }
        name = tags.get('Name', '')
        instance['name'] = name
        instance['ec2Instance'] = ec2Instance

    instances.sort(key = lambda i: i['name'])

    families = list(families.items())
    families.sort(key=lambda x: x[0])

    return instances, families

app = Flask(__name__, static_url_path='')

@app.route('/cluster/<cluster_name>/', methods=['GET', 'POST'])
def overview(cluster_name):
    instances, families = get_cluster_overview(cluster_name)
    return render_template('overview.html', instances=instances, families=families, cluster_name=cluster_name)

@app.route('/static/<path:path>')
def send_staticfles(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True)

