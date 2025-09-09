import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from dotenv import load_dotenv
import uuid
from werkzeug.utils import secure_filename
import os.path

# Import document processors
from document_processor import process_document
from chatbot import get_answer_from_docs

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'docx', 'xlsx', 'xls', 'pdf', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Create uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    print("Received upload request")
    if 'file' not in request.files:
        print("Error: No file part in request")
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    print(f"File received: {file.filename}")
    
    if file.filename == '':
        print("Error: Empty filename")
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        print(f"Saving file to: {file_path}")
        # Save file
        file.save(file_path)
        print(f"File saved successfully")
        
        # Process document
        try:
            print(f"Starting document processing for {file_path}")
            success = process_document(file_path)
            if success:
                print("Document processed successfully")
                return jsonify({'success': True, 'message': 'Document uploaded and processed successfully', 'filename': filename})
            else:
                print("Document processing failed")
                return jsonify({'error': 'Failed to process document', 'filename': filename}), 500
        except Exception as e:
            print(f"Exception during document processing: {str(e)}")
            return jsonify({'error': f"Error processing document: {str(e)}", 'filename': filename}), 500
    
    print(f"File type not allowed: {file.filename}")
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({'error': 'No message provided'}), 400
    
    user_message = data['message']
    
    try:
        response = get_answer_from_docs(user_message)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
