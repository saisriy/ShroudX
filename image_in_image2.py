# -*- coding: utf-8 -*-
"""Autolevelling_Img_in_Img.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1tRUWBkijEoIjme3yMQgUQP0C5yYY3H4f
"""

import numpy as np
import matplotlib.pyplot as plt
import cv2
import math

def Read_image(image_path) :
    image = cv2.imread(image_path)
    return image

def Write_image(image_path,image) :
    cv2.imwrite(image_path,image)

def Show_image(image,title) :
    plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    plt.title(title)
    plt.show()


def resize_image(image_path, output_path, width, height) :
    image = Read_image(image_path)
    resized_image = cv2.resize(image, (width, height))
    Write_image(output_path, resized_image)

'''
  Converts each value into 8-bit binary representation
'''
def image_to_binary_3D(image):
    image = np.nan_to_num(image, nan=0.0).astype(np.uint8) #V
    binary_image = np.vectorize(lambda x: format(x, '08b'))(image)
    return binary_image

'''
    Store corresponging index's value in a list
'''
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

from PIL import Image, ImageEnhance

def enhance_image(image_path, output_path, sharpness=2.5, contrast=1, brightness=1):
    # Open the image
    img = Image.open(image_path)

    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(sharpness)

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(contrast)

    # Enhance brightness
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(brightness)

    # Save the enhanced image
    img.save(output_path)

def Triggering_Level (cover_path,secret_path) :
    cover = Read_image(cover_path)
    secret = Read_image(secret_path)
    a,b = cover.shape[:2]
    c,d = secret.shape[:2]
    Level = (a * b) / (c * d)
    if Level * c*d == a * b :
        Level = int(Level)
    else :
        Level = int(Level) + 1

    if Level >= 8 :
        Level = 1
    elif Level < 8 and Level >= 4 :
        Level = 2
    elif Level < 4 and Level >= 2 :
        Level = 4
    else :
        Level = 8
    return Level

def Encode_im_im(cover_path, secret_paths,some, output_path,Level) :

    cover = Read_image(cover_path)
    numbers,height, width,color = secret_paths.shape[:4]
    cover_height, cover_width = cover.shape[:2]
    Masking_factor = (0xFF << (Level)) & 0xFF
    numbers = int(numbers/Level)

    cover_masked = cover.copy()

    e = 0
    f = 0
    for i in range(numbers * height * width) :
        cover_masked[e, f] = cover_masked[e, f] & Masking_factor
        f += 1
        if f == cover_width :
            f = 0
            e += 1


    secrets = []

    for i in range(numbers) :
        x = Combiner(Level*i,Level*(i+1) - 1,secret_paths,some)
        x = np.array(x)
        ix = making_to_int(x)
        ix = np.array(ix)
        sx = (ix >> (8-Level)).astype(np.uint8)
        secrets.append(sx)

    a = 0
    b = 0
    count = 0;
    for i in range(cover_height) :
        for j in range(cover_width) :
                if count >= numbers * height * width :
                    break
                d = count % numbers
                cover_masked[i,j] |= secrets[d][a,b]

                if d == numbers-1 :
                    b += 1
                count += 1

                if b == width :
                    b = 0
                    a = a+1


    Write_image(output_path, cover_masked)

    return [numbers,height,width,color]

def DECode_lsb(stego_path, output_path, secret_size,l,x) :

    stego = Read_image(stego_path)
    numbers,height,width,color = secret_size[:4]
    stego_height, stego_width = stego.shape[:2]

    Level = int(8/x)

    deMasking_factor = (0xFF >> (8-Level)) & 0xFF

    secrets = []
    for i in range(numbers) :
        secrets.append(np.zeros((height, width, 3), dtype=np.uint8))

    index = 0
    a = 0
    b = 0
    for i in range(stego_height) :
        for j in range(stego_width) :
            if a >= height :
                break
            s = index % numbers
            secrets[s][a,b] = (stego[i,j] & deMasking_factor) << (8 - Level*(s+1))


            if s == numbers-1 :
              b += 1

            index += 1

            if b == width :
                b = 0
                a = a+1

    Reconstruct_im_im(secrets,output_path)
    resize_image(output_path,output_path, int(width*math.sqrt(l*x/8)), int(height*math.sqrt(l*x/8)))
    enhance_image(output_path,output_path)


