import re
import random

def text_to_binary(text):
    return ''.join(format(ord(char), '08b') for char in text)

def binary_to_text(binary):
    # Make sure binary length is a multiple of 8
    if len(binary) % 8 != 0:
        binary = binary[:-(len(binary) % 8)]  # Trim extra bits
    
    chars = [binary[i:i+8] for i in range(0, len(binary), 8)]
    return ''.join(chr(int(char, 2)) for char in chars if len(char) == 8)

def encode_message(cover_text, secret_message):
    
    # Define 16 different modifications for 4-bit patterns
    modifications = {
        '0000': '',           # No modification
        '0001': '.',
        '0010': ',',
        '0011': ';',
        '0100': ':',
        '0101': '!',
        '0110': '?',
        '0111': '-',
        '1000': '()',        # Empty parentheses
        '1001': "'",          # Single quote
        '1010': '"',          # Double quote
        '1011': '...',        # Ellipsis
        '1100': '&',         # Ampersand
        '1101': '*',         # Asterisk
        '1110': '_',         # Underscore
        '1111': '+'          # Plus sign
    }
    
    words = cover_text.split()
    max_capacity_bits = len(words) * 4
    max_capacity_chars = max_capacity_bits // 8

    binary_message = text_to_binary(secret_message)
    print(f"Binary message: {binary_message}, Length: {len(binary_message)}")
    original_length_bits = len(binary_message)

    if original_length_bits > max_capacity_bits:
        print(f"⚠️ Cover can hold only {max_capacity_chars} characters.")
        binary_message = binary_message[:max_capacity_bits]

    # Check if we have enough words
    if len(binary_message) > len(words) * 4:
        raise ValueError("Cover text is too short to hide the secret message!")
    
    stego_words = []
    binary_index = 0
    
    for word in words:
        # If we've encoded the entire message, add remaining words unchanged
        if binary_index >= len(binary_message):
            stego_words.append(word)
            continue
            
        # Get next 4 bits to encode (or whatever is left)
        bits_remaining = len(binary_message) - binary_index
        if bits_remaining >= 4:
            current_bits = binary_message[binary_index:binary_index+4]
            binary_index += 4
        else:
            # Pad with zeros if less than 4 bits remain
            current_bits = binary_message[binary_index:].ljust(4, '0')
            binary_index = len(binary_message)
        
        # Encode based on 4-bit pattern
        stego_words.append(word + modifications[current_bits])

    encoded_text = ' '.join(stego_words)
    chars_encoded = len(binary_message) // 8
    chars_remaining = max_capacity_chars - chars_encoded
    
    print(f"Encoded {chars_encoded} characters into cover text.")
    print(f"Remaining space: {chars_remaining} characters.")

    return encoded_text, binary_message

