import os
import cv2
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS  # Ensure CORS support
from image_in_image import start_Encode, DEcode_lsb, Read_image  # Import encoding/decoding functions

app = Flask(__name__)
CORS(app)  # Enable CORS to allow frontend access

# Folder paths for uploaded and processed images
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/")
def home():
    return "Image Steganography API is running!"

@app.route("/encode", methods=["POST"])
def encode_image():
    if "cover_image" not in request.files or "secret_image" not in request.files:
        return jsonify({"error": "Missing images"}), 400

    cover_img = request.files["cover_image"]
    secret_img = request.files["secret_image"]

    # Define paths
    cover_path = os.path.join(UPLOAD_FOLDER, "cover.png")
    secret_path = os.path.join(UPLOAD_FOLDER, "secret.png")
    stego_path = os.path.join(OUTPUT_FOLDER, "stego.png")

    # Save images
    cover_img.save(cover_path)
    secret_img.save(secret_path)

    # Debugging: Check if files are saved
    if not os.path.exists(cover_path) or not os.path.exists(secret_path):
        return jsonify({"error": "Failed to save uploaded images"}), 500

    try:
        # Read the secret image
        secret_image = Read_image(secret_path)
        if secret_image is None or not isinstance(secret_image, np.ndarray):
            return jsonify({"error": "Failed to read secret image"}), 500

        # Debugging output
        print(f"DEBUG: Secret image read successfully - Shape: {secret_image.shape}, Type: {secret_image.dtype}")

        # Perform encoding
        secret_size = start_Encode(cover_path, secret_image, stego_path)

        # Debugging: Check if stego image is saved
        if not os.path.exists(stego_path):
            return jsonify({"error": "Encoding failed, stego image not created"}), 500

        print(f"DEBUG: Stego image saved successfully at {stego_path}")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "message": "Encoding complete",
        "stego_image": f"http://{request.host}/outputs/stego.png",
        "secret_size": secret_size
    })

@app.route("/decode", methods=["POST"])
def decode_image():
    # Ensure the secret size is provided in the request
    data = request.get_json()
    if not data or "secret_size" not in data:
        return jsonify({"error": "Missing secret size"}), 400

    secret_size = tuple(data["secret_size"])  # Ensure it's a tuple
    stego_path = os.path.join(OUTPUT_FOLDER, "stego.png")
    extracted_secret_path = os.path.join(OUTPUT_FOLDER, "extracted_secret.png")

    # Debugging: Print received secret size
    print(f"DEBUG: Received secret size for decoding - {secret_size}")

    if not os.path.exists(stego_path):
        return jsonify({"error": "Stego image not found"}), 400

    try:
        extracted_secret = DEcode_lsb(stego_path, extracted_secret_path, secret_size)
        if extracted_secret is None:
            return jsonify({"error": "Failed to decode secret image"}), 500

        # Save the extracted secret image
        cv2.imwrite(extracted_secret_path, extracted_secret)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "message": "Decoding complete",
        "extracted_secret_image": f"http://{request.host}/outputs/extracted_secret.png"
    })

# Serve static files
@app.route("/outputs/<path:filename>")
def serve_output_files(filename):
    return send_from_directory(os.path.abspath(OUTPUT_FOLDER), filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
