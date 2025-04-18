import os
from flask import Flask, render_template, request, send_file, jsonify,redirect, url_for, session
from crypto_utils import encrypt, decrypt
import time 
from scipy.io import wavfile
from werkzeug.exceptions import RequestEntityTooLarge


import text_in_image  

import image_in_image2

from audio_in_image import Start_Encode, Start_Decode 

from logger import log_event




app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
OUTPUT_FOLDER = "static/outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.secret_key = "your-very-secret-key"

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 *1024  # 10 MB


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

def handle_large_file(e):
       return render_template('page3.html', error=" File too large. Max size is 200KB."), 200



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
                        log_event("TEXT_ENCODE", f"Image: {image_file.filename}, Text: {text_file.filename}, Expiry: {expiry_seconds}s")
                    else:
                        encoded_random_path, key = text_in_image.embed_text_random(image_path, text_path, encoded_random_path)
                        log_event("TEXT_ENCODE", f"Image: {image_file.filename}, Text: {text_file.filename}, No expiry")
                    end_time = time.time()
                    embed_time = round(end_time - start_time, 4)

                    encoded_image_random = encoded_random_path
                    
                    key_used = encrypt(str(key), "your-secret-password")
                except ValueError as ve:
                    error_messages["encode_random"] = str(ve)
                    log_event("TEXT_ENCODE_FAILED", f"Image: {image_file.filename}, Error: {ve}")
                    

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
                    log_event("TEXT_DECODE_FAILED", f"Image: {image_file.filename}, Key: {key_str[:4]}****")

                else:
                    decoded_text = decoded_text_path
                    log_event("TEXT_DECODE_SUCCESS", f"Image: {image_file.filename}, Key: {key_str[:4]}****")

                # Optional: Evaluate metrics if original image and text were provided
                original_image = request.form.get("original_image", "").strip()
                original_text = request.form.get("original_text", "").strip()
                
                if original_image and original_text:
                    try:
                        metrics = text_in_image.evaluate_steganography(
                            original_image, image_path, original_text, decoded_text_path
                        )
                        print("Metrics:", metrics)
                        log_event("METRICS_EVALUATED", f"Image: {image_file.filename}, Metrics: {metrics}")
                    except Exception as e:
                        error_messages["metrics_error"] = f"Error during evaluation: {e}"
                        log_event("METRICS_FAILED", f"Error evaluating metrics: {e}")

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
                    log_event("IMAGE_ENCODE", f"Cover: {cover_img.filename}, Secret: {secret_img.filename}, Expiry: {expiry_seconds}s")
                except Exception as e:
                    encode_error = f"Encoding failed: {str(e)}"
                    log_event("IMAGE_ENCODE_FAILED", f"Cover: {cover_img.filename}, Error: {e}")

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
                        log_event("IMAGE_DECODE_EXPIRED", f"Stego: {stego_img.filename}, Expired by {current_time - encode_time - expiry_seconds}s")
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
                    log_event("IMAGE_DECODE_SUCCESS", f"Stego: {stego_img.filename}, Level: {level}, Decode Time: {decode_time}s")
                except Exception as e:
                    decode_error = f"Decoding failed: {str(e)}"
                    log_event("IMAGE_DECODE_FAILED", f"Stego: {stego_img.filename}, Error: {e}")

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

