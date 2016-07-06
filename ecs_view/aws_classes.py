class Cluster:

    def __init__(self):
        return


class Task:

    def __init__(self):
        return


class Instance:
    def __init__(self, id, name, auto_scaling_group, cluster, tasks):
        self.id = id
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

    def __init__(self):
        return


class TaskDefinition:

    def __init__(self):
        return
