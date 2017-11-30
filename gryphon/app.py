import sys
import os
import logging

from flask import Flask, render_template, session, request, redirect, flash
from flask.helpers import url_for
from markupsafe import Markup

from aws_classes import (Cluster, get_authorization, list_clusters,
                         get_task_def_list, region, get_exec_info, ecs, parse_task_def_arn, parse_cluster_arn,
                         describe_all_services)

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
def cluster_view(cluster_name):
    authorization_data = get_authorization()
    cluster = Cluster(name=cluster_name)
    return render_template('cluster.html',
                           cluster=cluster,
                           auth_data=authorization_data,
                           region=region,
                           ssh_signature=session.get('ssh_signature', ''))


@app.route('/task_definitions/')
def task_definitions_view():
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

        return redirect(request.args.get('next', '/'))

    return render_template('ssh_parameters.html',
                           ssh_signature=session.get('ssh_signature', ''),
                           region=region)


@app.route('/cluster/<cluster_name>/stop/<path:task_arn>')
def stop_task(cluster_name, task_arn):
    cluster = Cluster(name=cluster_name)
    cluster.stop_task(task_arn)
    return redirect("/cluster/{}/".format(cluster_name))


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


@app.route("/environment/<task_def_family_name>/<container_name>", methods=["GET", "POST"])
def environment_table(task_def_family_name, container_name):
    task_def = ecs.describe_task_definition(taskDefinition=task_def_family_name)['taskDefinition']
    matching = []
    wrong_revision = []

    for cluster, service in describe_all_services():
        service_name = service['serviceName']

        cluster = parse_cluster_arn(cluster)
        family, revision = parse_task_def_arn(service['taskDefinition'])
        if family != task_def['family']:
            continue

        if int(revision) == task_def['revision']:
            matching.append((cluster, service_name))
        else:
            wrong_revision.append((cluster, service_name, revision))

    for container in task_def['containerDefinitions']:
        if container['name'] == container_name:
            break
    else:
        raise ValueError('Container %s not found' % container_name)

    if request.method == 'POST':
        container['environment'] = []
        for form_key, form_value in request.form.items():
            if form_key.endswith('_name'):
                env_key = request.form[form_key]
                if env_key:
                    env_value = request.form[form_key[:-5] + '_value']
                    container['environment'].append({'name': env_key, 'value': env_value})

        kwargs = {key: task_def[key]
                  for key in 'family networkMode taskRoleArn containerDefinitions'.split()
                  if key in task_def}

        new_task_def = ecs.register_task_definition(**kwargs)['taskDefinition']['taskDefinitionArn']

        def update_service():
            ecs.update_service(cluster=cluster, service=service_name, taskDefinition=new_task_def)

        for cluster, service_name in matching:
            update_service()

        if request.form.get('update_old_services'):
            for cluster, service_name, _ in wrong_revision:
                update_service()

        flash('Services updated!')

        # So that the user can verify that the new environment looks right
        return redirect("/environment/%s/%s" % (task_def_family_name, container_name))
    else:
        container['environment'].sort(key=lambda e: e['name'])
        return render_template(
            'environment.html',
            matching_string=Markup(', '.join('<a href="/cluster/{0}/">{0}</a>:{1}'.format(*m)
                                             for m in matching)),
            **locals())


if __name__ == '__main__':
    app.run(debug=True, port=8000)
