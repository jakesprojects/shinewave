FROM python:3.8

RUN mkdir -p /run/user/1000/xpra
RUN mkdir /run/xpra
RUN chmod 777 /run/* -R
RUN chmod 777 /tmp/* -R
RUN apt-get update
RUN apt-get -y install build-essential
RUN apt-get -y install cmake
RUN apt-get -y install qtbase5-dev
RUN apt-get -y install qtdeclarative5-dev
RUN apt-get -y install libnss3
RUN apt-get -y install libasound2
RUN apt-get -y install libpulse0
RUN apt-get -y install libpulse-dev
RUN apt-get -y install libudev-dev
RUN apt-get -y install net-tools
RUN apt-get -y install psmisc

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN apt-get -y install x11-apps
ENV DISPLAY :80

RUN wget -q https://xpra.org/gpg.asc -O- | apt-key add -
RUN apt update
RUN apt -y install xpra
RUN git clone https://github.com/Xpra-org/xpra-html5
RUN xpra-html5/setup.py install
RUN apt-get install --reinstall -y xdg-utils

COPY NodeGraphQt-master /srv/NodeGraphQt
COPY jakenode-master /srv/jakenode
COPY shinewave_webapp /srv/shinewave_webapp
RUN pip3 install /srv/NodeGraphQt
RUN pip3 install /srv/jakenode
RUN pip3 install /srv/shinewave_webapp

WORKDIR "/srv"

CMD ["jupyter", "notebook", "--port=8888", "--no-browser", "--ip=0.0.0.0", "--allow-root"]