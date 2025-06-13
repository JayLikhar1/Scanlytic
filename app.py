import os
from flask import Flask, render_template, request, jsonify, send_file, url_for, send_from_directory
from werkzeug.utils import secure_filename
from models.resume_analyzer import ResumeAnalyzer
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
    static_url_path='',
    static_folder='static',
    template_folder='templates'
)

# Environment variables configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', os.urandom(24))
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB max file size
app.config['FLASK_ENV'] = os.environ.get('FLASK_ENV', 'production')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for development

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize resume analyzer
try:
    logger.info("Initializing ResumeAnalyzer...")
    analyzer = ResumeAnalyzer()
    logger.info("ResumeAnalyzer initialized successfully!")
except Exception as e:
    logger.error(f"Failed to initialize ResumeAnalyzer: {str(e)}")
    raise

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    logger.info("Serving index page")
    return render_template('index.html')

@app.route('/static/<path:filename>')
def serve_static(filename):
    logger.info(f"Serving static file: {filename}")
    return send_from_directory(app.static_folder, filename)

@app.route('/analyze', methods=['POST'])
def analyze_resume():
    logger.info("Received resume analysis request")
    if 'resume' not in request.files:
        logger.error("No file uploaded")
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['resume']
    if file.filename == '':
        logger.error("No file selected")
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logger.info(f"Saving file: {filename}")
        file.save(filepath)
        
        try:
            logger.info("Starting resume analysis")
            analysis_results = analyzer.analyze_resume(filepath)
            logger.info("Resume analysis completed successfully")
            
            # Ensure all required fields are present
            required_fields = {
                'ats_score': 0,
                'score_breakdown': {
                    'keyword_match': 0,
                    'section_presence': 0,
                    'experience_relevance': 0,
                    'formatting': 0,
                    'grammar': 0,
                    'contact_info': 0,
                    'filename': 0,
                    'customization': 0
                },
                'analysis': {
                    'overall_assessment': '',
                    'strengths': [],
                    'improvements': []
                },
                'job_recommendations': [],
                'skills_analysis': {
                    'technical': [],
                    'soft': [],
                    'missing': []
                }
            }
            
            # Merge analysis results with default values
            for key, default_value in required_fields.items():
                if key not in analysis_results:
                    analysis_results[key] = default_value
                elif isinstance(default_value, dict):
                    for subkey, subdefault in default_value.items():
                        if subkey not in analysis_results[key]:
                            analysis_results[key][subkey] = subdefault
            
            # Clean up uploaded file
            os.remove(filepath)
            logger.info("Analysis results returned successfully")
            return jsonify(analysis_results)
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            # Clean up file in case of error
            if os.path.exists(filepath):
                os.remove(filepath)
            return jsonify({'error': str(e)}), 500
    
    logger.error("Invalid file type")
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/download-report', methods=['GET'])
def download_report():
    logger.info("Received download report request")
    try:
        # Get the latest analysis results from the session or request
        data = request.args.get('data')
        if not data:
            logger.error("No analysis data available")
            return jsonify({'error': 'No analysis data available'}), 400
            
        data = json.loads(data)
        logger.info("Generating feedback PDF")
        feedback_pdf = analyzer.generate_feedback_pdf(data)
        
        logger.info("Sending feedback PDF")
        return send_file(
            feedback_pdf,
            as_attachment=True,
            download_name=f'resume_analysis_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = app.config['FLASK_ENV'] == 'development'
    logger.info(f"Starting server on port {port} (debug={debug})")
    app.run(host='0.0.0.0', port=port, debug=debug) 