import os
from flask import Flask, render_template, request, send_file, jsonify


import text_in_image  

import image_in_image  


app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/page1", methods=["GET", "POST"])
def text_in_image_page():
    encoded_image_lsb = None
    encoded_image_random = None
    decoded_text = None
    metrics = {}
    show_metrics_button = False 
    error_messages = {
        "decode_image": "",
        "decode_key": "",
        "decode_random": "",
        "metrics_error": "",
        "encode": ""
    }  # Store error messages
    form_submitted = None 
    encoded_image_random = None
    key_used = None  

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
                    expiry_str = request.form.get("expiry_time", "").strip()
                    try:
                        expiry_seconds = int(expiry_str) if expiry_str else None
                    except ValueError:
                        expiry_seconds = None
                        error_messages["encode_expiry"] = "Invalid expiry time format."

                    # Embed with expiry if provided
                    if expiry_seconds:
                        key = text_in_image.embed_text_random_expire(image_path, text_path, encoded_random_path, expiry_seconds)
                    else:
                        key = text_in_image.embed_text_random(image_path, text_path, encoded_random_path)

                    encoded_image_random = encoded_random_path
                except ValueError as e:
                    error_messages["encode_random"] = str(e)
                try:
                    encoded_random_path, key_used = text_in_image.embed_text_random_expire(image_path, text_path, encoded_random_path, expiry_seconds)
                    encoded_image_random = encoded_random_path
                except ValueError as ve:
                    error_message = str(ve)

        elif "decode" in request.form:
            form_submitted = "decode"
            image_file = request.files.get("stego_image")
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
                    key = None

            # Only try to decode if both image and valid key are provided
            if image_file and key_str and key is not None:
                image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
                image_file.save(image_path)

                decoded_text_path = os.path.join(OUTPUT_FOLDER, "decoded.txt")
                result = text_in_image.extract_text_random_expire(image_path, decoded_text_path, key)

                if result is False:
                    error_messages["decode_random"] = "Message expired or invalid stego image/key."
                else:
                    decoded_text = decoded_text_path

                # Optional: Evaluate metrics if original image and text were provided
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
        pass

    return render_template(
        "page1.html", 
        encoded_image_random=encoded_image_random, 
        decoded_text=decoded_text,
        metrics=metrics,
        show_metrics_button=show_metrics_button,
        error_messages=error_messages,
        form_submitted=form_submitted,
        key_used=key_used 
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

@app.route("/page3", methods=["GET", "POST"])
def image_in_image_page():
    encoded_image_path = None
    decoded_image_path = None
    error = None
    key_values = [] 

    if request.method == "POST":
        action = request.form.get("action")

        if action == "encode":
            cover_img = request.files.get("cover_image")
            secret_img = request.files.get("secret_image")

            if not cover_img or not secret_img:
                error = "Both cover and secret images are required."
            else:
                cover_path = os.path.join(UPLOAD_FOLDER, cover_img.filename)
                secret_path = os.path.join(UPLOAD_FOLDER, secret_img.filename)
                stego_path = os.path.join(OUTPUT_FOLDER, "stego_image.png")
                key_path = os.path.join(OUTPUT_FOLDER, "secret_size_level.txt")

                cover_img.save(cover_path)
                secret_img.save(secret_path)

                try:
                    secret_info, level = image_in_image.Start_Encode(cover_path, secret_path, stego_path)
                    key_values = secret_info + [level]  # store key as list of 5 values
                    with open(key_path, "w") as f:
                        f.write(','.join(map(str, key_values)))
                    encoded_image_path = stego_path
                except Exception as e:
                    error = f"Encoding failed: {str(e)}"


        elif action == "decode":
            stego_img = request.files.get("stego_image")
            manual_key_str = request.form.get("manual_key")  # Get text input for key

            if not stego_img or not manual_key_str:
                error = "Stego image and key (5 comma-separated values) are required for decoding."
            else:
                stego_path = os.path.join(UPLOAD_FOLDER, stego_img.filename)
                decoded_path = os.path.join(OUTPUT_FOLDER, "decoded_secret.png")
                stego_img.save(stego_path)

                try:
                    # Parse and validate key input
                    data = list(map(int, manual_key_str.strip().split(',')))
                    if len(data) != 5:
                        raise ValueError("Please enter exactly 5 comma-separated integers.")
                    
                    size = data[:4]
                    level = data[4]

                    # Call decode
                    image_in_image.DECode_lsb(stego_path, decoded_path, size, level)
                    decoded_image_path = decoded_path
                except Exception as e:
                    error = f"Decoding failed: {str(e)}"


        

    return render_template(
        "page3.html",
        encoded_image_path=encoded_image_path,
        decoded_image_path=decoded_image_path,
        error=error,
        key_values=key_values
    )


if __name__ == "__main__":
    app.run(debug=True)
