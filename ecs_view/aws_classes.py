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

    def __init__(self, name, definition, containers, instances):
        self.name = name
        self.definition = definition
        self.containers = containers
        self.instances = instances

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

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
    def __init__(self, inst_id, name, auto_scaling_group, cluster, tasks):
        self.id = inst_id
        self.name = name
        self.auto_scaling_group = auto_scaling_group
        self.cluster = cluster
        self.tasks = tasks

    def get_auto_scaling_group(self):
        return self.auto_scaling_group

    def set_cluster(self, cluster):
        self.cluster = cluster

    def get_cluster(self):
        return self.cluster

    def add_task(self, task):
        if task not in self.tasks:
            self.tasks.append(task)

    def get_tasks(self):
        return self.tasks


class AutoScalingGroup:

    def __init__(self, name, min_val, max_val, instances):
        self.name = name
        self.min = min_val
        self.max = max_val
        self.instances = instances

    def remove_instance(self, inst_id):
        self.instances.remove(inst_id)

    def add_instance(self, inst_id):
        if inst_id not in self.instances:
            self.instances.append(inst_id)

    def get_instances(self):
        return self.instances


class Container:

    def __init__(self, name, task):
        self.name = name
        self.task = task

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_task(self):
        return self.task

    def set_task(self, task):
        self.task = task


class TaskDefinition:

    def __init__(self, name, tasks):
        self.name = name
        self.tasks = tasks

    def get_name(self):
        return self.name

    def set_name(self, name):
        self.name = name

    def get_task(self):
        return self.tasks

    def set_task(self, tasks):
        self.tasks = tasks
