FROM cypress/base

COPY requirements.txt /tmp/requirements.txt
COPY ci-server-key.json /tmp/ci-server-key.json

RUN apt-get -y update
RUN apt-get install -y python3-pip 
RUN pip3 install --upgrade pip
RUN alias pip=pip3
RUN alias python=python3.7
RUN pip3 install -r /tmp/requirements.txt
RUN pip3 install pytest
