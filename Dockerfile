FROM python:3.5
COPY ./requirements.txt /web-server/requirements.txt
RUN pip install -r /web-server/requirements.txt
COPY ./ /web-server/
EXPOSE 3000
WORKDIR web-server/
CMD ["bash","/web-server/ecs_view/run.sh"]
