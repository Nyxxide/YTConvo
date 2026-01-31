from flask import Flask, request, send_file, jsonify, render_template
import yt_dlp
import os
import re

app = Flask(__name__)

OUTPUT_PATH = os.path.join(app.instance_path, "Holding")

@app.route('/')
def home():
    return render_template('index.html')

def download_youtube_video_as_mp3(videoData):
    processors = os.cpu_count()
    if videoData.get("ext") == "m4a":
        options = {
            'format': 'bestaudio[ext=m4a]',
            'outtmpl': f'{OUTPUT_PATH}/%(title)s.%(ext)s',
        }
    elif videoData.get("ext") == "mp3":
        options = {
            'format': 'bestaudio/best',
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }
            ],
            'outtmpl': f'{OUTPUT_PATH}/%(title)s.%(ext)s',
            'quiet': False,
        }
    elif videoData.get("ext") == "mp4":
        quality = videoData.get("quality")
        options = {
            'format': f'bestvideo[ext=mp4][height<={quality}]+bestaudio[ext=m4a]/best[height<={quality}]',
            'outtmpl': f'{OUTPUT_PATH}/%(title)s.%(ext)s',
        }

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(videoData.get("URL"), download=True)
        filename = ydl.prepare_filename(info)
        download_filename = filename.rsplit('.', 1)[0] + "." + videoData.get("ext")
        print("Download completed!")
        print(download_filename)
        return download_filename


@app.route('/download', methods=['POST'])
def handle_download_request():

    regex = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/)|youtu\.be\/)([\w\-]{11})"

    data = request.get_json()
    url = data.get("URL")
    if url is None or not re.search(regex, url):
        return "Error: Invalid URL provided", 400


    # Ensure the output path exists
    os.makedirs(OUTPUT_PATH, exist_ok=True)

    # Download the video as MP3
    mp3_file = download_youtube_video_as_mp3(data)

    # Send the MP3 file back to the user
    response = send_file(mp3_file, as_attachment=True)
    os.remove(mp3_file)
    return response

@app.route('/formats', methods=['POST'])
def get_format_list():
    
    data =request.get_json()
    if data.get("URL") is not None:
        ydlp = yt_dlp.YoutubeDL()
        video_info = ydlp.extract_info(data.get("URL"), download=False)
        buildJson = video_info['formats']
        resJson = {"ext": [], "quality": []}
        for format in buildJson:
            if format["ext"] == "mp4":
                if 'mp4' not in resJson['ext']:
                    resJson["ext"].append('mp4')
                if format.get("height") not in resJson['quality'] and type(format.get("height")) == int:
                    resJson["quality"].append(format.get("height"))
            if format["ext"] == "m4a":
                if 'm4a' not in resJson['ext']:
                    resJson["ext"].append('m4a')
        resJson["ext"].append('mp3')
        return jsonify(resJson)
    else:
        return jsonify({"VideoTypes": "Enter Video URL"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

