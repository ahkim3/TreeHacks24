FROM ghcr.io/merklebot/hackathon-arm-image:master as build

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt requirements.txt
RUN python3.8 -m pip install -r requirements.txt
COPY . .

CMD ["python3.8", "server.py"]