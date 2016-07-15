from flask import Flask, render_template

from aws_classes import *

app = Flask(__name__)

@app.route('/health')
def hello():
    return 'ok'


@app.route("/cli/exec/<cluster>/<container>")
def cli_exec(cluster, container):
    container_name = container
    task_arn, ip = get_exec_info(cluster, container)
    if not(task_arn and ip):
        return 'echo "Cluster or Container not found (Did you mistype?)"'

    command = 'echo set -eux; containerName="' + container_name + '"; ' + 'taskArn=' + task_arn + '; ' +\
              'dockerCommand="CONTAINER_ID=\\`curl http://localhost:51678/v1/tasks?taskarn=${taskArn} | jq -r \\".Containers[] | select(.Name==\\\\\\"${containerName}\\\\\\").DockerId\\"\\`; sudo docker exec -it -u root \\${CONTAINER_ID} bash"; ' +\
              'ssh ' + ip + ' -t -t "set -ex; $dockerCommand"'
    return command


@app.route('/')
def index():
    cluster_list = list_clusters()
    return render_template('index.html', clusters=cluster_list)


@app.route('/cluster/<cluster_name>/', methods=['GET', 'POST'])
def cluster(cluster_name):
    authorization_data = get_authorization()
    cluster = Cluster(name=cluster_name)
    return render_template('cluster.html', cluster=cluster, auth_data=authorization_data)


@app.route('/task_definitions/', methods=['GET', 'POST'])
def task_definitions():
    authorization_data = get_authorization()
    task_definitions = get_task_def_list()
    return render_template('definitions.html', task_definitions=task_definitions, should_exec=False, auth_data=authorization_data)


if __name__ == '__main__':
    app.run(debug=True)
