from collections import defaultdict
import boto3
import functools

boto3.setup_default_session(region_name='us-east-1')
ecs = boto3.client('ecs')
ec2 = boto3.resource('ec2')
auto_scaling = boto3.client('autoscaling')


def create_clusters():
    clusters = []
    cluster_keys = ecs.list_clusters()['clusterArns']
    if not cluster_keys:
        return None
    cluster_info = ecs.describe_clusters(clusters=cluster_keys)['clusters']
    for cluster in cluster_info:
        c_arn = cluster['clusterArn']
        clusters.append(Cluster(arn=c_arn, name=cluster['clusterName']))
    return clusters


@functools.lru_cache(maxsize=None)
def get_task_definition(arn):
    return ecs.describe_task_definition(
        taskDefinition=arn
    )['taskDefinition']


def get_task_def_list():
    lst = ecs.list_task_definitions().get('taskDefinitionArns')
    task_fam_list = defaultdict(list)
    for arn in lst:
        definition = get_task_definition(arn)
        task_fam = definition['family']
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
        task_fams.append(TaskFamily(name=fam, task_defs=task_fam_list[fam]))
    return task_fams


class Cluster:
    def __init__(self, arn=None, name=None, tasks=None, instances=None, task_families=None):
        self.arn = arn
        self.name = name
        self.tasks = tasks
        self.instances = instances
        self.task_families = task_families

    def setup_cluster(self):
        tasks = {}
        instances = {}
        containers = {}
        task_defs = {}
        task_families = {}
        container_defs = {}
        task_keys = ecs.list_tasks(cluster=self.name)['taskArns']

        if not task_keys:
            return None

        task_info = ecs.describe_tasks(cluster=self.name, tasks=task_keys)['tasks']
        cont_inst_arn = defaultdict(list)
        task_dict = defaultdict(list)
        for task in task_info:
            task_arn = task['taskArn']
            cont_inst_arn[task['containerInstanceArn']].append(task['taskArn'])
            tasks[task_arn] = Task(arn=task_arn,
                                   cluster=self)
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
        for task_def_arn, child_task_arns in task_dict.items():
            task_def_info = get_task_definition(task_def_arn)
            task_def_arn = task_def_info['taskDefinitionArn']
            task_defs[task_def_arn] = TaskDefinition(arn=task_def_arn,
                                                     family=task_def_info['family'],
                                                     revision=task_def_info['revision'],
                                                     tasks=child_task_arns)
            families[task_def_info['family']].append(task_defs[task_def_arn])
            for task in task_defs[task_def_arn].tasks:
                task.definition = task_defs[task_def_arn]
            for cont_def in task_def_info['containerDefinitions']:
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

        container_instances = ecs.describe_container_instances(
            cluster=self.name,
            containerInstances=list(cont_inst_arn.keys())
        )['containerInstances']
        ec2_id_to_ci = {}
        for container in container_instances:
            ec2_id_to_ci[container['ec2InstanceId']] = container

        auto_instances = {auto_inst['InstanceId']: auto_inst for auto_inst in
                          auto_scaling.describe_auto_scaling_instances(
                              InstanceIds=list(ec2_id_to_ci.keys()))['AutoScalingInstances']}
        ec2_instances = {inst.instance_id: inst for inst in
                         ec2.instances.filter(InstanceIds=list(ec2_id_to_ci.keys()))}
        for instance in ec2_instances.values():
            ec2_id = instance.instance_id
            ci_arn = ec2_id_to_ci[ec2_id]['containerInstanceArn']
            tags = {value['Key']: value['Value'] for value in instance.tags}
            rem_resources = {}
            for resource in ec2_id_to_ci[ec2_id]['remainingResources']:
                if resource.get('name') == 'CPU' or resource.get('name') == 'MEMORY':
                    if resource.get('type') == 'INTEGER':
                        rem_resources[resource.get('name')] = resource.get('integerValue')
                    elif resource.get('type') == 'DOUBLE':
                        rem_resources[resource.get('name')] = resource.get('doubleValue')
                    elif resource.get('type') == 'LONG':
                        rem_resources[resource.get('name')] = resource.get('longValue')
            reg_resources = {}
            for resource in ec2_id_to_ci[ec2_id]['registeredResources']:
                if resource.get('name') == 'CPU' or resource.get('name') == 'MEMORY':
                    if resource.get('type') == 'INTEGER':
                        reg_resources[resource.get('name')] = resource.get('integerValue')
                    elif resource.get('type') == 'DOUBLE':
                        reg_resources[resource.get('name')] = resource.get('doubleValue')
                    elif resource.get('type') == 'LONG':
                        reg_resources[resource.get('name')] = resource.get('longValue')
            task_list = [tasks[task_arn] for task_arn in cont_inst_arn[ci_arn]]
            launch_time = instance.launch_time
            if auto_instances.get(ec2_id):
                instances[ec2_id] = Instance(
                    inst_id=ec2_id,
                    name=tags.get('Name'),
                    container_instance_arn=ci_arn,
                    auto_scaling_group=auto_instances.get(ec2_id)['AutoScalingGroupName'],
                    life_cycle_state=auto_instances.get(ec2_id)['LifecycleState'],
                    cluster=self,
                    tasks=sorted(task_list, key=lambda x: x.definition.family.name),
                    ip=instance.private_ip_address,
                    type=instance.instance_type,
                    cpu=reg_resources.get('CPU'),
                    cpu_rem=rem_resources.get('CPU'),
                    mem=reg_resources.get('MEMORY'),
                    mem_rem=rem_resources.get('MEMORY'),
                    launch_time=launch_time)
            else:
                instances[ec2_id] = Instance(
                    inst_id=ec2_id,
                    name=tags.get('Name'),
                    container_instance_arn=ci_arn,
                    cluster=self,
                    tasks=sorted(task_list, key=lambda x: x.definition.family.name),
                    ip=instance.private_ip_address,
                    type=instance.instance_type,
                    cpu=reg_resources.get('CPU'),
                    cpu_rem=rem_resources.get('CPU'),
                    mem=reg_resources.get('MEMORY'),
                    mem_rem=rem_resources.get('MEMORY'),
                    launch_time=launch_time)  # Needs list of task arns
        for inst in instances.values():
            for task in inst.tasks:
                task.instance = inst
        self.instances = sorted(instances.values(), key=lambda x: x.name)
        self.tasks = sorted(tasks.values(), key=lambda x: x.definition.family.name)
        self.task_families = sorted(task_families.values(), key=lambda x: x.name)
        return self


