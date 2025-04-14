from flask import Flask, render_template, request, jsonify
from study_recommender import process_text
import os
import logging

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.logger.setLevel(logging.DEBUG)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'txt'}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    app.logger.info("Upload request received")
    
    if 'file' not in request.files:
        app.logger.error("No file part in request")
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        app.logger.error("Empty filename received")
        return jsonify({'error': 'No selected file'}), 400
    
    if not (file and allowed_file(file.filename)):
        app.logger.error(f"Invalid file type: {file.filename}")
        return jsonify({'error': 'Only .txt files allowed'}), 400

    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        text = file.read().decode('utf-8')
        app.logger.info(f"Processing file: {file.filename} ({len(text)} characters)")
        
        results = process_text(text)
        app.logger.info(f"Recommendations generated: "
                f"YouTube({len(results['youtube'])}), "
                f"Wikipedia({len(results['wikipedia'])}), "
                f"Khan Academy({len(results['khan'])})")
        
        return jsonify(results)
    except Exception as e:
        app.logger.error(f"Processing error: {str(e)}", exc_info=True)
        return jsonify({'error': 'File processing failed'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)