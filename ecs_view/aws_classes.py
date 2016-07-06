class Cluster:
    def __init__(self, arn, name, tasks, instances):
        self.arn = arn
        self.name = name
        self.tasks = tasks
        self.instances = instances


class Task:
    def __init__(self, arn,  name, definition, containers, instances):
        self.arn = arn
        self.name = name
        self.definition = definition
        self.containers = containers
        self.instances = instances


class Instance:

    def __init__(self, inst_id, name, auto_scaling_group, life_cycle_state, cluster, tasks):
        self.id = inst_id
        self.name = name
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
    def __init__(self, arn, name, tasks):
        self.arn = arn
        self.name = name
        self.tasks = tasks
