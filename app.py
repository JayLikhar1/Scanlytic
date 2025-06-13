import os
import logging
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
from models.resume_analyzer import ResumeAnalyzer
import json
from datetime import datetime
import spacy
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize ResumeAnalyzer
try:
    logger.info("Loading spaCy model...")
    nlp = spacy.load('en_core_web_sm')
    logger.info("SpaCy model loaded successfully!")
except OSError:
    logger.warning("SpaCy model not found. Downloading...")
    spacy.cli.download('en_core_web_sm')
    nlp = spacy.load('en_core_web_sm')
    logger.info("SpaCy model downloaded and loaded successfully!")

# Initialize analyzer without passing nlp
analyzer = ResumeAnalyzer()
logger.info("ResumeAnalyzer initialized successfully!")

@app.route('/')
def index():
    """Serve the main page"""
    logger.info("Serving index page")
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files with proper error handling"""
    logger.info(f"Serving static file: {filename}")
    try:
        return send_from_directory(app.static_folder, filename)
    except Exception as e:
        logger.error(f"Error serving static file {filename}: {str(e)}")
        return jsonify({"error": "File not found"}), 404

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    """Handle resume analysis requests"""
    logger.info("Received resume analysis request")
    
    if 'file' not in request.files:
        logger.error("No file uploaded")
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        logger.error("No file selected")
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.endswith(('.pdf', '.docx')):
        logger.error(f"Invalid file type: {file.filename}")
        return jsonify({"error": "Invalid file type. Please upload a PDF or DOCX file"}), 400
    
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            filepath = temp_file.name
            file.save(filepath)
        
        logger.info("Starting resume analysis")
        result = analyzer.analyze_resume(filepath)
        logger.info("Resume analysis completed successfully")
        
        # Clean up the temporary file
        try:
            os.remove(filepath)
            logger.info(f"Cleaned up temporary file: {filepath}")
        except Exception as e:
            logger.warning(f"Failed to clean up file {filepath}: {str(e)}")
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error during resume analysis: {str(e)}")
        # Clean up the temporary file in case of error
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"Cleaned up temporary file after error: {filepath}")
        except Exception as cleanup_error:
            logger.warning(f"Failed to clean up file after error: {str(cleanup_error)}")
        return jsonify({"error": str(e)}), 500

@app.route('/download-report', methods=['POST'])
def download_report():
    """Handle report download requests"""
    logger.info("Received download report request")
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Generate the feedback PDF in a temporary file
        logger.info("Generating feedback PDF")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            pdf_path = temp_file.name
        
        analyzer.generate_feedback_pdf(data, pdf_path)
        
        # Send the file
        response = send_from_directory(
            os.path.dirname(pdf_path),
            os.path.basename(pdf_path),
            as_attachment=True,
            download_name='resume_feedback.pdf'
        )
        
        # Clean up the temporary file after sending
        try:
            os.remove(pdf_path)
            logger.info(f"Cleaned up temporary PDF file: {pdf_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up PDF file: {str(e)}")
        
        return response
    
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({"error": str(e)}), 500

# For local development
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port) 