import os
from flask import Flask, render_template, request, send_file, jsonify
from crypto_utils import encrypt, decrypt
import time 


import text_in_image  

import image_in_image2

from audio_in_image import Start_Encode, Start_Decode 


app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
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
    embed_time = None
    decode_time = None

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
                expiry_str = request.form.get("expiry_time", "").strip()

                
                try:
                    expiry_seconds = int(expiry_str) if expiry_str else None
                except ValueError:
                    expiry_seconds = None
                    error_messages["encode_expiry"] = "Invalid expiry time format."

                try:
                    start_time = time.time()
                    if expiry_seconds:
                        encoded_random_path, key = text_in_image.embed_text_random_expire(image_path, text_path, encoded_random_path, expiry_seconds)
                    else:
                        encoded_random_path, key = text_in_image.embed_text_random(image_path, text_path, encoded_random_path)
                    end_time = time.time()
                    embed_time = round(end_time - start_time, 4)

                    encoded_image_random = encoded_random_path
                    key_used = encrypt(str(key), "your-secret-password")
                except ValueError as ve:
                    error_messages["encode_random"] = str(ve)
                    

        elif "decode" in request.form:
            form_submitted = "decode"
            image_file = request.files.get("stego_image")
            encrypted_key_str = request.form.get("secret_key", "").strip()
            try:
                key_str = decrypt(encrypted_key_str, "your-secret-password")
                key = int(key_str)
            except Exception as e:
                error_messages["decode_key"] = f"Invalid or corrupted key: {e}"
                key = None


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
                start_decode = time.time()
                result = text_in_image.extract_text_random_expire(image_path, decoded_text_path, key)
                end_decode = time.time()
                decode_time = round(end_decode - start_decode, 4)
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
        key_used=key_used,
        embed_time=embed_time,
        decode_time=decode_time
    )





@app.route("/page3", methods=["GET", "POST"])
def image_in_image_page():
    encoded_image_path = None
    decoded_image_path = None
    error = None
    encrypted_key = None
    embed_time = None
    decode_time = None
    encode_error = None
    decode_error = None
    time_limit_error = None

    aes_password = "your-secret-password"

    if request.method == "POST":
        action = request.form.get("action")

        if action == "encode":
            cover_img = request.files.get("cover_image")
            secret_img = request.files.get("secret_image")
            expiry_time = request.form.get("expiry_time")

            if not cover_img or not secret_img or not expiry_time:
                encode_error = "Cover image, secret image, and expiry time are required."
            else:
                try:
                    expiry_seconds = int(expiry_time)
                except ValueError:
                    encode_error = "Expiry time must be a valid integer."
                    return render_template("page3.html", encode_error=encode_error)

                cover_path = os.path.join(UPLOAD_FOLDER, cover_img.filename)
                secret_path = os.path.join(UPLOAD_FOLDER, secret_img.filename)
                stego_path = os.path.join(OUTPUT_FOLDER, "stego_image.png")

                cover_img.save(cover_path)
                secret_img.save(secret_path)

                try:
                    start_time = time.time()
                    secret_info, level,x = image_in_image2.Start_Encode(cover_path, secret_path, stego_path)
                    end_time = time.time()
                    embed_time = round(end_time - start_time, 4)

                    # Encrypt [w, h, cw, ch, level, timestamp, expiry]
                    encode_timestamp = int(time.time())
                    key_values = secret_info + [level, encode_timestamp, expiry_seconds,x ]
                    key_string = ','.join(map(str, key_values))
                    encrypted_key = encrypt(key_string, aes_password)

                    encoded_image_path = stego_path
                except Exception as e:
                    encode_error = f"Encoding failed: {str(e)}"

        elif action == "decode":
            stego_img = request.files.get("stego_image")
            encrypted_key_input = request.form.get("manual_key")

            if not stego_img or not encrypted_key_input:
                decode_error = "Stego image and encrypted key are required for decoding."
            else:
                stego_path = os.path.join(UPLOAD_FOLDER, stego_img.filename)
                decoded_path = os.path.join(OUTPUT_FOLDER, "decoded_secret.png")
                stego_img.save(stego_path)

                try:
                    decrypted_key = decrypt(encrypted_key_input.strip(), aes_password)
                    data = list(map(int, decrypted_key.split(',')))

                    if len(data) != 8:
                        raise ValueError("Decrypted key must contain exactly 7 integers.")

                    size = data[:4]
                    level = data[4]
                    encode_time = data[5]
                    expiry_seconds = data[6]
                    x = data[7]

                    current_time = int(time.time())
                    if current_time - encode_time > expiry_seconds:
                        time_limit_error = "time limit exceeded"
                        time_limit_error = "Time limit exceeded"
                        return render_template(
                            "page3.html",
                            encoded_image_path=None,
                            decoded_image_path=None,
                            error=None,
                            encode_error=encode_error,
                            decode_error=None,
                            encrypted_key=None,
                            embed_time=None,
                            decode_time=None,
                            time_limit_error=time_limit_error
                        )

                    start_decode = time.time()
                    image_in_image2.DECode_lsb(stego_path, decoded_path, size, level,x)
                    decoded_image_path = decoded_path
                    end_decode = time.time()
                    decode_time = round(end_decode - start_decode, 4)
                except Exception as e:
                    decode_error = f"Decoding failed: {str(e)}"

    return render_template(
        "page3.html",
        encoded_image_path=encoded_image_path,
        decoded_image_path=decoded_image_path,
        error=error,
        encode_error=encode_error,
        decode_error=decode_error,
        encrypted_key=encrypted_key,
        embed_time=embed_time,
        decode_time=decode_time,
        time_limit_error = time_limit_error
    )


    
