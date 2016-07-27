Gryphon Cluster Viewer
======================

AWS Elastic Container Service Interface

<img src="/mascot.png?raw=true" width="500">

A simply designed web-based application to allow users to view a clear interface for the AWS console showing information such as tasks running on each instance as well as the commands to ssh into the instance or run the docker container for debugging. It is a very thin layer over the AWS API's to make common tasks easier and give a much better general overview. 

Features include:

* Easily see your cluster state, including all the instances and tasks
* See resource allocation
* See autoscaling terminations
* Shortcuts to different AWS interfaces and other useful quick links.
* Quickly ssh into you instances
* Exec directly into a running container in a task. A single command that ssh's finds the container ID and execs into it.
* Manually run any task definition. Gives the terminal commands to run a container exactly as ECS would to make debugging easier.

# Running Instructions

You can run it directly from dockerhub with:

```
docker run \
  -e AWS_ACCESS_KEY_ID=<AWS_ACCESS_KEY_ID> \
  -e AWS_DEFAULT_REGION=<AWS_DEFAULT_REGION> \
  -e AWS_SECRET_ACCESS_KEY=<AWS_SECRET_ACCESS_KEY> \
  -p 3000:3000 \
  --name=gryphon \
  businessoptics/gryphon
```

Gryphon uses boto to communicate with AWS so if you run it on ECS with a task role it can use that task role's AWS credentials automatically.
