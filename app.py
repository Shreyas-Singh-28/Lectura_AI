from flask import Flask, request, jsonify, send_from_directory, redirect, url_for
import os
import subprocess
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import study_recommender  # Import your recommendation system

load_dotenv()

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'docx', 'mp3', 'mp4', 'wav'}
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_file(filepath):
    try:
        if os.path.exists('./main.exe'):
            result = subprocess.run(
                ['./main.exe', filepath],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        else:
            result = subprocess.run(
                ['python', 'transcribe.py', filepath],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error processing file: {e.stderr}")
        return None

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        output = process_file(filepath)
        if not output:
            return jsonify({'error': 'File processing failed'}), 500
        
        transcription_path = os.path.join(app.config['UPLOAD_FOLDER'], 'transcription.txt')
        with open(transcription_path, 'w', encoding='utf-8') as f:
            f.write(output)
            
        return jsonify({
            'success': True,
            'message': 'File processed successfully',
            'redirect': '/recommendations'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/recommendations')
def recommendations():
    transcription_path = os.path.join(app.config['UPLOAD_FOLDER'], 'transcription.txt')
    
    if not os.path.exists(transcription_path):
        return redirect('/')
    
    with open(transcription_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Call your recommendation system
    recommendations = study_recommender.generate_recommendations(content)
    
    # Convert newlines to HTML line breaks and escape special characters
    formatted_content = content[:500].replace('\n', '<br>') + ('...' if len(content) > 500 else '')
    formatted_recommendations = recommendations.replace('\n', '<br>')
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Recommendations</title>
        <link rel="stylesheet" href="/style.css">
    </head>
    <body>
        <div class="container">
            <h1>Study Recommendations</h1>
            <div class="results-container">
                <div class="transcription-preview">
                    <h3>Processed Content Preview:</h3>
                    <div class="content-box">{formatted_content}</div>
                </div>
                <div class="recommendations">
                    <h3>Recommended Study Materials:</h3>
                    <div class="recommendations-box">{formatted_recommendations}</div>
                </div>
            </div>
            <a href="/" class="back-btn">Process Another File</a>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    if not os.path.exists('main.exe'):
        try:
            subprocess.run(['g++', 'main.cpp', '-o', 'main.exe'], check=True)
        except subprocess.CalledProcessError:
            print("C++ compilation failed, using Python fallback")
    app.run(debug=True)