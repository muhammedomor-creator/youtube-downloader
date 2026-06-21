from flask import Flask, render_template, request, send_file
import requests
import io

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# থাম্বনেইল ডাউনলোডের প্রক্সি রুটটি সচল রাখা হলো
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
