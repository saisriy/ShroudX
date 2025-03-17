import os
import numpy as np
import matplotlib.pyplot as plt
import cv2

def Read_image(image_path):
    image = cv2.imread(image_path)
    print(f"DEBUG: Read_image({image_path}) -> {type(image)}")
    return image  # Returns a NumPy array

def Write_image(image_path,image):
    directory = os.path.dirname(image_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    cv2.imwrite(image_path,image)

def Show_image(image,title) :
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title(title)
    plt.show()


def resize_image(image_path, output_path, width, height) :
    image = Read_image(image_path)
    resized_image = cv2.resize(image, (width, height))
    Write_image(output_path, resized_image)
    print(f"Resized image saved to {output_path}")

def image_to_binary_3D(image):
    binary_image = np.vectorize(lambda x: format(x, '08b'))(image)
    return binary_image

def each_bit(binary_image,index,height,width,color) :
    matrix =[]
    for i in range(height) :
      Line = []
      for j in range(width) :
        cell = []
        for k in range(color) :
          cell.append(binary_image[i][j][k][index])
        Line.append(cell)
      matrix.append(Line)
    return matrix

def Divider(binary_matrix) :
    matrix = []
    height, width, color = binary_matrix.shape

    for i in range(8) :
      matrix.append(each_bit(binary_matrix,i,height,width,color))
    return matrix

def Combiner(index_1,index_2,Matrix,binary_matrix) :
    matrix = []
    height, width, color = binary_matrix.shape

    for i in range(height):
      Line = []
      for j in range(width) :
        cell = []
        for k in range(color) :
          unit = ''
          for l in range(index_1,index_2+1) :
            unit += Matrix[l][i][j][k]
          for x in range(7-index_2+index_1) :
            unit += '0'

          cell.append(unit)
        Line.append(cell)
      matrix.append(Line)
    return matrix

def binary_to_int(binary_string) :
  return int(binary_string, 2)

def making_to_int(binary_matrix) :
    height,width,color = binary_matrix.shape
    number_matrix = []
    for i in range(height) :
       Line = []
       for j in range(width) :
          cell = []
          for k in range(color) :
            unit = binary_to_int(binary_matrix[i][j][k])
            cell.append(unit)
          Line.append(cell)
       number_matrix.append(Line)

    return number_matrix

def ENcode_lsb(cover_path, secret_path_1,secret_path_2, output_path) :

    cover = Read_image(cover_path)
    height, width = secret_path_1.shape[:2]
    cover_height, cover_width = cover.shape[:2]

    if height > cover_height or width > cover_width/2 :
        raise ValueError("stego capacity maximum level reached. Resize it or use a smaller secret.")

    cover_masked = cover.copy()
    cover_masked[0:height, 0:2*width] = cover_masked[0:height, 0:2*width] & 0b11111000


    secret_masked_1 = (secret_path_1 >> 5).astype(np.uint8)

    secret_masked_2 = (secret_path_2 >> 5).astype(np.uint8)

    for i in range(height) :
        for j in range(width) :
                cover_masked[i, 2*j] |= secret_masked_1[i, j]

                cover_masked[i, 2*j+1] |= secret_masked_2[i, j]



    Write_image(output_path, cover_masked)

    print(f"Stego image saved as {output_path}")

    # return height,width
        # os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # # Save the stego image
    # success = cv2.imwrite(output_path, cover_masked)
    # if not success:
    #     raise RuntimeError(f"Failed to save stego image at {output_path}")
    
    # print(f"DEBUG: Stego image successfully saved at {output_path}")
    return cover_masked.shape


def DEcode_lsb(stego_path, output_path, secret_size) :

    stego = Read_image(stego_path)
    height, width = secret_size

    secret_1 = np.zeros((height, width, 3), dtype=np.uint8)
    secret_2 = np.zeros((height, width, 3), dtype=np.uint8)

    for i in range(height) :
        for j in range(2*width) :
            if  j % 2 == 0:
                k = int(j/2)
                secret_1[i, k] = (stego[i, j] & 0b00000111) << 5
            else:
                k = int((j-1)/2)
                secret_2[i, k] = (stego[i, j] & 0b00000111) << 2

    return reconstruct(secret_1,secret_2,output_path)


def reconstruct(secret_image_1, secret_image_2, output_path) :
    height_1, width_1 = secret_image_1.shape[:2]
    height_2, width_2 = secret_image_2.shape[:2]

    if height_1 != height_2 or width_1 != width_2:
        raise ValueError("Secret images must have the same dimensions. Error Occured in the process")

    recombined_image = np.zeros_like(secret_image_1)

    for i in range(height_1) :
        for j in range(width_1) :
                recombined_image[i, j] = secret_image_1[i, j] + secret_image_2[i, j]

    Write_image(output_path, recombined_image)
    print(f"Reconstructed image saved as {output_path}")

def start_Encode(cover_path, secret_image, stego_path):
    print(f"DEBUG: Cover Image Path -> {cover_path}")
    print(f"DEBUG: Stego Image Path -> {stego_path}")

    try:
        # Ensure the cover image exists
        if not os.path.exists(cover_path):
            raise FileNotFoundError(f"Cover image not found: {cover_path}")

        # Read the cover image
        cover_image = Read_image(cover_path)
        if cover_image is None or not isinstance(cover_image, np.ndarray):
            raise ValueError("Failed to read cover image!")

        # Ensure secret_image is valid
        if secret_image is None or not isinstance(secret_image, np.ndarray):
            raise ValueError("Invalid secret image!")

        print(f"DEBUG: Cover image shape: {cover_image.shape}, Type: {cover_image.dtype}")
        print(f"DEBUG: Secret image shape: {secret_image.shape}, Type: {secret_image.dtype}")

        # Convert secret image to binary
        Binary_secret = image_to_binary_3D(secret_image)
        Bitted_secret = Divider(Binary_secret)

        # Process secret image bits
        Secret_1 = Combiner(0, 2, Bitted_secret, Binary_secret)
        Secret_2 = Combiner(3, 5, Bitted_secret, Binary_secret)

        # Convert to NumPy arrays
        Secret_1 = np.array(Secret_1)
        Secret_2 = np.array(Secret_2)

        # Convert binary to integer format
        change_11 = making_to_int(Secret_1)
        change_22 = making_to_int(Secret_2)

        change_11 = np.array(change_11)
        change_22 = np.array(change_22)

        # Ensure outputs directory exists
        stego_dir = os.path.dirname(stego_path)
        os.makedirs(stego_dir, exist_ok=True)

        # Perform LSB encoding and save stego image
        code = ENcode_lsb(cover_path, change_11, change_22, stego_path)

        # Ensure stego image was actually saved
        if not os.path.exists(stego_path):
            raise FileNotFoundError(f"Failed to create stego image at: {stego_path}")

        print(f"DEBUG: Stego image successfully created at {stego_path}")
        return code

    except Exception as e:
        print(f"ERROR in start_Encode: {str(e)}")
        return None