class Task:
    def __init__(self, arn=None, definition=None, containers=None, cluster=None, instance=None):
        self.arn = arn
        self.definition = definition
        self.containers = containers
        self.cluster = cluster
        self.instance = instance


class Instance:
    def __init__(self, inst_id=None, container_instance_arn=None, name=None,
                 auto_scaling_group=None,
                 ip=None, type=None, life_cycle_state=None, cluster=None, tasks=None, cpu=None,
                 cpu_rem=None, mem=None, mem_rem=None, launch_time=None):
        self.id = inst_id
        self.container_instance_arn = container_instance_arn
        self.name = name
        self.auto_scaling_group = auto_scaling_group
        self.ip = ip
        self.type = type
        self.life_cycle_state = life_cycle_state
        self.cluster = cluster
        self.tasks = tasks
        self.cpu = cpu
        self.cpu_rem = cpu_rem
        self.mem = mem
        self.mem_rem = mem_rem
        self.launch_time = launch_time

    @property
    def cpu_perc(self):
        return (float(self.cpu_used) / float(self.cpu)) * 100

    @property
    def mem_perc(self):
        return (float(self.mem_used) / float(self.mem)) * 100

    @property
    def cpu_used(self):
        return self.cpu - self.cpu_rem

    @property
    def mem_used(self):
        return self.mem - self.mem_rem

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
