Gryphon Cluster Viewer
======================

AWS Elastic Container Service Interface

<img src="/mascot.png?raw=true" width="500">

#Description

A simply designed web-based application to allow users to view a clear interface for the AWS console showing information such as tasks running on each instance as well as the commands to ssh into the instance or run the docker container for debugging.

#Requirements

Docker: Installation instructions can be found [here](https://docs.docker.com/engine/installation/)

# Running Instructions

List of Scripts:

	build.sh - builds the docker image
	run-dev.sh - run the program in development mode (Flask with debug mode, no gunicorn)
	entrypoint.sh - script run on container start-up to start the server

# Configuration Requirements

Set the following Environment variables:

	AWS_SECRET_ACCESS_KEY
	AWS_ACCESS_KEY_ID
	AWS_DEFAULT_REGION
	DEBUG (1 if in debug mode, 0 otherwise)



