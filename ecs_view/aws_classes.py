class Cluster:

    def __init__(self, name, tasks, instances):
        self.name = name
        self.tasks = tasks
        self.instances = instances

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_tasks(self):
        return self.tasks

    def set_tasks(self, tasks):
        self.tasks = tasks

    def get_instances(self):
        return self.instances

    def set_instances(self, instances):
        self.instances = instances


class Task:

    def __init__(self, definition, containers, instances):
        self.definition = definition
        self.containers = containers
        self.instances = instances

    def get_definition(self):
        return self.definition

    def set_definition(self, definition):
        self.definition = definition

    def get_containers(self):
        return self.containers

    def set_containers(self, containers):
        self.containers = containers

    def get_instances(self):
        return self.instances

    def set_instances(self, instances):
        self.instances = instances


class Instance:

    def __init__(self):
        return


class AutoScalingGroup:

    def __init__(self):
        return


class Container:

    def __init__(self, task):
        self.task = task

    def get_task(self):
        return self.task

    def set_task(self, task):
        self.task = task


class TaskDefinition:

    def __init__(self, tasks):
        self.tasks = tasks

    def get_task(self):
        return self.tasks

    def set_task(self, tasks):
        self.tasks = tasks
