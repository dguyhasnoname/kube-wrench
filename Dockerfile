FROM python:3.8-slim-buster

ENV PYTHONUNBUFFERED=1

COPY requirements.txt /
RUN apt-get update && apt-get install  -y \
        curl \
        tar \
        unzip

# Install python packages
RUN pip3 install --no-cache --upgrade -r requirements.txt

COPY . /app
WORKDIR /app

ENV KUBECONFIG=$KUBECONFIG

ENTRYPOINT ["python3", "kube-wrench.py"]
