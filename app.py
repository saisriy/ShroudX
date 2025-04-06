import os
from flask import Flask, render_template, request, send_file,jsonify
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
    show_metrics_button = False 
    error_message = None  # Store error messages

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
                # encoded_lsb_path = os.path.join(OUTPUT_FOLDER, "encoded_lsb.png")
                encoded_random_path = os.path.join(OUTPUT_FOLDER, "encoded_random.png")

                # Call your existing LSB and Random LSB functions
                #text_in_image.embed_text_LSB(image_path, text_path, encoded_lsb_path)
                try:
                    # Call the encoding function
                    text_in_image.embed_text_random(image_path, text_path, encoded_random_path)
                    encoded_image_random = encoded_random_path

                except ValueError as e:
                    error_message = str(e)

        elif "decode" in request.form:
            image_file = request.files["stego_image"]

            if image_file:
                image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
                image_file.save(image_path)

                # Extract text using LSB method
                decoded_text_path = os.path.join(OUTPUT_FOLDER, "decoded.txt")
                key_str = request.form.get("secret_key", "").strip()
                try:
                    key = int(key_str)
                    text_in_image.extract_text_random(image_path, decoded_text_path, key)
                except ValueError:
                    error_message = "Invalid key format. Please enter a valid integer key."
                



                decoded_text = decoded_text_path
                                

                # Evaluate only if original image is provided
                original_image = request.form.get("original_image", "").strip()
                original_text = request.form.get("original_text", "").strip()
                print("hiya")
                
                if original_image and original_text:
                    metrics = text_in_image.evaluate_steganography(original_image, image_path, original_text, decoded_text_path)
                    print("Metrics:", metrics)

                show_metrics_button = True 
    return render_template(
        "index.html", 
        #encoded_image_lsb=encoded_image_lsb, 
        encoded_image_random=encoded_image_random, 
        decoded_text=decoded_text,
        metrics=metrics,
        show_metrics_button=show_metrics_button,
        error_message=error_message
    )

@app.route("/evaluate", methods=["GET", "POST"])
def evaluate():
    metrics = {}
    if request.method == "POST":
        original_image = request.files["original_image"]
        stego_image = request.files["stego_image"]

        if original_image and stego_image:
            original_path = os.path.join(UPLOAD_FOLDER, original_image.filename)
            stego_path = os.path.join(UPLOAD_FOLDER, stego_image.filename)
            original_image.save(original_path)
            stego_image.save(stego_path)

            metrics = text_in_image.evaluate_steganography(original_path, stego_path)

    return render_template("evaluate.html", metrics=metrics)

    

if __name__ == "__main__":
    app.run(debug=True)
