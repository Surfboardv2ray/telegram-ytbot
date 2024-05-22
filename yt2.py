import os
import re
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler
from pytube import YouTube, Playlist

# Get the Telegram bot token from environment variables
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def start(update, context):
    update.message.reply_text('Send me a YouTube link, playlist link, or Shorts link, and I will download the video(s) and send you a link.')

def normalize_youtube_url(url):
    # Check if the URL is a shortened YouTube URL or a Shorts URL
    if 'youtu.be' in url:
        video_id = url.split('/')[-1]
        return f'https://www.youtube.com/watch?v={video_id}'
    elif 'youtube.com/shorts' in url:
        video_id = url.split('/')[-1]
        return f'https://www.youtube.com/watch?v={video_id}'
    return url

def download_youtube_video(url, output_path, quality=None):
    yt = YouTube(url)
    if quality:
        stream = yt.streams.filter(resolution=quality).first()
        if not stream:
            raise ValueError("Cannot find the specified resolution, please try again with a different option.")
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

def get_playlist_video_qualities(playlist_url):
    playlist = Playlist(playlist_url)
    qualities = []
    for video_url in playlist.video_urls:
        yt = YouTube(video_url)
        video_qualities = [stream.resolution for stream in yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()]
        qualities.extend(video_qualities)
    return qualities

def download_youtube_playlist(playlist_url, message, quality=None):
    try:
        playlist_qualities = get_playlist_video_qualities(playlist_url)
        if not playlist_qualities:
            message.reply_text("No videos found in the playlist.")
            return
        
        lowest_quality = min(playlist_qualities)
        highest_quality = max(playlist_qualities)
        
        if quality == 'lowest':
            selected_quality = lowest_quality
        elif quality == 'highest':
            selected_quality = highest_quality
        else:
            message.reply_text("Invalid quality option.")
            return

        playlist = Playlist(playlist_url)
        total_videos = len(playlist.video_urls)
        current_video = 0

        for video_url in playlist.video_urls:
            current_video += 1
            message.reply_text(f'Uploading video {current_video}/{total_videos}...')
            
            video_file = download_youtube_video(video_url, './', quality=selected_quality)
            fileio_link = upload_to_fileio(video_file)
            if fileio_link:
                message.reply_text(f'Uploaded video {current_video}/{total_videos} in {selected_quality}: {fileio_link}')
            else:
                message.reply_text(f'Failed to upload video {current_video}/{total_videos} in {selected_quality}.')
            os.remove(video_file)

    except Exception as e:
        message.reply_text(f'Error: {e}')

def handle_message(update, context):
    url = update.message.text
    chat_id = update.message.chat_id
    normalized_url = normalize_youtube_url(url)
    context.user_data['url'] = normalized_url  # Save the normalized URL in user's context

    if 'youtube.com/watch' in normalized_url:  # Check if it's a regular video link
        yt = YouTube(normalized_url)
        available_qualities = [stream.resolution for stream in yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()]
        keyboard = [[InlineKeyboardButton(q, callback_data=q) for q in available_qualities]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Please select the video quality:', reply_markup=reply_markup)
    elif 'youtube.com/playlist' in normalized_url:  # Check if it's a playlist link
        keyboard = [[InlineKeyboardButton("Lowest Quality", callback_data='lowest'),
                     InlineKeyboardButton("Highest Quality", callback_data='highest')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Please select the quality for all videos in the playlist:', reply_markup=reply_markup)
    elif 'youtube.com/shorts' in normalized_url:  # Check if it's a Shorts link
        yt = YouTube(normalized_url)
        available_qualities = [stream.resolution for stream in yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()]
        keyboard = [[InlineKeyboardButton(q, callback_data=q) for q in available_qualities]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text('Please select the video quality:', reply_markup=reply_markup)
    else:
        update.message.reply_text('Please send a valid YouTube link, playlist link, or Shorts link.')

def button(update, context):
    query = update.callback_query
    quality = query.data

    if quality.isdigit() or quality.endswith('p'):
        quality = quality + 'p' if quality.isdigit() else quality
        try:
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
        except ValueError as e:
            query.answer()
            query.edit_message_text(text=str(e))
    elif quality in ['lowest', 'highest']:  # Adjusted condition to check for 'lowest' or 'highest'
        query.answer()
        query.edit_message_text(text=f"Selected quality: {quality.capitalize()} Quality")
        url = context.user_data['url']
        download_youtube_playlist(url, query.message, quality=quality)  # Pass the quality option to the function
    else:
        query.answer()
        query.edit_message_text(text="Invalid option.")

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
