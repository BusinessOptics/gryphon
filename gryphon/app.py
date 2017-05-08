import sys
import os
import logging

from flask import Flask, render_template, session, request, redirect
from aws_classes import (Cluster, get_authorization, list_clusters,
                         get_task_def_list, region, get_exec_info)

logFormatter = logging.Formatter(
    "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s"
    )
rootLogger = logging.getLogger()
consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
rootLogger.addHandler(consoleHandler)
rootLogger.setLevel(logging.INFO)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', "VGJAA^S&*ASKASP")

@app.route('/health')
def health():
    return 'ok'


@app.route('/')
def index():
    cluster_list = list_clusters()
    return render_template('index.html', clusters=cluster_list, region=region)


@app.route('/cluster/<cluster_name>/')
def cluster(cluster_name):
    authorization_data = get_authorization()
    cluster = Cluster(name=cluster_name)
    return render_template('cluster.html',
                           cluster=cluster,
                           auth_data=authorization_data,
                           region=region,
                           ssh_signature=session.get('ssh_signature', '')
                          )


@app.route('/task_definitions/')
def task_definitions():
    authorization_data = get_authorization()
    task_definitions = get_task_def_list()
    return render_template('definitions.html',
                           task_definitions=task_definitions,
                           should_exec=False,
                           auth_data=authorization_data,
                           region=region)


@app.route('/ssh_parameters/', methods=['GET', 'POST'])
def ssh_parameters():
    if request.method == "POST":
        if 'save' in request.form:
            session['ssh_signature'] = request.form['signature']

        return redirect(request.args.get('next','/'))

    return render_template('ssh_parameters.html',
                           ssh_signature=session.get('ssh_signature', ''),
                           region=region)


@app.route("/cli/exec/<cluster_name>/<container>")
def cli_exec(cluster_name, container):
    task_arn, ip = get_exec_info(cluster_name, container)
    if not(task_arn and ip):
        return 'echo "Cluster or Container not found (Did you mistype?)"'

    command = 'set -eux;\n' \
              'containerName="' + container + '";\n' + \
              'taskArn=' + task_arn + ';\n' +\
              'dockerCommand="CONTAINER_ID=\\`curl http://localhost:51678/v1/tasks?taskarn=${taskArn} | jq -r \\".Containers[] | select(.Name==\\\\\\"${containerName}\\\\\\").DockerId\\"\\`; sudo docker exec -it -u root \\${CONTAINER_ID} bash";\n' +\
              'ssh ' + ip + ' -t "set -ex; $dockerCommand"'
    return command



if __name__ == '__main__':
    app.run(debug=True, port=8000)