@app.route('/page4', methods=['GET', 'POST'])
def audio_in_image():
    result = {}
    if request.method == 'POST':
        action = request.form.get("action")

        if action == "encode":
            audio_file = request.files.get("audio_file")
            cover_image = request.files.get("cover_image")
            expiry = request.form.get("expiry_time", "60")  # default to 60s

            if audio_file and cover_image:
                audio_path = os.path.join(UPLOAD_FOLDER, audio_file.filename)
                cover_path = os.path.join(UPLOAD_FOLDER, cover_image.filename)
                stego_path = os.path.join(UPLOAD_FOLDER, "stego_image_audio.png")

                audio_file.save(audio_path)
                cover_image.save(cover_path)

                try:
                    start_time = time.time()
                    key = Start_Encode(audio_path, cover_path, int(expiry), stego_path)
                    embed_time = round(time.time() - start_time, 2)

                    result.update({
                        "encoded_image_path": stego_path,
                        "key": key,
                        "embed_time": embed_time
                    })
                except Exception as e:
                    result["error"] = f"Encoding failed: {str(e)}"

        elif action == "decode":
            stego_image = request.files.get("stego_image")
            key = request.form.get("manual_key")

            if stego_image and key:
                stego_path = os.path.join("static/uploads", stego_image.filename)
                retrieved_audio_path = os.path.join("static/uploads", "retrieved_audio.wav")
                stego_image.save(stego_path)

                try:
                    key = int(key.strip())

                    start_time = time.time()
                    success = Start_Decode(stego_path, key, retrieved_audio_path)
                    decode_time = round(time.time() - start_time, 2)

                    if success:
                        result.update({
                            "retrieved_audio_path": retrieved_audio_path,
                            "decode_time": decode_time
                        })
                    else:
                        result["decode_error"] = "Extraction failed: Possibly expired or wrong key."
                except Exception as e:
                    result["decode_error"] = f"Decoding failed: {str(e)}"

    return render_template("page4.html", **result)



@app.route("/evaluate_im", methods=["GET","POST"])
def evaluate_im():
    psnr_value = None
    hamming_value = None
    eval_error = None

    if request.method == "POST":
        original_image = request.files.get("original_image")
        stego_image = request.files.get("stego_image")

        if original_image and stego_image:
            original_path = os.path.join(UPLOAD_FOLDER, original_image.filename)
            stego_path = os.path.join(UPLOAD_FOLDER, stego_image.filename)
            original_image.save(original_path)
            stego_image.save(stego_path)

            try:
                psnr_value = image_in_image2.calculate_psnr_im_im(original_path, stego_path)
                hamming_value = image_in_image2.hamming_distance(original_path, stego_path)
            except Exception as e:
                eval_error = f"Error while evaluating: {str(e)}"

    return render_template("evaluate_im.html", psnr_value=psnr_value, hamming_value=hamming_value, eval_error=eval_error)
if __name__ == "__main__":
    app.run(debug=True)