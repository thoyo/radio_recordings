FROM python:3.8

ENV RADIO_RECORDINGS /opt/radio_recordings

RUN mkdir -p $RADIO_RECORDINGS
RUN mkdir -p $RADIO_RECORDINGS/data

COPY requirements.txt $RADIO_RECORDINGS/requirements.txt
COPY main.py $RADIO_RECORDINGS/main.py
COPY .env $RADIO_RECORDINGS/.env

ENV AM_I_IN_A_DOCKER_CONTAINER Yes

RUN apt update
RUN apt-get -y install ffmpeg
RUN pip install -r $RADIO_RECORDINGS/requirements.txt

WORKDIR $RADIO_RECORDINGS
# CMD ["python", "-u", "main.py", "manual"]
CMD ["python", "-u", "main.py", "automatic"]
