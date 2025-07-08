import json
import requests
from PIL import Image
from io import BytesIO
import time
import os
from werkzeug.utils import secure_filename
import io

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}

def secure_file_path(base_dir, filename):
    """Create a secure file path that prevents directory traversal"""
    filename = secure_filename(filename)
    return os.path.join(base_dir, filename)

def validate_image(img_data):
    """Validate image size and format"""
    if len(img_data) > MAX_FILE_SIZE:
        raise ValueError("Image too large")
        
    try:
        img = Image.open(io.BytesIO(img_data))
        if img.format.lower() not in ALLOWED_EXTENSIONS:
            raise ValueError("Invalid image format")
        return img
    except Exception as e:
        raise ValueError(f"Invalid image: {str(e)}")

def fetch_and_save_image(camera_id, timestamp):
    """Fetch an image from the NYC traffic camera API"""
    try:
        api_url = f'https://webcams.nyctmc.org/api/cameras/{camera_id}/image?t={timestamp}'
        print(f"[DEBUG] Fetching image from: {api_url}")
        
        response = requests.get(api_url)
        print(f"[DEBUG] Response status: {response.status_code}, Content length: {len(response.content) if response.status_code == 200 else 0}")
        
        if response.status_code == 200:
            try:
                img_data = response.content
                img = validate_image(img_data)
                return img
            except ValueError as e:
                print(f"Image validation failed: {e}")
                return None
            except Exception as e:
                print(f"Image fetch failed: {e}")
                return None
        else:
            print(f"[ERROR] Failed to fetch image for camera {camera_id}. Status Code: {response.status_code}")
            if response.status_code != 404:  # Don't print potentially large error responses
                print(f"[DEBUG] Error response: {response.text[:200]}...")
            return None

    except Exception as e:
        print(f"[ERROR] Request failed for camera {camera_id}: {e}")
        return None

def load_camera_data(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("[ERROR] camera_addresses_to_id.json file not found. Please run the scraping script first.")
        return None
    except json.JSONDecodeError:
        print("[ERROR] JSON file is malformed.")
        return None