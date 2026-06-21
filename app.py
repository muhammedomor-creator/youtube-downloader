from flask import Flask, render_template, request, jsonify, send_file
import requests
import io
import re

# আপনার দেওয়া অফিশিয়াল ইউটিউব এপিআই কি
YOUTUBE_API_KEY = "AIzaSyBwieraquhUI5OSIuj5jld-G-IPK-bLx9c"

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# লিংক থেকে ভিডিও আইডি আলাদা করার লজিক
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
        # ১. ওফিসিয়াল ইউটিউব API দিয়ে ডেটা আনা
        api_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_id}&key={YOUTUBE_API_KEY}"
        api_res = requests.get(api_url).json()
        
        if not api_res.get('items'):
            return jsonify({'error': 'ভিডিওর তথ্য পাওয়া যায়নি। লিংকটি আবার চেক করুন।'}), 404
            
        item = api_res['items'][0]
        title = item['snippet']['title']
        
        thumbnails = item['snippet']['thumbnails']
        thumbnail = (thumbnails.get('maxres') or thumbnails.get('high') or thumbnails.get('default'))['url']
        
        # ২. ব্যাকএন্ড সার্ভার থেকে ডাউনলোডের লিংক জেনারেট করা (CORS সমস্যা এড়াতে)
        formats = []
        
        # একটি বিশ্বস্ত এবং ফ্রি ওপেন-সোর্স ডাউনলোডার গেটওয়ে ব্যবহার করা হচ্ছে
        # এটি ব্যাকএন্ড টু ব্যাকএন্ড কাজ করে তাই ব্রাউজারে ব্লক হবে না
        try:
            download_engine_url = f"https://api.multidl.workers.dev/?url={video_url}"
            engine_res = requests.get(download_engine_url).json()
            
            if engine_res.get('status') == 'success' or engine_res.get('links'):
                links = engine_res.get('links', {})
                
                # 720p চেক করা
                if links.get('720p'):
                    formats.append({'resolution': '720p (HD Video)', 'ext': 'MP4', 'download_url': links['720p']})
                # 1080p চেক করা
                if links.get('1080p'):
                    formats.append({'resolution': '1080p (Full HD)', 'ext': 'MP4', 'download_url': links['1080p']})
                # MP3/Audio চেক করা
                if links.get('mp3') or links.get('audio'):
                    formats.append({'resolution': 'Audio Only (MP3)', 'ext': 'MP3', 'download_url': links.get('mp3') or links.get('audio')})
        except:
            pass

        # যদি কোনো কারণে ডাইনামিক ইঞ্জিন ফেইল করে, তবে ব্যাকআপ হিসেবে স্টেবল গেটওয়ে লিংক দেওয়া
        if not formats:
            formats = [
                {
                    'resolution': '720p (HD Video)',
                    'ext': 'MP4',
                    'download_url': f"https://loader.to/api/button/?url={video_url}&f=720"
                },
                {
                    'resolution': 'Audio Only (MP3)',
                    'ext': 'MP3',
                    'download_url': f"https://loader.to/api/button/?url={video_url}&f=mp3"
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
