from collections import defaultdict
from multiprocessing.pool import ThreadPool
import base64
import functools
import logging
import re

import boto3

ecs = boto3.client('ecs')
ec2 = boto3.resource('ec2')
auto_scaling = boto3.client('autoscaling')
ecr = boto3.client('ecr')

logger = logging.getLogger()

def get_authorization():
    authorization = ecr.get_authorization_token()['authorizationData'][0]
    encoded_token = authorization['authorizationToken']
    token = str(base64.b64decode(encoded_token), "utf-8")
    proxy = authorization['proxyEndpoint']
    index = token.find(':')
    username = token[:index]
    password = token[index+1:]
    return {'username': username, 'password': password, 'endpoint': proxy}


def list_clusters():
    clusters = []
    cluster_keys = ecs.list_clusters()['clusterArns']
    if not cluster_keys:
        return []
    return ecs.describe_clusters(clusters=cluster_keys)['clusters']


@functools.lru_cache(maxsize=None)
def get_task_definition(arn):
    logger.info("Describing task definition {}".format(arn))
    return ecs.describe_task_definition(
        taskDefinition=arn
    )['taskDefinition']


def get_task_def_list():
    lst_all = ecs.list_task_definitions()
    lst_raw = lst_all['taskDefinitionArns']
    lst_token = lst_all.get('nextToken')

    while lst_token is not None:
        lst_info = ecs.list_task_definitions(nextToken=lst_token)
        lst_token = lst_info.get('nextToken')
        lst_raw = lst_raw + lst_info['taskDefinitionArns']

    task_fam_list = defaultdict(list)
    fam_to_rev = defaultdict(list)
    lst = []

    for arn in lst_raw:
        result = re.match(r'arn:.*:task-definition/(.+):(\d+)', arn)
        if result:
            family, revision = result.groups()
        fam_to_rev[family].append((int(revision), arn))

    for key in fam_to_rev.keys():
        temp_list = fam_to_rev[key]
        temp_list.sort(reverse=True)
        top_5 = temp_list[:5]
        final_list = [ arn for num, arn in top_5 ]
        lst = lst+final_list

    t_definitions = map(get_task_definition, lst)
    for definition in t_definitions:
        task_fam = definition['family']
        arn = definition['taskDefinitionArn']
        temp_task_def = TaskDefinition(arn=arn, family=task_fam, revision=definition['revision'])
        cont_defs = []
        for container in definition['containerDefinitions']:
            environments = {env['name']: env['value'] for env in container['environment']}
            temp_cont_def = ContainerDefinition(name=container['name'],
                                                image=container['image'],
                                                task_definition=temp_task_def,
                                                environments=environments)
            cont_defs.append(temp_cont_def)
        temp_task_def.container_defs = cont_defs
        task_fam_list[task_fam].append(temp_task_def)
    task_fams = []
    for fam in task_fam_list.keys():
        task_fams.append(TaskFamily(name=fam,
                                    task_defs=sorted(task_fam_list[fam], key=lambda x: x.revision)))
    return sorted(task_fams, key=lambda x: x.name)


def extract_resource(resources_list, name):
    resource = [r for r in resources_list if r['name'] == name][0]
    value_name = {
        'INTEGER': 'integerValue',
        'DOUBLE': 'doubleValue',
        'LONG': 'longValue'
    }[resource['type']]
    return resource[value_name]


