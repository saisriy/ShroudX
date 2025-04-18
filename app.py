import os
from flask import Flask, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
import text_in_image  # Import your existing script
import text_in_text_zwc
import text_in_text_caecip
# import semantic_based
# import syntax_based
import time
import nltk

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "static/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html",)

@app.route("/page2", methods=["GET"])
def page2():
    return render_template('page2.html')

@app.route("/page5", methods=["GET"])
def page4():
    return render_template('page5.html')

@app.route("/page1", methods=["GET", "POST"])
def index():
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

@app.route("/sub1", methods=["GET", "POST"])
def sub1():
    encoded_output_file = None
    decoded_output_file = None
    encryption_key = None
    error_message = {}  # Store error messages
    expiry = None
    form_submitted = None
    embed_time=None

    if request.method == "POST":
        if "encode" in request.form:
            form_submitted = "encode"
            try:
                cover_file = request.files.get("cover_text")
                secret_file = request.files.get("secret_file")
                expiry = int(request.form.get("expiry"))  

                if not cover_file or not secret_file:
                    error_message = "Both cover text and secret file are required."
                else:
                    cover_path = os.path.join("uploads", os.path.join(cover_file.filename))
                    secret_path = os.path.join("uploads", os.path.join(secret_file.filename))

                    cover_file.save(cover_path)
                    secret_file.save(secret_path)

                    start_time = time.time()

                    # Read the secret message from the uploaded file
                    with open(secret_path, "r", encoding="utf-8") as sfile:
                        secret_message = sfile.read()

                    output_file = os.path.join(OUTPUT_FOLDER, "stego_text.txt")

                    encryption_key = text_in_text_zwc.encode_stego_file(
                        input_file=cover_path,
                        secret_message=secret_message,
                        output_file=output_file,
                        expiry_seconds=expiry
                    )
                    encoded_output_file = output_file
            except Exception as e:
                error_message = f"Encoding failed: {e}"

            end_time = time.time()
            embed_time = round(end_time - start_time, 4)

        elif "decode" in request.form:
            form_submitted = "decode"
            try:
                stego_file = request.files.get("stego_file")
                user_key = request.form.get("secret_key")

                if not stego_file or not user_key:
                    error_message = "Both stego file and secret key are required."
                else:
                    stego_path = os.path.join(UPLOAD_FOLDER, stego_file.filename)
                    stego_file.save(stego_path)

                    output_file = os.path.join(OUTPUT_FOLDER, "decoded_message.txt")

                    text_in_text_zwc.decode_stego_file(
                        stego_file=stego_path,
                        output_file=output_file,
                        user_key=user_key
                    )

                    decoded_output_file = output_file
            except Exception as e:
                error_message = f"Decoding failed: {e}"

    return render_template(
        "sub1.html",
        encoded_output_file=encoded_output_file,
        decoded_output_file=decoded_output_file,
        encryption_key=encryption_key,
        error_message=error_message,
        form_submitted=form_submitted,
        expiry=expiry,
        embed_time=embed_time
    )

@app.route("/sub2", methods=["GET", "POST"])
def sub2():
    encoded_output_file = None
    decoded_output_file = None
    encryption_key = None
    error_message = {}  # Store error messages
    expiry = None
    embed_time = None
    form_submitted = None

    if request.method == "POST":
        if "encode" in request.form:
            form_submitted = "encode"
            try:
                secret_file = request.files.get("secret_file")
                expiry = int(request.form.get("expiry", 60))  # default 60 seconds if not given

                if not secret_file:
                    error_message = "Secret file is required."
                else:
                    secret_path = os.path.join("uploads", secret_file.filename)
                    secret_file.save(secret_path)

                    output_file = os.path.join(OUTPUT_FOLDER, "stego_text_caecip.txt")

                    start_time = time.time()

                    encryption_key = text_in_text_caecip.encrypt(
                        secret_file=secret_path,
                        output_file=output_file,
                        expiry_seconds=expiry
                    )

                    end_time = time.time()
                    embed_time = round(end_time - start_time, 4)

                    encoded_output_file = output_file
            except Exception as e:
                error_message = f"Encoding failed: {e}"

        elif "decode" in request.form:
            form_submitted = "decode"
            try:
                stego_file = request.files.get("stego_file")
                user_key = request.form.get("secret_key")

                if not stego_file or not user_key:
                    error_message = "Both stego file and secret key are required."
                else:
                    stego_path = os.path.join(UPLOAD_FOLDER, stego_file.filename)
                    stego_file.save(stego_path)

                    output_file = os.path.join(OUTPUT_FOLDER, "decoded_message_caecip.txt")

                    # Use the updated decrypt() function which returns status and message
                    success, message = text_in_text_caecip.decrypt(
                        secret_file=stego_path,
                        output_file=output_file,
                        user_key=user_key
                    )

                    if success:
                        decoded_output_file = output_file
                    else:
                        error_message = message
            except Exception as e:
                error_message = f"Decoding failed: {e}"

    return render_template(
        "sub2.html",
        encoded_output_file=encoded_output_file,
        decoded_output_file=decoded_output_file,
        encryption_key=encryption_key,
        error_message=error_message,
        form_submitted=form_submitted,
        expiry=expiry,
        embed_time=embed_time
    )
 
