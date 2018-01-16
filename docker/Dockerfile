# mirrord's Dockerfile

FROM debian
MAINTAINER ideal <idealities@gmail.com>

RUN apt-get update
RUN apt-get install -y rsync python-pip

RUN pip install mirror

RUN mkdir /var/log/mirrord /var/log/rsync

CMD ["mirrord"]
