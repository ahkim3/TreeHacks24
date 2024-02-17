FROM ghcr.io/merklebot/hackathon-arm-image:master as build

RUN apt-get update && apt-get install -y ffmpeg alsa-utils

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ARG TARGETPLATFORM
ARG BUILDPLATFORM
ARG TARGETOS
ARG TARGETARCH

ARG Version
ARG GitCommit
RUN echo "I am running on $BUILDPLATFORM, building for $TARGETPLATFORM"

COPY requirements.txt requirements.txt
RUN python3.8 -m pip install --upgrade pip
RUN python3.8 -m pip install -r requirements.txt
COPY . .

CMD ["python3.8", "server.py"]