def Reconstruct_im_im(secret_Image_matrix, output_path) :
    height ,width = secret_Image_matrix[0].shape[:2]
    recombined_image = np.zeros_like(secret_Image_matrix[0])

    for i in range(height) :
        for j in range(width) :
                sum = 0
                for x in range(len(secret_Image_matrix)) :
                    sum += secret_Image_matrix[x][i,j]
                recombined_image[i, j] = sum
    Write_image(output_path, recombined_image)

def Level_encode(cover_image_path,secret_image_path,output_image_path,temp_path,x):
    cover_image = Read_image(cover_image_path)
    secret_image = Read_image(secret_image_path)
    Level = Triggering_Level(cover_image_path,secret_image_path)
    l = Level
    Level = int(8/x)
    resize_image(secret_image_path,temp_path, int(secret_image.shape[1]/math.sqrt(l*x/8)), int(secret_image.shape[0]/math.sqrt(l*x/8)))
    secret_image = Read_image(temp_path)
    Binary_Matrix = image_to_binary_3D(secret_image)
    Bitted_Matrix = Divider(Binary_Matrix)
    Bitted_Matrix = np.array(Bitted_Matrix)
    code = Encode_im_im(cover_image_path,Bitted_Matrix,Binary_Matrix,output_image_path,Level)
    return code,l

def calculate_psnr_im_im(img1_path, img2_path):
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    if img1.shape != img2.shape:
        resize_image(img1_path,img1_path, img2.shape[0], img2.shape[1])
        img1 = cv2.imread(img1_path)
    # Calculate MSE
    mse = np.mean((img1 - img2)**2)

    # Calculate PSNR
    if mse == 0:
        return float('inf')  # Handle case where images are identical
    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse))

    return psnr

def hamming_distance(image_path1, image_path2) :
  image1 = Read_image(image_path1)
  image2 = Read_image(image_path2)

  image_path3 = 'pemt.png'
  if image1.shape != image2.shape:
      resize_image(image_path1, image_path3, image2.shape[1], image2.shape[0]) #V width, height were reversed
      image3 = cv2.imread(image_path3)
  else:
      image3 = image1


  diff = image3 != image2
  distance = np.count_nonzero(diff)

  return distance

def Validating_image(cover_image_path,secret_image_path) :
    cover_image = Read_image(cover_image_path)
    secret_image = Read_image(secret_image_path)
    a,b,_ = cover_image.shape
    c,d,_ = secret_image.shape
    if a*b < c*d :
      print('Cover image is incomplatible to hold secret image')
      print('Hence, Resizing image...')
      resize_image(cover_image_path,cover_image_path,3*b,3*a)

def Start_Encode(cover_image_path,secret_image_path,output_image_path,temp_path='temp.png',random_path='random.png') :
    Validating_image(cover_image_path,secret_image_path)
    code2,l2 = Level_encode(cover_image_path,secret_image_path,'temp1.png','temp_path1.png',2)
    DECode_lsb('temp1.png','random1.png',code2,l2,2)
    ham2 = hamming_distance(secret_image_path,'random1.png')

    code4,l4 = Level_encode(cover_image_path,secret_image_path,'temp2.png','temp_path2.png',4)
    DECode_lsb('temp2.png','random2.png',code4,l4,4)
    ham4 = hamming_distance(secret_image_path,'random2.png')

    code8,l8 = Level_encode(cover_image_path,secret_image_path,'temp3.png','temp_path3.png',8)
    DECode_lsb('temp3.png','random3.png',code8,l8,8)
    ham8 = hamming_distance(secret_image_path,'random3.png')

    if ham2 < ham4 and ham2 < ham8 :
        code,l = Level_encode(cover_image_path,secret_image_path,output_image_path,temp_path,2)
        x = 2
    elif ham4 < ham2 and ham4 < ham8 :
        code,l = Level_encode(cover_image_path,secret_image_path,output_image_path,temp_path,4)
        x = 4
    else :
        code,l = Level_encode(cover_image_path,secret_image_path,output_image_path,temp_path,8)
        x = 8
    
    return code,l,x