def extract_message(stego_text, cover_text, expected_length=None):
    stego_words = stego_text.split()
    cover_words = cover_text.split()
    
    # Create reverse mapping
    modifications = {
        '': '0000',           # No modification
        '.': '0001',
        ',': '0010',
        ';': '0011',
        ':': '0100',
        '!': '0101',
        '?': '0110',
        '-': '0111',
        '()': '1000',        # Empty parentheses
        "'": '1001',          # Single quote
        '"': '1010',          # Double quote
        '...': '1011',        # Ellipsis
        '&': '1100',         # Ampersand
        '*': '1101',         # Asterisk
        '_': '1110',         # Underscore
        '+': '1111'          # Plus sign
    }
    
    reverse_mods = {v: k for k, v in modifications.items()}

    stego_words = stego_text.split()
    cover_words = cover_text.split()

    binary_message = ''

    # Go word-by-word, matching suffixes
    for i in range(min(len(stego_words), len(cover_words))):
        if expected_length and len(binary_message) >= expected_length:
            break

        cover_word = cover_words[i]
        stego_word = stego_words[i]

        suffix = stego_word[len(cover_word):]

        # Important: match exact suffixes from dictionary
        if suffix in modifications:
            binary_message += modifications[suffix]
        # else:
        #     binary_message += '0000'

    if expected_length:
        binary_message = binary_message[:expected_length]

    # Make sure to truncate to full bytes
    binary_message = binary_message[:(len(binary_message) // 8) * 8]
    return binary_to_text(binary_message), binary_message


# def extract_message(stego_text, cover_text):
#     stego_words = stego_text.split()
#     cover_words = cover_text.split()
    
#     binary_message = ''
    
#     for i in range(min(len(stego_words), len(cover_words))):
#         # Extract based on punctuation
#         if stego_words[i] == cover_words[i]:
#             binary_message += '00'
#         elif stego_words[i] == cover_words[i] + '.':
#             binary_message += '01'
#         elif stego_words[i] == cover_words[i] + ',':
#             binary_message += '10'
#         elif stego_words[i] == cover_words[i] + '!':
#             binary_message += '11'
#         elif stego_words[i].endswith(('.', ',', ';', ':', '!', '?')):
#             # Fallback for old encoding
#             binary_message += '1'
#         else:
#             binary_message += '0'
    
#     # Only process complete bytes
#     complete_bytes = len(binary_message) - (len(binary_message) % 8)
#     if complete_bytes > 0:
#         extracted_text = binary_to_text(binary_message[:complete_bytes])
#         return extracted_text, binary_message[:complete_bytes]
#     else:
#         return "", ""

# Example usage
cover = "he internet, once a futuristic dream, is now an essential part of daily life, influencing communication, commerce, and culture.he internet, once a futuristic dream, is now an essential part of daily life, influencing communication, commerce, and culture.he internet, once a futuristic dream, is now an essential part of daily life, influencing communication, commerce, and culture.he internet, once a futuristic dream, is now an essential part of daily life, influencing communication, commerce, and culture.he internet, once a futuristic dream, is now an essential part of daily life, influencing communication, commerce, and culture.he internet, once a futuristic dream, is now an essential part of daily life, influencing communication, commerce, and culture.he internet, once a futuristic dream, is now an essential part of daily life, influencing communication, commerce, and culture.he internet, once a futuristic dream, is now an essential part of daily life, influencing communication, commerce, and culture.he internet, once a futuristic dream, is now an essential part of daily life, influencing communication, commerce, and culture.he internet, once a futuristic dream, is now an essential part of daily life, influencing communication, commerce, and culture.he internet, once a futuristic dream, is now an essential part of daily life, influencing communication, commerce, and culture.he internet, once a futuristic dream, is now an essential part of daily life, influencing communication, commerce, and culture.he internet, once a futuristic dream, is now an essential part of daily life, influencing communication, commerce, and culture.Hello world this is a secret message hidden in syntax. Hello world this is a secret message hidden in syntax.Hello world this is a secret message hidden in syntax. Hello world this is a secret message hidden in syntax.Hello world this is a secret message hidden in syntax. Hello world this is a secret message hidden in syntax.Hello world this is a secret message hidden in syntax. Hello world this is a secret message hidden in syntax.Hello world this is a secret message hidden in syntax. Hello world this is a secret message hidden in syntax.Hello world this is a secret message hidden in syntax. Hello world this is a secret message hidden in syntax.Hello world this is a secret message hidden in syntax. Hello world this is a secret message hidden in syntax.Hello world this is a secret message hidden in syntax. Hello world this is a secret message hidden in syntax.Hello world this is a secret message hidden in syntax. Hello world this is a secret message hidden in syntax.Hello world this is a secret message hidden in syntax. Hello world this is a secret message hidden in syntax."
secret = "The internet, once a futuristic dream, is now an essential part of daily life, influencing communication, commerce, and culture. The internet, once a futuristic dream, is now an essential part of daily life, influencing communication, commerce, and culture."


stego_text, binary_encoded = encode_message(cover, secret)
print("Stego Text:", stego_text)

decoded_text, binary_decoded = extract_message(stego_text, cover)
print("Extracted Binary:", binary_decoded)
print("Decoded Message:", decoded_text)