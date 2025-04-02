import cv2
import numpy as np
import secrets
from skimage.metrics import structural_similarity as ssim

       ### LEVEL 1 IMPLEMENTATION OF TEXT IN IMAGE STEGANOGRAPHY ###

# Function to embed text into an image
def embed_text_LSB(image_path, text_file, output_path):
    image = cv2.imread(image_path)
    height, width, _ = image.shape
    max_bits = width * height * 3
    max_chars = max_bits // 8  
    with open(text_file, "r") as file:
        message = file.read()
   
    # Append a delimiter to mark the end of the message
    message += "#####"
    binary_message = ''.join(format(ord(char), '08b') for char in message)

    # Check if message fits
    if len(binary_message) > max_bits:
        print(f"Error: Message too long! Max {max_chars} characters can be embedded.")
        return
    
    data_index = 0
    message_length = len(binary_message)
    
    for row in image:
        for pixel in row:
            for channel in range(3):  
                if data_index < message_length:
                    pixel[channel] = (pixel[channel] & 254) | int(binary_message[data_index]) 
                    data_index += 1
                else:
                    break
    
    cv2.imwrite(output_path, image)
    print(f"Message embedded and saved as {output_path}")


# Function to extract text from an image
def extract_text_LSB(image_path, output_text_file):
    """ Extract hidden text from an image and save it to a file """
    image = cv2.imread(image_path)
    binary_message = ""
    
    for row in image:
        for pixel in row:
            for channel in range(3):  # Read RGB channels
                binary_message += str(pixel[channel] & 1)

    # Convert binary to text
    message = ""
    for i in range(0, len(binary_message), 8):
        byte = binary_message[i:i+8]
        char = chr(int(byte, 2))
        if message.endswith("#####"):  # Stop at delimiter
            message = message[:-5]
            break
        message += char

    with open(output_text_file, "w") as file:
        file.write(message)
    
    print(f"Extracted message saved as {output_text_file}")




# File paths
original_image = "butter.jpg"
text_file = "abc.txt"
decoded_text_file = "decoded_abc.txt"
stego_image = "static/outputs/encoded_butter.png"

# Embed and evaluate
embed_text_LSB(original_image, text_file, stego_image)

extract_text_LSB(stego_image, decoded_text_file)

