FROM docker.io/library/python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY ns-proxy.py .

CMD [ "python3", "-u", "ns-proxy.py" ]
