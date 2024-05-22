import os
import requests
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from pytube import YouTube

# Get the Telegram bot token from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def start(update, context):
    update.message.reply_text('Send me a YouTube link and I will download the video and send you a link.')

def download_youtube_video(url, output_path):
    yt = YouTube(url)
    stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
    stream.download(output_path=output_path)
    return stream.default_filename

def upload_to_fileio(file_path):
    with open(file_path, 'rb') as file:
        response = requests.post('https://file.io/', files={'file': file})
        if response.status_code == 200:
            return response.json().get('link')
        else:
            return None

def handle_message(update, context):
    url = update.message.text
    chat_id = update.message.chat_id

    if 'youtube.com' in url or 'youtu.be' in url:
        update.message.reply_text('Downloading video...')
        video_file = download_youtube_video(url, './')
        update.message.reply_text('Uploading to file.io...')
        fileio_link = upload_to_fileio(video_file)
        if fileio_link:
            update.message.reply_text(f'Here is your video: {fileio_link}')
        else:
            update.message.reply_text('Failed to upload the video.')
        os.remove(video_file)
    else:
        update.message.reply_text('Please send a valid YouTube link.')

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("No TELEGRAM_BOT_TOKEN found. Set the TELEGRAM_BOT_TOKEN environment variable.")
    
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
