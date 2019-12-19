FROM jupyter/datascience-notebook:latest

LABEL maintainer="ernestolowy@gmail.com"
LABEL description="Dockerfile used for using jupyter nbs with my FOREX library"

# cloning FOREX repo
WORKDIR work/
RUN git clone https://github.com/elowy01/FOREX.git
ENV PYTHONPATH="$PYTHONPATH:/home/jovyan/work/FOREX/src/"

