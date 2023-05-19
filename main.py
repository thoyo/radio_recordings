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

START_TIME = "06:00"
DURATION_MINUTES = 0.1  # 10
m3u8_file = 'data/rne_r3_main.m3u8'  # Replace with the desired output file path

load_dotenv()

# Replace TOKEN with your own Telegram API token
bot = Bot(os.getenv("TELEGRAM_TOKEN"))

# Replace CHAT_ID with the chat ID of the chat you want to send the image to
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
    ts_list = []
    while True:
        url = 'https://rtvelivestream.akamaized.net/rtvesec/rne/rne_r3_main.m3u8'  # Replace with the URL of the file you want to download

        download_file(url, m3u8_file)
        ts_sub_list = m3u8_to_ts_list()
        for ts in ts_sub_list:
            if ts not in ts_list:
                ts_list.append(ts)
        if (datetime.datetime.now() - start).total_seconds() / 60 > DURATION_MINUTES:
            break
        time.sleep(10)

    for ts in ts_list:
        subprocess.call(['ffmpeg', '-y', '-i', ts, f"data/{ts.split('/')[-1]}.mp3"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    concatenate_mp3_files([f"data/{ts.split('/')[-1]}.mp3" for ts in ts_list], "data/out.mp3")

    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(bot.send_audio(CHAT_ID, "data/out.mp3"))]
    loop.run_until_complete(asyncio.wait(tasks))

    os.system("rm -v data/*")

if sys.argv[1] == "manual":
    job()
else:
    schedule.every().day.at(START_TIME).do(job)
    while True:
        schedule.run_pending()
        time.sleep(60)  # wait one minute