class Cluster:
    def __init__(self, name):
        self.name = name

        tasks = {}
        instances = {}
        containers = {}
        task_defs = {}
        task_families = {}
        container_defs = {}

        logger.info("Starting retrieving tasks list")
        task_info = ecs.list_tasks(cluster=self.name)
        task_keys = task_info['taskArns']
        task_next_token = task_info.get('nextToken')
        if not task_keys:
            return
        while task_next_token is not None:
            logger.info("Continue retrieving tasks list")
            task_info = ecs.list_tasks(cluster=self.name, nextToken=task_next_token)
            task_next_token = task_info.get('nextToken')
            task_keys = task_keys + task_info['taskArns']

        logger.info("Describes tasks")
        task_info = ecs.describe_tasks(cluster=self.name, tasks=task_keys)['tasks']
        cont_inst_arn = defaultdict(list)
        task_dict = defaultdict(list)

        for task in task_info:
            task_arn = task['taskArn']
            cont_inst_arn[task['containerInstanceArn']].append(task['taskArn'])
            tasks[task_arn] = Task(arn=task_arn, cluster=self, last_status=task['lastStatus'])
            task_dict[task['taskDefinitionArn']].append(tasks[task_arn])
            conts = []

            for cont in task['containers']:
                container_arn = cont['containerArn']
                containers[container_arn] = Container(arn=container_arn,
                                                      name=cont['name'],
                                                      task=tasks[task_arn],
                                                      status=cont['lastStatus'])
                conts.append(containers[container_arn])

            tasks[task_arn].containers = conts

        families = defaultdict(list)
        cont_defs_by_task_defs = defaultdict(list)
        t_definitions = map(get_task_definition, task_dict.keys())
        for definition in t_definitions:
            task_def_arn = definition['taskDefinitionArn']
            task_defs[task_def_arn] = TaskDefinition(arn=task_def_arn,
                                                     family=definition['family'],
                                                     revision=definition['revision'],
                                                     tasks=task_dict[task_def_arn])
            families[definition['family']].append(task_defs[task_def_arn])

            for task in task_defs[task_def_arn].tasks:
                task.definition = task_defs[task_def_arn]

            for cont_def in definition['containerDefinitions']:
                container_def_name = cont_def['name']
                environments = {env['name']: env['value'] for env in cont_def['environment']}
                conts = [cont for cont in containers.values() if
                         cont.name == container_def_name]
                temp_container = ContainerDefinition(name=container_def_name,
                                                     image=cont_def['image'],
                                                     task_definition=task_defs[task_def_arn],
                                                     environments=environments,
                                                     containers=conts)
                container_defs[container_def_name] = temp_container
                cont_defs_by_task_defs[task_def_arn].append(temp_container)
                for cont in conts:
                    cont.container_def = temp_container

        for task_def in cont_defs_by_task_defs.keys():
            task_defs[task_def].container_defs = cont_defs_by_task_defs[task_def]

        for name, task_defs in families.items():
            task_families[name] = TaskFamily(name=name, task_defs=task_defs)
            for task_def in task_defs:
                task_def.family = task_families[name]

        logging.info("Describe container instances")
        container_instances = ecs.describe_container_instances(
            cluster=self.name,
            containerInstances=list(cont_inst_arn.keys())
        )['containerInstances']

        ec2_id_to_ci = {container['ec2InstanceId']: container for container in container_instances}

        logging.info("Describe autoscaling instances")
        auto_instances = {auto_inst['InstanceId']: auto_inst for auto_inst in
                          auto_scaling.describe_auto_scaling_instances(
                              InstanceIds=list(ec2_id_to_ci.keys()))['AutoScalingInstances']}

        logging.info("Describe ec2 instances")
        ec2_instances = {inst.instance_id: inst for inst in
                         ec2.instances.filter(InstanceIds=list(ec2_id_to_ci.keys()))}

        for instance in ec2_instances.values():
            ec2_id = instance.instance_id
            container_instance = ec2_id_to_ci[ec2_id]
            autoscaling_instance = auto_instances.get(ec2_id)

            ci_arn = container_instance['containerInstanceArn']
            task_list = [tasks[task_arn] for task_arn in cont_inst_arn[ci_arn]]
            launch_time = instance.launch_time

            instances[ec2_id] = Instance(
                ec2_instance = instance,
                container_instance=container_instance,
                autoscaling_instance=autoscaling_instance,
                cluster=self,
                tasks=sorted(task_list, key=lambda x: x.definition.family.name)
                )

        for inst in instances.values():
            for task in inst.tasks:
                task.instance = inst
        self.instances = sorted(instances.values(), key=lambda x: x.name)
        self.tasks = sorted(tasks.values(), key=lambda x: x.definition.family.name)
        self.task_families = sorted(task_families.values(), key=lambda x: x.name)


class Task:
    def __init__(self, arn=None, definition=None, containers=None,
                 cluster=None, instance=None, last_status=None):
        self.arn = arn
        self.definition = definition
        self.containers = containers
        self.cluster = cluster
        self.instance = instance
        self.last_status = last_status


class Instance:
    def __init__(self,
                 ec2_instance,
                 container_instance,
                 autoscaling_instance,
                 cluster,
                 tasks):

        self.id = ec2_instance.instance_id
        self.container_instance_arn = container_instance['containerInstanceArn']
        self.ip = ec2_instance.private_ip_address
        self.type = ec2_instance.instance_type
        self.cluster = cluster
        self.tasks = tasks
        self.launch_time = ec2_instance.launch_time

        if autoscaling_instance:
            self.auto_scaling_group=autoscaling_instance['AutoScalingGroupName'],
            self.life_cycle_state=autoscaling_instance['LifecycleState'],
        else:
            self.auto_scaling_group = ""
            self.life_cycle_state = ""

        tag_list = ec2_instance.tags or []

        tags = {value['Key']: value['Value'] for value in tag_list}
        self.name = tags.get('Name', '')

        resource_keys = ["CPU", "MEMORY"]
        self.remaining_resources = {
                key: extract_resource(container_instance['remainingResources'], key)
                for key in resource_keys
                }
        self.registered_resources = {
                key: extract_resource(container_instance['registeredResources'], key)
                for key in resource_keys
                }
        self.used_resources = {
                key: self.registered_resources[key] - self.remaining_resources[key]
                for key in resource_keys
                }
        self.percentage_resources_used = {
                key: (self.used_resources[key] / self.registered_resources[key]) * 100
                for key in resource_keys
                }

    def __str__(self):
        return str(self.id) + " " + str(self.name)


class Container:
    def __init__(self, arn=None, name=None, task=None, status=None, container_def=None):
        self.arn = arn
        self.name = name
        self.task = task
        self.status = status
        self.container_def = container_def


class TaskFamily:
    def __init__(self, name=None, task_defs=None):
        self.name = name
        self.task_defs = task_defs


class TaskDefinition:
    def __init__(self, arn=None, family=None, revision=None, tasks=None, container_defs=None):
        self.arn = arn
        self.family = family
        self.revision = revision
        self.tasks = tasks
        self.container_defs = container_defs


class ContainerDefinition:
    def __init__(self, name=None, image=None, task_definition=None, containers=None,
                 environments=None):
        self.name = name
        self.image = image
        self.task_definition = task_definition
        self.containers = containers
        self.environments = environments

