import os
from flask import Flask, render_template, request, send_file, jsonify
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
    error_messages = {}   # Store error messages
    form_submitted = None 

    if request.method == "POST":
        if "encode" in request.form:
            form_submitted = "encode"
            image_file = request.files["image"]
            text_file = request.files["text"]
            if not image_file:
                error_messages["encode_image"] = "Please upload an image for encoding."

            if not text_file:
                error_messages["encode_text"] = "Please upload a text file to encode."

            if image_file and text_file:
                image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
                text_path = os.path.join(UPLOAD_FOLDER, text_file.filename)
                image_file.save(image_path)
                text_file.save(text_path)

                encoded_random_path = os.path.join(OUTPUT_FOLDER, "encoded_random.png")

                try:
                    text_in_image.embed_text_random(image_path, text_path, encoded_random_path)
                    encoded_image_random = encoded_random_path
                except ValueError as e:
                    error_messages["encode_random"] = str(e)

        elif "decode" in request.form:
            form_submitted = "decode"
            image_file = request.files["stego_image"]
            key_str = request.form.get("secret_key", "").strip()

            if not image_file:
                error_messages["decode_image"] = "Please upload a stego image to decode."

            if not key_str:
                error_messages["decode_key"] = "Please enter the secret key."
            else:
                try:
                    key = int(key_str)
                except ValueError as e:
                    error_messages["decode_key"] = f"Invalid key format: {e}"
                    key = None  # So we don’t proceed with invalid key

            if image_file and key is not None:
                image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
                image_file.save(image_path)

                decoded_text_path = os.path.join(OUTPUT_FOLDER, "decoded.txt")

                try:
                    key = int(key_str)
                    result = text_in_image.extract_text_random(image_path, decoded_text_path, key)
                    if result is False:  # We'll update the function to return False on failure
                        error_messages["decode_random"] = "Incorrect key or corrupted image. Please try again."
                    else:
                        decoded_text = decoded_text_path
                except ValueError as e:
                    error_messages["decode_random"] = str(e)


                # Optional metrics evaluation
                original_image = request.form.get("original_image", "").strip()
                original_text = request.form.get("original_text", "").strip()
                
                if original_image and original_text:
                    try:
                        metrics = text_in_image.evaluate_steganography(
                            original_image, image_path, original_text, decoded_text_path
                        )
                        print("Metrics:", metrics)
                    except Exception as e:
                        error_messages["metrics_error"] = f"Error during evaluation: {e}"

                show_metrics_button = True 

    return render_template(
        "index.html", 
        encoded_image_random=encoded_image_random, 
        decoded_text=decoded_text,
        metrics=metrics,
        show_metrics_button=show_metrics_button,
        error_messages=error_messages,
        form_submitted=form_submitted 
    )


@app.route("/evaluate", methods=["GET", "POST"])
def evaluate():
    metrics = {}
    if request.method == "POST":
        original_image = request.files.get("original_image")
        stego_image = request.files.get("stego_image")

        if original_image and stego_image:
            original_path = os.path.join(UPLOAD_FOLDER, original_image.filename)
            stego_path = os.path.join(UPLOAD_FOLDER, stego_image.filename)
            original_image.save(original_path)
            stego_image.save(stego_path)

            try:
                metrics = text_in_image.evaluate_steganography(original_path, stego_path)
            except Exception as e:
                return render_template("evaluate.html", error=str(e))

    return render_template("evaluate.html", metrics=metrics)

if __name__ == "__main__":
    app.run(debug=True)
