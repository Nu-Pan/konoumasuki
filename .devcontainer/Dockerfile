
FROM ubuntu:latest

RUN apt-get update \
&&  export DEBIAN_FRONTEND=noninteractive \
&&  apt-get -y install --no-install-recommends python3 pip \
&&  apt-get autoremove -y \
&&  apt-get clean

RUN pip install --no-cache-dir sympy jupyterlab matplotlib

