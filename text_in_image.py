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
    max_chars = max_bits // 8  # Each character takes 8 bits

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
            for channel in range(3):  # Iterate over RGB channels
                                      # first r then g then b
                if data_index < message_length:
                    pixel[channel] = (pixel[channel] & 254) | int(binary_message[data_index])  # Use 254 to ensure uint8 range
                    data_index += 1
                else:
                    break
    
    cv2.imwrite(output_path, image)
    print(f"Message embedded and saved as {output_path}")


# Function to extract text from an image
def extract_text_LSB(image_path, output_text_file):
    """Extract hidden text from an image and save it to a file"""
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

         
             ### level 2 implementation with random key generation ###


# Function to generate and save a random key
def generate_key():
    key = secrets.randbits(32)  # Generate a 32-bit random key
    with open("stego_key.txt", "w") as key_file:
        key_file.write(str(key))
    return key

# Function to read the stored key
def read_key():
    with open("stego_key.txt", "r") as key_file:
        return int(key_file.read())

# Function to embed text into an image using random pixel selection
def embed_text_random(image_path, text_file, output_path):
    image = cv2.imread(image_path)
    with open(text_file, "r") as file:
        message = file.read()

    message += "#####"  # Append a delimiter to mark the end of the message
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    
    key = generate_key()  # Generate and save a random key
    np.random.seed(key)  # Seed random generator with key
    pixel_indices = np.random.choice(image.size // 3, len(binary_message), replace=False)

    data_index = 0
    for i in pixel_indices:
        row = i // image.shape[1]
        col = i % image.shape[1]
        channel = data_index % 3  # Distribute across RGB channels
        image[row, col, channel] = (image[row, col, channel] & 254) | int(binary_message[data_index])
        data_index += 1
    
    cv2.imwrite(output_path, image)
    print(f"Message embedded. Key saved in 'stego_key.txt'.")

def extract_text_random(image_path, output_text_file):
    image = cv2.imread(image_path)
    key = read_key()  # Read stored key
    np.random.seed(key)  # Seed random generator with key
    
    binary_message = ""
    pixel_indices = np.random.choice(image.size // 3, image.size // 3, replace=False)

    for i in pixel_indices:
        row = i // image.shape[1]
        col = i % image.shape[1]
        channel = len(binary_message) % 3
        binary_message += str(image[row, col, channel] & 1)
        
        if len(binary_message) % 8 == 0:
            char = chr(int(binary_message[-8:], 2))
            if binary_message.endswith("00100011001000010010000100100001"):  # '#####' in binary
                break

    message = "".join(chr(int(binary_message[i:i+8], 2)) for i in range(0, len(binary_message), 8))
    message = message.replace("#####", "")


    with open(output_text_file, "w", encoding="utf-8") as file:
        file.write(message)
    
    print(f"Extracted message saved as {output_text_file}")



      ### LEVEL 3 IMPLEMENTATION OF IMAGE IN TEXT ###


# Compute PSNR
def compute_psnr(original, stego):
    mse = np.mean((original - stego) ** 2)
    if mse == 0:
        return float('inf')  # No difference
    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))
    return psnr

# Compute SSIM
def compute_ssim(original, stego):
    ssim_value = ssim(original, stego, data_range=stego.max() - stego.min(), multichannel=True)
    return ssim_value

# Compute Hamming Distance
def compute_hamming_distance(original, stego):
    original_bits = np.unpackbits(original.flatten())
    stego_bits = np.unpackbits(stego.flatten())
    return np.sum(original_bits != stego_bits)

# Evaluate steganography
def evaluate_steganography(original_image, stego_image):
    original = cv2.imread(original_image)
    stego = cv2.imread(stego_image)

    gray_original = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
    gray_stego = cv2.cvtColor(stego, cv2.COLOR_BGR2GRAY)

    psnr_value = compute_psnr(original, stego)
    ssim_value = compute_ssim(gray_original, gray_stego)
    hamming_value = compute_hamming_distance(original, stego)

    print(f"PSNR: {psnr_value:.2f} dB")
    print(f"SSIM: {ssim_value:.4f}")
    print(f"Hamming Distance: {hamming_value}")

# File paths
original_image = "butter.jpg"
text_file = "abc.txt"
decoded_text_file = "decoded_abc.txt"
stego_image = "static/outputs/encoded_butter.png"

# Embed and evaluate
embed_text_LSB(original_image, text_file, stego_image)

extract_text_LSB(stego_image, decoded_text_file)
print("for the LSB technique using rgb least bit manipulation method, the performance metrics are:")
evaluate_steganography(original_image, stego_image)

embed_text_random(original_image, text_file, stego_image)
extract_text_random(stego_image, decoded_text_file)

print("for the LSB technique using rgb random bit manipulation method, the performance metrics are:")
evaluate_steganography(original_image, stego_image)



