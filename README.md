ECS Cluster Viewer
==================

Requires python 3. Use  `virtualenv --python=python3 venv` to create a venv with python 3. We can do this until we docker it properly.

Scripts:
	build.sh - builds the docker image
	run-dev.sh - run the program in development mode (Flask with debug mode, no gunicorn)
	push.sh - pushes the image to AWS ECR

Environment variables:
	AWS_SECRET_ACCESS_KEY
	AWS_ACCESS_KEY_ID
	DEV_MODE (1 if in dev_mode, otherwise not)
