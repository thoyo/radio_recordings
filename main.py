import sys
import os
import datetime
import schedule
import subprocess
import m3u8
from pydub import AudioSegment
import urllib.request
import time
from telegram import Bot
import asyncio
from dotenv import load_dotenv
import logging

logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s",
                    level=logging.INFO,
                    datefmt="%Y-%m-%d %H:%M:%S")
logging.info("Starting program")

m3u8_file = 'data/out.m3u8'

load_dotenv()

START_TIME = os.getenv("START_TIME")
DURATION_MINUTES = float(os.getenv("DURATION_MINUTES"))
bot = Bot(os.getenv("TELEGRAM_TOKEN"))
CHAT_ID = os.getenv("TELEGRAM_CHAT")


def m3u8_to_ts_list():
    playlist = m3u8.load(m3u8_file)

    ts_list = []
    for segment in playlist.segments:
        ts_list.append(segment.uri)

    return ts_list


def concatenate_mp3_files(input_files, output_file):
    output_audio = AudioSegment.empty()

    for file in input_files:
        audio = AudioSegment.from_mp3(file)
        output_audio += audio

    output_audio.export(output_file, format="mp3")


def download_file(url, output_path):
    urllib.request.urlretrieve(url, output_path)


def job():
    start = datetime.datetime.now()
    logging.info(f"Starting job at {start}")

    ts_list = []
    url = os.getenv("M3U8URL")
    while True:
        logging.info("Retrieving m3u8 file")
        download_file(url, m3u8_file)
        logging.info("m3u8 file retrieved")

        ts_sub_list = m3u8_to_ts_list()
        for ts in ts_sub_list:
            if ts not in ts_list:
                ts_list.append(ts)
                logging.info(f"Converting segment {ts} to mp3")
                subprocess.call(['ffmpeg', '-y', '-i', ts, f"data/{ts.split('/')[-1]}.mp3"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logging.info(f"Segment {ts} converted to mp3")
        if (datetime.datetime.now() - start).total_seconds() / 60 > DURATION_MINUTES:
            break
        time.sleep(10)

    logging.info("Concatenating full mp3 file")
    concatenate_mp3_files([f"data/{ts.split('/')[-1]}.mp3" for ts in ts_list], "data/out.mp3")
    logging.info("Full file concatenated")

    logging.info("Sending file to Telegram")
    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(bot.send_audio(CHAT_ID, "data/out.mp3"))]
    loop.run_until_complete(asyncio.wait(tasks))
    logging.info("File sent to Telegram")

    logging.info("Deleting data")
    os.system("rm -v data/*")
    logging.info("Data deleted")


if len(sys.argv) != 2 or sys.argv[1] not in ["manual", "automatic"]:
    logging.error("Usage: `python main.py automatic` for execution at the `START_TIME` in .env, or "
                  "`python main.py manual` to be executed now")

if sys.argv[1] == "manual":
    job()
elif sys.argv[1] == "automatic":
    schedule.every().day.at(START_TIME).do(job)
    while True:
        schedule.run_pending()
        logging.info("Go sleep")
        time.sleep(60)
