class Cluster:
    def __init__(self, arn, name, tasks, instances):
        self.arn = arn
        self.name = name
        self.tasks = tasks
        self.instances = instances


class Task:
    def __init__(self, arn, definition, containers, cluster, instance):
        self.arn = arn
        self.definition = definition
        self.containers = containers
        self.cluster = cluster
        self.instance = instance


class Instance:
    def __init__(self, inst_id, container_instance_arn, auto_scaling_group, life_cycle_state, cluster, tasks):
        self.id = inst_id
        self.container_instance_arn = container_instance_arn
        self.auto_scaling_group = auto_scaling_group
        self.life_cycle_state = life_cycle_state
        self.cluster = cluster
        self.tasks = tasks


class Container:
    def __init__(self, arn, name, task):
        self.arn = arn
        self.name = name
        self.task = task


class TaskDefinition:
    def __init__(self, arn, family, tasks):
        self.arn = arn
        self.family = family
        self.tasks = tasks
