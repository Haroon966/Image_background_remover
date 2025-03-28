from flask import Flask, request, render_template, send_file, jsonify
from rembg import remove
from PIL import Image
import os
import uuid
import logging
from werkzeug.utils import secure_filename
from io import BytesIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

# Initialize Sentry for error tracking
sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN', ''),
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)

# Initialize Flask app
app = Flask(__name__)

# Security headers with Flask-Talisman
talisman = Talisman(
    app,
    force_https=True,
    strict_transport_security=True,
    content_security_policy={
        'default-src': "'self'",
        'img-src': "'self' data:"
    }
)

# Configure folders
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'static', 'output')

# Create directories
os.makedirs UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# App configuration
app.config.update(
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    OUTPUT_FOLDER=OUTPUT_FOLDER,
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max upload size
    SECRET_KEY=os.environ.get('SECRET_KEY', os.urandom(24))
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per day", "10 per minute"]
)

# Allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
@limiter.limit("50 per day")
def index():
    """Render the main page"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error rendering index: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/remove-background', methods=['POST'])
@limiter.limit("20 per minute")
def remove_background():
    """Process image to remove background"""
    try:
        # Check if image was uploaded
        if 'image' not in request.files:
            logger.warning("No file part in request")
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['image']
        
        # Check if file was selected
        if file.filename == '':
            logger.warning("No file selected")
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file
        if not file or not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Invalid file type. Only PNG, JPG, JPEG allowed'}), 400

        # Process the image
        logger.info(f"Processing image: {file.filename}")
        input_image = Image.open(file.stream)
        
        # Optimize image if too large
        if input_image.size[0] > 2000 or input_image.size[1] > 2000:
            input_image.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
        
        output_image = remove(input_image)
        
        # Save to BytesIO with compression
        output_stream = BytesIO()
        output_image.save(
            output_stream,
            format="PNG",
            optimize=True,
            quality=85
        )
        output_stream.seek(0)
        
        logger.info(f"Successfully processed image: {file.filename}")
        return send_file(
            output_stream,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'processed_{uuid.uuid4().hex}.png'
        )

    except MemoryError:
        logger.error("Memory error during image processing")
        return jsonify({'error': 'Image too large to process'}), 413
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        return jsonify({'error': 'Failed to process image'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(429)
def ratelimit_handler(error):
    return jsonify({'error': 'Rate limit exceeded'}), 429

# Only for local development; Gunicorn handles this in production
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use PORT from env or default to 5000
    app.run(
        host='0.0.0.0',  # Bind to all interfaces
        port=port,
        debug=os.environ.get('FLASK_ENV') == 'development',
        threaded=True
    )
