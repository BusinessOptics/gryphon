"""

Instances (ssh, cadvisor)
Services
ECS Tasks
ECS Containers (exec)

Monitored/Celery Tasks

Current State
"""

from aws_classes import *
from flask import Flask, render_template, send_from_directory

app = Flask(__name__, static_url_path='')


@app.route('/')
def index():
    cluster_list = create_clusters()
    return render_template('index.html', clusters=cluster_list)


@app.route('/cluster/<cluster_name>/', methods=['GET', 'POST'])
def cluster(cluster_name):
    cluster = Cluster(name=cluster_name)
    cluster.setup_cluster()

    return render_template('cluster.html', cluster=cluster)


@app.route('/taskDefinitions/', methods=['GET', 'POST'])
def definitions():
    task_definitions = get_task_def_list()
    return render_template('definitions.html', task_definitions=task_definitions)


@app.route('/static/<path:path>')
def send_staticfles(path):
    return send_from_directory('static', path)


if __name__ == '__main__':
    app.run(debug=True)
