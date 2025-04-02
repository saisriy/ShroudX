import os
from flask import Flask, render_template, request, send_file
import text_in_image  # Import your existing script

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    encoded_image_lsb = None
    encoded_image_random = None
    decoded_text = None
    metrics = {}

    if request.method == "POST":
        if "encode" in request.form:
            image_file = request.files["image"]
            text_file = request.files["text"]

            if image_file and text_file:
                image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
                text_path = os.path.join(UPLOAD_FOLDER, text_file.filename)
                image_file.save(image_path)
                text_file.save(text_path)

                # File paths for outputs
                encoded_lsb_path = os.path.join(OUTPUT_FOLDER, "encoded_lsb.png")
                encoded_random_path = os.path.join(OUTPUT_FOLDER, "encoded_random.png")

                # Call your existing LSB and Random LSB functions
                text_in_image.embed_text_LSB(image_path, text_path, encoded_lsb_path)
                text_in_image.embed_text_random(image_path, text_path, encoded_random_path)

                encoded_image_lsb = encoded_lsb_path
                encoded_image_random = encoded_random_path

        elif "decode" in request.form:
            image_file = request.files["stego_image"]

            if image_file:
                image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
                image_file.save(image_path)

                # Extract text using LSB method
                decoded_text_path = os.path.join(OUTPUT_FOLDER, "decoded.txt")
                text_in_image.extract_text_random(image_path, decoded_text_path)

                decoded_text = decoded_text_path

                # Evaluate steganography
                original_image = request.form.get("original_image", "")  # Original image used for encoding
                if original_image:
                    metrics = text_in_image.evaluate_steganography(original_image, image_path)

    return render_template(
        "index.html", 
        encoded_image_lsb=encoded_image_lsb, 
        encoded_image_random=encoded_image_random, 
        decoded_text=decoded_text,
        metrics=metrics
    )

if __name__ == "__main__":
    app.run(debug=True)
