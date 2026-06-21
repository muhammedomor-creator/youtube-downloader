from flask import Flask, render_template, request, jsonify, send_file
import requests
import io
import re

# আপনার অফিশিয়াল ইউটিউব এপিআই কি
YOUTUBE_API_KEY = "AIzaSyBwieraquhUI5OSIuj5jld-G-IPK-bLx9c"

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def get_video_id(url):
    regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
    match = re.search(regex, url)
    return match.group(1) if match else None

@app.route('/fetch-info', methods=['POST'])
def fetch_info():
    data = request.json
    video_url = data.get('url')
    
    if not video_url:
        return jsonify({'error': 'দয়া করে একটি সঠিক লিংক দিন।'}), 400

    video_id = get_video_id(video_url)
    if not video_id:
        return jsonify({'error': 'ইউটিউব লিংকটি সঠিক নয়।'}), 400

    try:
        # ১. ইউটিউব API দিয়ে টাইটেল ও থাম্বনেইল আনা
        api_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={YOUTUBE_API_KEY}"
        api_res = requests.get(api_url).json()
        
        if not api_res.get('items'):
            return jsonify({'error': 'ভিডিওর তথ্য পাওয়া যায়নি।'}), 404
            
        item = api_res['items'][0]
        title = item['snippet']['title']
        
        thumbnails = item['snippet']['thumbnails']
        thumbnail = (thumbnails.get('maxres') or thumbnails.get('high') or thumbnails.get('default'))['url']
        
        # ২. ডাইরেক্ট ও ফাস্ট ডাউনলোডের জন্য নতুন API কনফিগারেশন
        formats = [
            {
                'resolution': '720p (HD Video)',
                'ext': 'MP4',
                'download_url': f"https://api.vexdl.com/v1/youtube/download?url={video_url}&quality=720p"
            },
            {
                'resolution': '1080p (Full HD)',
                'ext': 'MP4',
                'download_url': f"https://api.vexdl.com/v1/youtube/download?url={video_url}&quality=1080p"
            },
            {
                'resolution': 'Audio Only (MP3)',
                'ext': 'MP3',
                'download_url': f"https://api.vexdl.com/v1/youtube/download?url={video_url}&quality=mp3"
            }
        ]

        return jsonify({
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats
        })

    except Exception as e:
        return jsonify({'error': f'সার্ভার ত্রুটি: {str(e)}'}), 500

@app.route('/download-thumbnail', methods=['GET'])
def download_thumbnail():
    img_url = request.args.get('url')
    if not img_url:
        return "Missing URL", 400
    try:
        response = requests.get(img_url)
        return send_file(
            io.BytesIO(response.content),
            mimetype='image/jpeg',
            as_attachment=True,
            download_name='thumbnail.jpg'
        )
    except Exception as e:
        return str(e), 500

app = app
