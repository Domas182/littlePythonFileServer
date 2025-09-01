import os
from flask import Flask, request, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename

# The folder where uploaded files will be stored
UPLOAD_FOLDER = 'uploads'
# UPLOAD_FOLDER = '<absolute_path_if_you_want'

# Create a Flask application instance
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# Set the upload limit to 80 Gigabytes
app.config['MAX_CONTENT_LENGTH'] = 80 * 1024 * 1024 * 1024 # 80 GB upload limit

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    """
    Main page: Displays an upload form with a progress bar and a list of files.
    """
    files = os.listdir(app.config['UPLOAD_FOLDER'])

    # HTML and JavaScript for the page
    html = f"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Il nostro piccolo file server</title>
      <style>
        body {{ font-family: sans-serif; background-color: #f4f4f9; color: #333; max-width: 800px; margin: 40px auto; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1, h2 {{ color: #0056b3; }}
        a {{ color: #007bff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ background-color: #fff; margin: 5px 0; padding: 10px; border-radius: 4px; border: 1px solid #ddd; }}
        form {{ background-color: #fff; padding: 20px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 20px; }}
        input[type="file"] {{ border: 1px solid #ccc; padding: 5px; border-radius: 4px; }}
        input[type="submit"] {{ background-color: #28a745; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; }}
        input[type="submit"]:hover {{ background-color: #218838; }}
        progress {{ width: 100%; height: 25px; margin-top: 10px; }}
        #cancel-btn {{
            display: none;
            background-color: #dc3545;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-left: 10px;
        }}
        #cancel-btn:hover {{ background-color: #c82333; }}
        #status {{ margin-top: 10px; font-weight: bold; }}
      </style>
    </head>
    <body>
        <h1>Il nostro piccolo file server</h1>

        <h2>Upload a New File</h2>
        <form id="upload-form" action="/upload" method="post" enctype="multipart/form-data">
          <input type="file" name="file" id="file-input" required>
          <input type="submit" value="Upload">
          <button type="button" id="cancel-btn">Cancel</button>
        </form>

        <progress id="progress-bar" value="0" max="100"></progress>
        <p id="status">Select a file and click Upload.</p>

        <h2>Available Files</h2>
        <ul>
    """

    if not files:
        html += "<li>No files have been uploaded yet.</li>"
    else:
        for filename in files:
            download_url = url_for('download_file', filename=filename)
            html += f'<li><a href="{download_url}">{filename}</a></li>'

    html += """
        </ul>

        <script>
            const form = document.getElementById('upload-form');
            const fileInput = document.getElementById('file-input');
            const submitBtn = form.querySelector('input[type="submit"]');
            const progressBar = document.getElementById('progress-bar');
            const status = document.getElementById('status');
            const cancelBtn = document.getElementById('cancel-btn');

            let xhr;

            function resetForm() {
                fileInput.disabled = false;
                submitBtn.disabled = false;
                cancelBtn.style.display = 'none';
                progressBar.value = 0;
            }

            cancelBtn.addEventListener('click', function() {
                if (xhr) {
                    xhr.abort();
                }
            });

            form.addEventListener('submit', function(event) {
                // Prevent the default form submission
                event.preventDefault();

                const file = fileInput.files[0];
                if (!file) {
                    status.textContent = 'Please select a file to upload.';
                    return;
                }

                // UI changes for upload start
                fileInput.disabled = true;
                submitBtn.disabled = true;
                cancelBtn.style.display = 'inline-block';

                // Create a FormData object to hold the file
                const formData = new FormData();
                formData.append('file', file);

                // Create a new XMLHttpRequest
                xhr = new XMLHttpRequest();

                // Listen for progress events
                xhr.upload.addEventListener('progress', function(event) {
                    if (event.lengthComputable) {
                        const percentComplete = (event.loaded / event.total) * 100;
                        progressBar.value = percentComplete;
                        status.textContent = 'Uploading... ' + Math.round(percentComplete) + '%';
                    }
                });

                // Handle successful upload
                xhr.addEventListener('load', function() {
                    if (xhr.status >= 200 && xhr.status < 300) {
                        status.textContent = 'Upload complete! Refreshing...';
                        progressBar.value = 100;
                        window.location.reload();
                    } else {
                        status.textContent = 'Upload failed: ' + (xhr.statusText || 'Server error');
                        resetForm();
                    }
                });

                // Handle upload errors
                xhr.addEventListener('error', function() {
                    status.textContent = 'Upload failed. A network error occurred.';
                    resetForm();
                });

                // Handle upload cancellation
                xhr.addEventListener('abort', function() {
                    status.textContent = 'Upload canceled.';
                    resetForm();
                });

                // Open the request and send the file
                xhr.open('POST', '/upload');
                xhr.send(formData);
            });
        </script>

    </body>
    </html>
    """
    return html

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        # Return a success message
        return jsonify({'message': 'File uploaded successfully'}), 200

@app.route('/download/<path:filename>')
def download_file(filename):
    """
    Serves a specific file for download.
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

# simple app.run server
#if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=8080, debug=True)

# waitress server
if __name__ == '__main__':
    from waitress import serve

    # Calculate 80GB in bytes
    eighty_gb = 80 * 1024 * 1024 * 1024

    print("Server running at http://<your-ip>:8080")
    serve(
        app,
        host='0.0.0.0',
        port=8080,
        max_request_body_size=eighty_gb,
        channel_timeout=1800 # Timeout in seconds (30 minutes)
    )
