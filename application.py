import os
import boto3
from werkzeug.utils import secure_filename
from botocore.exceptions import ClientError
from flask_cors import CORS
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS

application = Flask(__name__)
CORS(application)

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'zip'}
application.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
S3_BUCKET = os.environ.get('S3_BUCKET', 'my-file-uploader-bucket-12')
S3_REGION = os.environ.get('S3_REGION', 'ap-south-1')

s3_client = boto3.client(
    's3',
    region_name=S3_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@application.route('/')
def index():
    return render_template('index.html')

@application.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400

        filename = secure_filename(file.filename)
        s3_client.upload_fileobj(
            file,
            S3_BUCKET,
            filename,
            ExtraArgs={
                'ContentType': file.content_type or 'application/octet-stream'
            }
        )
        file_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{filename}"
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully!',
            'url': file_url,
            'filename': filename
        }), 200

    except ClientError as e:
        error_code = e.response['Error']['Code']
        return jsonify({'error': f'AWS S3 Error: {error_code}'}), 500
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@application.route('/health')
def health():
    return jsonify({'status': 'healthy', 'service': 'file-uploader'}), 200



