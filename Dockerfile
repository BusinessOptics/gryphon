FROM ubuntu:18.04
MAINTAINER Alex Hall, <alex.mojaki@gmail.com>

ENV apti "apt-get install -y "
RUN apt-get update
RUN $apti software-properties-common

RUN apt-get update
RUN $apti python3 python3-dev python3-pip
RUN $apti nginx
RUN $apti vim curl

COPY ./requirements.txt /web-server/requirements.txt
RUN pip3 install -r /web-server/requirements.txt
COPY ./ /web-server/
COPY ./nginx.conf /etc/nginx/
EXPOSE 3000
CMD ["bash","/web-server/devops/entrypoint.sh"]
