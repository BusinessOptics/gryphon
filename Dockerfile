FROM ubuntu:14.04
MAINTAINER Alex Hall, <alex.mojaki@gmail.com>

ENV apti "apt-get install -y "
RUN apt-get update
RUN $apti software-properties-common
RUN add-apt-repository ppa:fkrull/deadsnakes
RUN apt-get update
RUN $apti python3.5
RUN $apti python3.5-dev
RUN $apti curl
RUN $apti vim
RUN $apti nginx
RUN curl "https://bootstrap.pypa.io/get-pip.py" -o "get-pip.py" && python3.5 get-pip.py
COPY ./requirements.txt /web-server/requirements.txt
RUN pip install -r /web-server/requirements.txt
COPY ./ /web-server/
COPY ./nginx.conf /etc/nginx/
EXPOSE 3000
CMD ["bash","/web-server/devops/entrypoint.sh"]
