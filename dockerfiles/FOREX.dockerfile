FROM jupyter/datascience-notebook:latest

LABEL maintainer="ernestolowy@gmail.com"
LABEL description="Dockerfile used for using jupyter nbs with my FOREX library"

# Install packages
RUN apt-get update \
 && apt-get -y --no-install-recommends install \
    build-essential \
    git \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
 && pip install --upgrade pip && \
    pip install --no-cache-dir pandas

# cloning igsr-analysis
WORKDIR /lib
RUN git clone https://github.com/elowy01/FOREX.git
ENV PYTHONPATH=/lib/FOREX/src/

# getting rid of installed dependencies
RUN apt-get remove --purge -y git
