import os
import re
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from pytube import YouTube, Playlist

# Get the Telegram bot token from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def start(update, context):
    update.message.reply_text('Send me a YouTube link or playlist link, and I will download the video(s) and send you a link.')

def download_youtube_video(url, output_path, quality=None):
    yt = YouTube(url)
    if quality:
        stream = yt.streams.filter(resolution=quality).first()
    else:
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

    if 'youtube.com/watch' in url:  # Check if it's a regular video link
        keyboard = [[InlineKeyboardButton("144p", callback_data='144'),
                     InlineKeyboardButton("240p", callback_data='240'),
                     InlineKeyboardButton("360p", callback_data='360'),
                     InlineKeyboardButton("480p", callback_data='480'),
                     InlineKeyboardButton("720p", callback_data='720'),
                     InlineKeyboardButton("1080p", callback_data='1080')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Please select the video quality:', reply_markup=reply_markup)
    elif 'youtube.com/playlist' in url:  # Check if it's a playlist link
        keyboard = [[InlineKeyboardButton("Lowest Quality", callback_data='lowest'),
                     InlineKeyboardButton("Highest Quality", callback_data='highest')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Please select the quality for all videos in the playlist:', reply_markup=reply_markup)
    else:
        update.message.reply_text('Please send a valid YouTube link or playlist link.')

def download_youtube_playlist(playlist_url, update, quality=None):
    try:
        playlist = Playlist(playlist_url)
        total_videos = len(playlist.video_urls)
        current_video = 0

        for video_url in playlist.video_urls:
            current_video += 1
            update.message.reply_text(f'Uploading video {current_video}/{total_videos}...')

            video_file = download_youtube_video(video_url, './', quality=quality)
            fileio_link = upload_to_fileio(video_file)
            if fileio_link:
                update.message.reply_text(f'Uploaded video {current_video}/{total_videos}: {fileio_link}')
            else:
                update.message.reply_text(f'Failed to upload video {current_video}/{total_videos}.')
            os.remove(video_file)

    except Exception as e:
        update.message.reply_text(f'Error: {e}')

def button(update, context):
    query = update.callback_query
    quality = query.data

    if quality.isdigit():
        quality += 'p'  # Append 'p' to make it resolution (e.g., 720p)
        query.answer()
        query.edit_message_text(text=f"Selected video quality: {quality}")
        url = context.user_data['url']
        video_file = download_youtube_video(url, './', quality=quality)
        fileio_link = upload_to_fileio(video_file)
        if fileio_link:
            query.message.reply_text(f'Here is your video in {quality}: {fileio_link}')
        else:
            query.message.reply_text('Failed to upload the video.')
        os.remove(video_file)
    elif quality == 'lowest':
        query.answer()
        query.edit_message_text(text=f"Selected quality: Lowest Quality")
        url = context.user_data['url']
        download_youtube_playlist(url, query.message, quality='144')
    elif quality == 'highest':
        query.answer()
        query.edit_message_text(text=f"Selected quality: Highest Quality")
        url = context.user_data['url']
        download_youtube_playlist(url, query.message, quality='1080')

def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("No TELEGRAM_BOT_TOKEN found. Set the TELEGRAM_BOT_TOKEN environment variable.")
    
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    dp.add_handler(CallbackQueryHandler(button))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
