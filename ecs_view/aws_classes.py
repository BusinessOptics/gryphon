class Cluster:

    def __init__(self, name, tasks, instances):
        self.name = name
        self.tasks = tasks
        self.instances = instances


class Task:

    def __init__(self, name, definition, containers, instances):
        self.name = name
        self.definition = definition
        self.containers = containers
        self.instances = instances


class Instance:

    def __init__(self, inst_id, name, auto_scaling_group, cluster, tasks):
        self.id = inst_id
        self.name = name
        self.auto_scaling_group = auto_scaling_group
        self.cluster = cluster
        self.tasks = tasks


class Container:

    def __init__(self, name, task):
        self.name = name
        self.task = task


class TaskDefinition:

    def __init__(self, name, tasks):
        self.name = name
        self.tasks = tasks