# @app.route("/sub3", methods=["GET", "POST"])
# def sub3():
#     encoded_output_file = None
#     decoded_output_file = None
#     encryption_key = None
#     error_message = {}  # Store error messages
#     form_submitted = None

#     if request.method == "POST":
#         if "encode" in request.form:
#             form_submitted = "encode"
#             try:
#                 cover_file = request.files.get("cover_text")
#                 secret_file = request.files.get("secret_file")
#                 expiry = int(request.form["expiry"])

#                 if not cover_file or not secret_file:
#                     error_message = "Both cover text and secret file are required."
#                 else:
#                     cover_path = os.path.join("uploads", os.path.join(cover_file.filename))
#                     secret_path = os.path.join("uploads", os.path.join(secret_file.filename))

#                     cover_file.save(cover_path)
#                     secret_file.save(secret_path)

#                     # Read the secret message from the uploaded file
#                     with open(secret_path, "r", encoding="utf-8") as sfile:
#                         secret_message = sfile.read()

#                     output_file = os.path.join(OUTPUT_FOLDER, "stego_text.txt")

#                     encryption_key = semantic_based.encode_stego_file(
#                         input_file=cover_path,
#                         secret_message=secret_message,
#                         output_file=output_file,
#                         expiry_seconds=expiry
#                     )
#                     encoded_output_file = output_file
#             except Exception as e:
#                 error_message = f"Encoding failed: {e}"

#         elif "decode" in request.form:
#             form_submitted = "decode"
#             try:
#                 stego_file = request.files.get("stego_file")
#                 user_key = request.form.get("secret_key")

#                 if not stego_file or not user_key:
#                     error_message = "Both stego file and secret key are required."
#                 else:
#                     stego_path = os.path.join(UPLOAD_FOLDER, stego_file.filename)
#                     stego_file.save(stego_path)

#                     output_file = os.path.join(OUTPUT_FOLDER, "decoded_message.txt")

#                     text_in_text_zwc.decode_stego_file(
#                         stego_file=stego_path,
#                         output_file=output_file,
#                         user_key=user_key
#                     )

#                     decoded_output_file = output_file
#             except Exception as e:
#                 error_message = f"Decoding failed: {e}"

#     return render_template(
#         "sub3.html",
#         encoded_output_file=encoded_output_file,
#         decoded_output_file=decoded_output_file,
#         encryption_key=encryption_key,
#         error_message=error_message,
#         form_submitted=form_submitted
#     )

# @app.route("/sub4", methods=["GET", "POST"])
# def sub4():
#     encoded_output_file = None
#     decoded_output_file = None
#     encryption_key = None
#     error_message = {}  # Store error messages
#     form_submitted = None

#     if request.method == "POST":
#         if "encode" in request.form:
#             form_submitted = "encode"
#             try:
#                 cover_file = request.files.get("cover_text")
#                 secret_file = request.files.get("secret_file")
#                 expiry = int(request.form["expiry"])

#                 if not cover_file or not secret_file:
#                     error_message = "Both cover text and secret file are required."
#                 else:
#                     cover_path = os.path.join("uploads", os.path.join(cover_file.filename))
#                     secret_path = os.path.join("uploads", os.path.join(secret_file.filename))

#                     cover_file.save(cover_path)
#                     secret_file.save(secret_path)

#                     # Read the secret message from the uploaded file
#                     with open(secret_path, "r", encoding="utf-8") as sfile:
#                         secret_message = sfile.read()

#                     output_file = os.path.join(OUTPUT_FOLDER, "stego_text.txt")

#                     encryption_key = text_in_text_caecip.encode_stego_file(
#                         input_file=cover_path,
#                         secret_message=secret_message,
#                         output_file=output_file,
#                         expiry_seconds=expiry
#                     )
#                     encoded_output_file = output_file
#             except Exception as e:
#                 error_message = f"Encoding failed: {e}"

#         elif "decode" in request.form:
#             form_submitted = "decode"
#             try:
#                 stego_file = request.files.get("stego_file")
#                 user_key = request.form.get("secret_key")

#                 if not stego_file or not user_key:
#                     error_message = "Both stego file and secret key are required."
#                 else:
#                     stego_path = os.path.join(UPLOAD_FOLDER, stego_file.filename)
#                     stego_file.save(stego_path)

#                     output_file = os.path.join(OUTPUT_FOLDER, "decoded_message.txt")

#                     text_in_text_zwc.decode_stego_file(
#                         stego_file=stego_path,
#                         output_file=output_file,
#                         user_key=user_key
#                     )

#                     decoded_output_file = output_file
#             except Exception as e:
#                 error_message = f"Decoding failed: {e}"

#     return render_template(
#         "sub4.html",
#         encoded_output_file=encoded_output_file,
#         decoded_output_file=decoded_output_file,
#         encryption_key=encryption_key,
#         error_message=error_message,
#         form_submitted=form_submitted
#     )

if __name__ == "__main__":
    app.run(debug=True)