@app.route("/page4", methods=["GET", "POST"])
def audio_in_image_page():
    encoded_image_path = None
    encoded_image_filename = None
    decoded_audio_path = None
    key_used = None
    embed_time = None
    decode_time = None
    error_messages = {
        "encode_audio": "",
        "encode_image": "",
        "encode_expiry": "",
        "decode_image": "",
        "decode_key": "",
        "decode_audio": ""
    }

    if request.method == "POST":
        if "encode" in request.form:
            audio_file = request.files.get("audio")
            image_file = request.files.get("cover_image")
            expiry_str = request.form.get("expiry_time", "").strip()

            if not audio_file:
                error_messages["encode_audio"] = "Please upload an audio file."

            if not image_file:
                error_messages["encode_image"] = "Please upload a cover image."

            try:
                expiry_seconds = int(expiry_str) if expiry_str else None
            except ValueError:
                expiry_seconds = None
                error_messages["encode_expiry"] = "Invalid expiry time format."

            if audio_file and image_file and expiry_seconds is not None:
                audio_path = os.path.join(UPLOAD_FOLDER, audio_file.filename)
                image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
                audio_file.save(audio_path)
                image_file.save(image_path)

                output_image_path = os.path.join(OUTPUT_FOLDER, "audio_stego.png")

                try:
                    start_time = time.time()
                    key, sample_rate = Start_Encode(audio_path, image_path, expiry_seconds, output_image_path)
                    end_time = time.time()
                    embed_time = round(end_time - start_time, 4)

                    encoded_image_path = output_image_path
                    encoded_image_filename = os.path.basename(encoded_image_path)
                    key_used = encrypt(f"{key}|{sample_rate}", "your-secret-password")  # Store both key & sample_rate

                    log_event("AUDIO_ENCODE", f"Audio: {audio_file.filename}, Image: {image_file.filename}, Expiry: {expiry_seconds}s")
                except Exception as e:
                    error_messages["encode_image"] = f"Encoding failed: {e}"
                    log_event("AUDIO_ENCODE_FAILED", f"Audio: {audio_file.filename}, Error: {e}")

        elif "decode" in request.form:
            stego_image = request.files.get("stego_image")
            encrypted_key_str = request.form.get("secret_key", "").strip()

            key = None
            sample_rate = None

            try:
                decrypted = decrypt(encrypted_key_str, "your-secret-password")
                key_str, sample_rate_str = decrypted.split("|")
                key = int(key_str)
                sample_rate = int(sample_rate_str)
                print(key,sample_rate)
            except Exception as e:
                error_messages["decode_key"] = f"Invalid or corrupted key: {e}"
                log_event("AUDIO_DECODE_KEY_ERROR", f"Invalid key or decryption failed: {e}")

            if not stego_image:
                error_messages["decode_image"] = "Please upload a stego image."

            if key is not None and stego_image and sample_rate is not None:
                image_path = os.path.join(UPLOAD_FOLDER, stego_image.filename)
                stego_image.save(image_path)

                decoded_audio_output = os.path.join(OUTPUT_FOLDER, "decoded_audio.wav")
                decoded_audio_output = decoded_audio_output.replace("\\", "/") 

                try:
                    start_time = time.time()
                    Start_Decode(image_path, key, sample_rate, decoded_audio_output)
                    end_time = time.time()
                    decode_time = round(end_time - start_time, 4)
                    decoded_audio_path = decoded_audio_output.split("static/")[-1]  # Extract the part after 'static/'

                    print(decoded_audio_path)
                    log_event("AUDIO_DECODE_SUCCESS", f"Stego: {stego_image.filename}, Decode Time: {decode_time}s")
                except Exception as e:
                    error_messages["decode_audio"] = f"Decoding failed: {e}"
                    log_event("AUDIO_DECODE_FAILED", f"Stego: {stego_image.filename}, Error: {e}")
    return render_template(
        "page4.html",
        encoded_image_path=encoded_image_path,
        encoded_image_filename=encoded_image_filename,
        decoded_audio_path=decoded_audio_path,
        key_used=key_used,
        embed_time=embed_time,
        decode_time=decode_time,
        error_messages=error_messages
    )
    


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
                log_event("EVALUATE_AUDIO_IMAGE", f"Original: {original_image.filename}, Stego: {stego_image.filename}, PSNR: {psnr_value}, Hamming: {hamming_value}")
            except Exception as e:
                eval_error = f"Error while evaluating: {str(e)}"
                log_event("EVALUATE_FAILED", f"Error: {e}")

            

    return render_template("evaluate_im.html", psnr_value=psnr_value, hamming_value=hamming_value, eval_error=eval_error)
if __name__ == "__main__":
    app.run(debug=False)