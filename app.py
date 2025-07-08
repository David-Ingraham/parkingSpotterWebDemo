import os
import json
import io
import sys
import time # Added for timestamp
from flask import Flask, jsonify, request, render_template, send_file, make_response
from PIL import Image, ImageDraw, ImageFont
import requests

# No longer need to modify sys.path since helpers is a local directory
from helpers.fetch_image import fetch_and_save_image

from ultralytics import YOLO

# --- Model Loading (Updated Path for flat structure) ---
model_path = os.path.join('model', 'weights.pt')
model = YOLO(model_path)

app = Flask(__name__) # templates and static are now in standard locations

# --- Helper Functions ---

def get_camera_data():
    """Loads camera data from the JSON file."""
    try:
        # Updated path for flat structure
        with open('camera_id_lat_lng_wiped.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: camera_id_lat_lng_wiped.json not found.")
        return {}

# --- Routes ---

@app.route('/')
def index():
    """Serves the main HTML page for the demo."""
    return render_template('index.html')

@app.route('/get_camera_names', methods=['GET'])
def get_camera_names():
    """Provides a list of camera names for autocomplete."""
    query = request.args.get('query', '').lower()
    camera_data = get_camera_data()
    
    if not query:
        return jsonify([])

    matches = []
    # Correctly iterate over the dictionary items
    for camera_name, info in camera_data.items():
        # The camera name is the KEY, not a value in the info dict.
        # We also need to replace underscores for user-friendly searching.
        searchable_name = camera_name.replace('_', ' ').lower()
        if query in searchable_name:
            matches.append({'id': info['camera_id'], 'name': camera_name.replace('_', ' ')})
            if len(matches) >= 15:  # Limit results for performance
                break
    
    return jsonify(matches)

@app.route('/detect_parking', methods=['GET'])
def detect_parking():
    """
    Fetches a live camera image, runs parking detection, and returns the
    image along with the count of open spots.
    """
    camera_id = request.args.get('camera_id')
    if not camera_id:
        return "Camera ID is required", 400

    # 1. Fetch the live image
    try:
        timestamp = int(time.time())
        img = fetch_and_save_image(camera_id, timestamp)
        if not img:
            return "Failed to fetch image from camera.", 404
    except Exception as e:
        return f"Error fetching image: {e}", 500

    # 2. Run the model on the image
    results = model(img, verbose=False)
    processed_img = Image.fromarray(results[0].plot()[..., ::-1])

    # 3. Count open parking spots
    open_parking_class_index = 1
    open_spots_count = sum(1 for box in results[0].boxes if int(box.cls) == open_parking_class_index)

    # 4. Prepare the multipart response
    img_io = io.BytesIO()
    processed_img.save(img_io, 'JPEG', quality=85)
    img_io.seek(0)
    
    response = make_response(img_io.getvalue())
    response.headers.set('Content-Type', 'image/jpeg')
    response.headers.set('X-Open-Spots-Count', str(open_spots_count))
    
    return response

if __name__ == '__main__':
    app.run(debug=True, port=5001) 