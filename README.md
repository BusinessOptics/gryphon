ECS Cluster Viewer
==================

<img src="/mascot.png?raw=true" width="500">

#Description

This is a simply designed web-based application to allow users to view a clear interface for the AWS console showing information such as tasks running on each instance as well as the commands to ssh into the instance or run the docker container for bug fixing

#Requirements

Docker: Installation instructions can be found [here](https://docs.docker.com/engine/installation/)

# Running Instructions

1. Run `build.sh` from inside the devops folder. (This may take some time depending on your internet connction)
2. Run `sudo docker run -it -e AWS_ACCESS_KEY_ID=YOUR_KEY_HERE -e AWS_SECRET_ACCESS_KEY=YOUR_KEY_HERE -e DEV_MODE=0 -p 3000:3000 gryphon` to run the docker container. If environment variables are set simply use `$(ENVIRONMENT_VARIABLE_NAME)` inplace of `YOUR_KEY_HERE`.
3. From here you may open a web browser and navigate to localhost:3000 or 127.0.0.1:3000 to view the app.
4. When you are finished give a keyboard intterupt to the terminal by pressing `ctrl-c` to stop the container
5. (OPTIONAL) To remove the exited containers run `sudo docker rm $(sudo docker ps -q -f status=exited)`


List of Scripts:

	build.sh - builds the docker image
	run-dev.sh - run the program in development mode (Flask with debug mode, no gunicorn)
	push.sh - pushes the image to AWS ECR
	entrypoint.sh - script run on container start-up to start the server

# Configuration Requirements

Set the following Environment variables:

	AWS_SECRET_ACCESS_KEY
	AWS_ACCESS_KEY_ID
	DEV_MODE (1 if in dev_mode, 0 otherwise)



