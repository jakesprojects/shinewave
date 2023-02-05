FROM python:3.7

RUN apt-get update
RUN apt-get -y install build-essential
RUN apt-get -y install cmake
RUN apt-get -y install qtbase5-dev
RUN apt-get -y install qtdeclarative5-dev
RUN apt-get -y install libnss3
RUN apt-get -y install libasound2
RUN apt-get -y install libpulse0
RUN apt-get -y install libpulse-dev

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY NodeGraphQt-master /srv/NodeGraphQt
COPY jakenode-master /srv/jakenode
RUN pip3 install /srv/NodeGraphQt
RUN pip3 install /srv/jakenode

RUN apt-get -y install x11-apps
ENV DISPLAY :80
# ENV DISPLAY localhost:0

RUN apt install -y chromium
RUN wget -q https://xpra.org/gpg.asc -O- | apt-key add -
RUN apt update
RUN apt -y install xpra
RUN git clone https://github.com/Xpra-org/xpra-html5
RUN xpra-html5/setup.py install
RUN apt-get install --reinstall -y xdg-utils

WORKDIR "/srv"
RUN adduser --disabled-password --gecos "" myuser
USER myuser
CMD ["jupyter", "notebook", "--port=8888", "--no-browser", "--ip=0.0.0.0", "--allow-root"]