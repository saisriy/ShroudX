import nltk
from nltk.corpus import wordnet
import random
import re
import base64

class SimpleSemanticSteganography:
    def __init__(self):
        # Map NLTK POS tags to WordNet POS tags
        self.pos_map = {
            'NN': 'n', 'NNS': 'n', 'NNP': 'n', 'NNPS': 'n',  # Nouns
            'JJ': 'a', 'JJR': 'a', 'JJS': 'a',  # Adjectives
            'RB': 'r', 'RBR': 'r', 'RBS': 'r',  # Adverbs
            'VB': 'v', 'VBD': 'v', 'VBG': 'v', 'VBN': 'v', 'VBP': 'v', 'VBZ': 'v'  # Verbs
        }
    
    def text_to_binary(self, text):
        """Convert text to binary string."""
        return ''.join(format(ord(char), '08b') for char in text)
    
    def binary_to_text(self, binary):
        """Convert binary string to text."""
        text = ""
        for i in range(0, len(binary), 8):
            if i + 8 <= len(binary):
                byte = binary[i:i+8]
                text += chr(int(byte, 2))
        return text
    
    def get_synonyms(self, word, pos):
        """Get synonyms for a word based on its part of speech."""
        if pos not in self.pos_map:
            return []
        
        wn_pos = self.pos_map[pos]
        synsets = wordnet.synsets(word, pos=wn_pos)
        synonyms = []
        
        for synset in synsets:
            for lemma in synset.lemmas():
                synonym = lemma.name().replace('_', ' ')
                if synonym.lower() != word.lower() and synonym not in synonyms:
                    synonyms.append(synonym)
        
        return synonyms
    
    def hide_message(self, cover_file, secret_file):
        """Hide a message in text using synonym substitution."""
        with open(cover_file, "r", encoding="utf-8") as file:
            cover_text = file.read()

        with open(secret_file, "r", encoding="utf-8") as file:
            secret_message = file.read()

        binary_message = self.text_to_binary(secret_message)
        print(f"Binary message: {binary_message} ({len(binary_message)} bits)")
        
        # Tokenize and tag the cover text
        tokens = nltk.word_tokenize(cover_text)
        tagged = nltk.pos_tag(tokens)
        
        # Find all words that have synonyms
        usable_words = []
        for i, (word, pos) in enumerate(tagged):
            synonyms = self.get_synonyms(word, pos)
            if synonyms:
                usable_words.append((i, word, synonyms))
        
        print(f"Found {len(usable_words)} usable words in the cover text")
        if len(usable_words) < len(binary_message):
            print(f"Not enough usable words to encode the entire message ({len(binary_message)} bits). Please give more cover text.")
            print(f"Will only encode the first {len(usable_words)} bits")
            exit(1)
        
        # Encode the message
        result = tokens.copy()
        bit_count = min(len(binary_message), len(usable_words))
        
        # Create a dictionary to track which positions were modified
        modifications = {}
        
        for i in range(bit_count):
            pos_idx, original_word, synonyms = usable_words[i]
            bit = binary_message[i]
            
            if bit == '1':
                # Choose a random synonym for bit 1
                new_word = random.choice(synonyms)
                result[pos_idx] = new_word
                modifications[pos_idx] = (original_word, new_word, '1')
            else:
                # Keep the original word for bit 0
                modifications[pos_idx] = (original_word, original_word, '0')
        
        # Reconstruct the text with proper spacing
        stego_text = ""
        for i, token in enumerate(result):
            if i > 0 and token not in ".,!?;:)]}'" and result[i-1] not in "([{":
                stego_text += " "
            stego_text += token
        
        # Create a key file for extraction
        key = []
        for i in range(len(tokens)):
            if i in modifications:
                key.append(modifications[i][2])  # Add the bit
            else:
                key.append('x')  # Mark as not used
        
        return stego_text, ''.join(key)
    
    def extract_message(self, stego_text, key):
        """Extract the message using the key."""
        # Extract the bits
        binary = ''.join([bit for bit in key if bit != 'x'])
        
        # Convert to text
        message = self.binary_to_text(binary)
        return message
    
stego = SimpleSemanticSteganography()
stego_text, key = stego.hide_message("/Users/pradeepikanori/Desktop/stego_file.txt", "/Users/pradeepikanori/Desktop/secret_text.txt")

print("\n--- ENCODING ---")
    # print(f"Secret message: {secret_message}")
    
    
print("\nOriginal text:")
    # print(cover_text)
    
print("\nStego text:")
print(stego_text)
    
print("\nKey (for extraction):")
print(key)
    
print("\n--- DECODING ---")
extracted = stego.extract_message(stego_text, key)
print(f"Extracted message: {extracted}")
    
    