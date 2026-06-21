from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp
import requests
import io

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# ১. ভিডিওর তথ্য এবং উপলব্ধ ফরম্যাট খোঁজার রুট
@app.route('/fetch-info', methods=['POST'])
def fetch_info():
    data = request.json
    video_url = data.get('url')
    
    if not video_url:
        return jsonify({'error': 'দয়া করে একটি সঠিক লিংক দিন।'}), 400

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            title = info.get('title', 'Unknown Title')
            thumbnail = info.get('thumbnail', '')
            duration = info.get('duration_string', '00:00')
            
            formats = []
            for f in info.get('formats', []):
                if f.get('url') and (f.get('vcodec') != 'none' or f.get('acodec') != 'none'):
                    ext = f.get('ext', 'mp4')
                    filesize = f.get('filesize') or f.get('filesize_approx', 0)
                    filesize_mb = round(filesize / (1024 * 1024), 2) if filesize else "Unknown"
                    
                    if f.get('height'):
                        resolution = f"{f.get('height')}p (Video)"
                    else:
                        resolution = "Audio Only (MP3/M4A)"
                        
                    formats.append({
                        'format_id': f.get('format_id'),
                        'resolution': resolution,
                        'ext': ext,
                        'size': f"{filesize_mb} MB" if filesize_mb != "Unknown" else "N/A",
                        'download_url': f.get('url')
                    })

            seen_resolutions = set()
            unique_formats = []
            for f in formats:
                if f['resolution'] not in seen_resolutions:
                    seen_resolutions.add(f['resolution'])
                    unique_formats.append(f)

            return jsonify({
                'title': title,
                'thumbnail': thumbnail,
                'duration': duration,
                'formats': unique_formats
            })

    except Exception as e:
        return jsonify({'error': f'তথ্য আনতে ব্যর্থ হয়েছে: {str(e)}'}), 500

# ২. থাম্বনেইল সরাসরি ডাউনলোড করার জন্য প্রক্সি রুট
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
# Vercel সার্ভারলেস ফাংশনের জন্য এটি প্রয়োজন
app = app

if __name__ == '__main__':
    app.run(debug=True)
