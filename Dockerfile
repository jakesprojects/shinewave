FROM python:3.7

RUN apt-get update
RUN apt-get -y install build-essential
RUN apt-get -y install cmake
RUN apt-get -y install qtbase5-dev
RUN apt-get -y install qtdeclarative5-dev

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY NodeGraphQt-master /srv/NodeGraphQt
COPY jakenode-master /srv/jakenode
RUN pip3 install /srv/NodeGraphQt
RUN pip3 install /srv/jakenode

RUN apt-get -y install x11-apps
ENV DISPLAY localhost:0

WORKDIR "/srv"
CMD ["jupyter", "notebook", "--port=8888", "--no-browser", "--ip=0.0.0.0", "--allow-root"]