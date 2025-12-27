#!/usr/bin/env python3
"""
Flask web application for generating PDFs from images with priority-based sorting.
"""

import os
import tempfile
import zipfile
from pathlib import Path
from flask import Flask, render_template, request, send_file, flash, jsonify
from werkzeug.utils import secure_filename
import shutil

# Import functions from the original script
from image_to_pdf_core import (
    split_by_semicolon,
    sort_by_priority,
    create_pdf_with_images,
    parse_priority_list
)
from reportlab.lib.pagesizes import letter, A4

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max upload
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    """Check if file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    """Handle PDF generation from uploaded images."""
    try:
        # Check if files were uploaded
        if 'images' not in request.files:
            return jsonify({'error': 'No images uploaded'}), 400
        
        files = request.files.getlist('images')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No images selected'}), 400
        
        # Get form data
        priority_str = request.form.get('priority', '')
        page_size_str = request.form.get('page_size', 'letter')
        
        # Create temporary directory for this request
        temp_dir = tempfile.mkdtemp(prefix='pdf_gen_')
        temp_path = Path(temp_dir)
        
        try:
            # Save uploaded files
            image_paths = []
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = temp_path / filename
                    file.save(str(file_path))
                    image_paths.append(file_path)
            
            if not image_paths:
                return jsonify({'error': 'No valid image files uploaded'}), 400
            
            # Parse priority list
            priority_list = parse_priority_list(priority_str)
            
            # Set page size
            page_size = A4 if page_size_str == 'A4' else letter
            
            # Split into groups
            group1, group2 = split_by_semicolon(image_paths)
            
            # Sort each group
            sorted_group1 = sort_by_priority(group1, priority_list)
            sorted_group2 = sort_by_priority(group2, priority_list)
            
            # Combine groups
            final_order = sorted_group1 + sorted_group2
            
            # Generate PDF
            output_pdf = temp_path / 'output.pdf'
            create_pdf_with_images(final_order, output_pdf, page_size)
            
            # Send the PDF file
            return send_file(
                str(output_pdf),
                mimetype='application/pdf',
                as_attachment=True,
                download_name='generated.pdf'
            )
            
        finally:
            # Clean up will happen after send_file completes
            # We can't delete immediately as send_file needs the file
            pass
            
    except Exception as e:
        app.logger.error(f"Error generating PDF: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    """Health check endpoint for Render."""
    return jsonify({'status': 'healthy'}), 200


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
