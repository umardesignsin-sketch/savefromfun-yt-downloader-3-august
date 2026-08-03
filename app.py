from flask import Flask, render_template, request, jsonify, send_file, redirect
import subprocess
import os
import uuid
import threading
import re
import shutil
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

# ============================================
# CONFIGURATION
# ============================================

CLOUDINARY_CLOUD_NAME = "vcaxtpc"
CLOUDINARY_API_KEY = "585339315215195"
CLOUDINARY_API_SECRET = "fe1KDUaf8zKdcKybcNEtK-7Ph7A"

cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
download_status = {}

# ============================================
# FUNCTIONS
# ============================================

def upload_to_cloudinary(filepath, filename):
    try:
        result = cloudinary.uploader.upload(
            filepath,
            resource_type="video",
            public_id=f"yt_downloads/{uuid.uuid4()}",
            use_filename=True,
            unique_filename=True
        )
        return result.get('secure_url')
    except Exception as e:
        print(f"Cloudinary error: {e}")
        return None

def download_video_web(url, download_id, quality='best', format_type='video'):
    try:
        status = download_status[download_id]
        status['status'] = 'downloading'
        status['progress'] = 0
        
        download_dir = os.path.join(DOWNLOAD_FOLDER, download_id)
        os.makedirs(download_dir, exist_ok=True)
        
        # ==========================================
        # SIMPLEST WORKING COMMANDS - NO FFMPEG
        # ==========================================
        
        if format_type == 'audio':
            # Download best audio as m4a
            command = [
                'yt-dlp',
                '-f', 'bestaudio',
                '--extract-audio',
                '--audio-format', 'm4a',
                '-o', os.path.join(download_dir, '%(title)s.%(ext)s'),
                url
            ]
        else:
            # Download best video + audio in a single file
            # Using the simplest format selector
            command = [
                'yt-dlp',
                '-f', 'best[ext=mp4]',  # This downloads the best MP4 available
                '-o', os.path.join(download_dir, '%(title)s.%(ext)s'),
                url
            ]
        
        print(f"Running: {' '.join(command)}")
        
        # Run the command
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Track progress
        for line in process.stdout:
            print(line)  # Log to Render
            if '[download]' in line and '%' in line:
                try:
                    percent_match = re.search(r'(\d+\.\d+)%', line)
                    if percent_match:
                        progress = float(percent_match.group(1))
                        status['progress'] = progress
                        status['message'] = f'Downloading... {int(progress)}%'
                except:
                    pass
        
        process.wait()
        
        # Check if download succeeded
        if process.returncode != 0:
            status['status'] = 'error'
            status['message'] = f'Download failed (code: {process.returncode})'
            print(f"Error: Process returned {process.returncode}")
            return
        
        # Find downloaded file
        files = os.listdir(download_dir)
        if files:
            filename = files[0]
            filepath = os.path.join(download_dir, filename)
            
            # Try uploading to Cloudinary
            status['status'] = 'uploading'
            status['progress'] = 99
            status['message'] = 'Uploading to CDN...'
            
            cloud_url = upload_to_cloudinary(filepath, filename)
            
            if cloud_url:
                status['status'] = 'completed'
                status['progress'] = 100
                status['filename'] = filename
                status['download_url'] = cloud_url
                status['message'] = 'Ready!'
                try:
                    shutil.rmtree(download_dir)
                except:
                    pass
            else:
                # Fallback: serve directly
                status['status'] = 'completed'
                status['progress'] = 100
                status['filename'] = filename
                status['filepath'] = filepath
                status['download_url'] = None
                status['message'] = 'Ready!'
        else:
            status['status'] = 'error'
            status['message'] = 'No file downloaded'
            print("Error: No files in download directory")
            
    except Exception as e:
        status['status'] = 'error'
        status['message'] = str(e)
        print(f"Exception: {e}")

# ============================================
# ROUTES
# ============================================

@app.route("/debug")
def debug():
    import shutil
    return {
        "yt_dlp": shutil.which("yt-dlp"),
        "ffmpeg": shutil.which("ffmpeg")
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def start_download():
    url = request.form.get('url')
    quality = request.form.get('quality', 'best')
    format_type = request.form.get('format', 'video')
    
    if not url:
        return jsonify({'error': 'URL required'}), 400
    
    if 'youtube.com' not in url and 'youtu.be' not in url:
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    download_id = str(uuid.uuid4())[:8]
    download_status[download_id] = {
        'status': 'starting',
        'progress': 0,
        'message': 'Initializing...'
    }
    
    thread = threading.Thread(
        target=download_video_web,
        args=(url, download_id, quality, format_type)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({'download_id': download_id, 'status': 'started'})

@app.route('/status/<download_id>')
def get_status(download_id):
    if download_id not in download_status:
        return jsonify({'error': 'Not found'}), 404
    
    status = download_status[download_id]
    return jsonify({
        'status': status.get('status'),
        'progress': status.get('progress', 0),
        'message': status.get('message', ''),
        'download_url': status.get('download_url'),
        'filename': status.get('filename')
    })

@app.route('/download/<download_id>/file')
def get_file(download_id):
    if download_id not in download_status:
        return jsonify({'error': 'Download not found'}), 404
    
    status = download_status[download_id]
    if status['status'] != 'completed':
        return jsonify({'error': 'Download not complete'}), 400
    
    if status.get('download_url'):
        return redirect(status['download_url'])
    
    filepath = status.get('filepath')
    filename = status.get('filename')
    
    if not filepath or not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(filepath, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    print("=" * 60)
    print("   🎬 YOUTUBE DOWNLOADER LIVE 🎬")
    print("=" * 60)
    
    if CLOUDINARY_CLOUD_NAME == "your_cloud_name":
        print("\n⚠️  Configure Cloudinary for CDN uploads!")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

    