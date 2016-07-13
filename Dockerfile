FROM python:3.5
COPY ./requirements.txt /web-server/requirements.txt
RUN pip install -r /web-server/requirements.txt
COPY ./ /web-server/
EXPOSE 3000
WORKDIR web-server/ecs_view
CMD ["gunicorn","-c","gunicorn_config.py","server:app","-u","root"]
