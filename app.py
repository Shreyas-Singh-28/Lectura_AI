from flask import Flask, render_template, request, jsonify
import os
import logging
from werkzeug.utils import secure_filename
from study_recommender import process_text  # Import from separate file

app = Flask(__name__, template_folder='.', static_folder='.', static_url_path='')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB limit
app.logger.setLevel(logging.INFO)

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'txt'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only .txt files allowed'}), 400

    try:
        filename = secure_filename(file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)

        with open(temp_path, 'r', encoding='utf-8') as f:
            text = f.read()

        results = process_text(text)

        os.remove(temp_path)
        
        return jsonify(results)

    except Exception as e:
        app.logger.error(f"Error processing file: {str(e)}")
        return jsonify({'error': 'File processing failed'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)  # HTTP only
