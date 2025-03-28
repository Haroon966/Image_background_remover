from flask import Flask, request, render_template, send_file, jsonify
from rembg import remove
from PIL import Image
import os
import uuid
from werkzeug.utils import secure_filename
from io import BytesIO

# Initialize Flask app
app = Flask(__name__)

# Configure upload and output folders
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'static/output'

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = None  # Remove size restriction

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/uploads/<filename>')
def serve_upload(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/remove-background', methods=['POST'])
def remove_background():
    """Process image to remove background"""
    # Check if image was uploaded
    if 'image' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['image']
    
    # Check if file was selected
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Process the file without saving
    if file:
        try:
            input_image = Image.open(file.stream)
            output_image = remove(input_image)
            
            # Save the processed image to a BytesIO stream
            output_stream = BytesIO()
            output_image.save(output_stream, format="PNG")
            output_stream.seek(0)
            
            # Return the processed image directly
            return send_file(output_stream, mimetype='image/png', as_attachment=True, download_name='processed_image.png')
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use the PORT environment variable or default to 5000
    app.run(host='0.0.0.0', port=port, debug=True)

    
