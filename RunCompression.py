import os
import LossyMethods as LM
import HuffmanCoding as HC
import numpy as np


def do_all_compression(image_path, svd_radius, fft_keep):
    cur_dir = os.getcwd()
    """Making output folders of the compressed and decompressed images if not in the directory"""
    out_dir = os.path.join(cur_dir, "compressed_images")
    if (os.path.isdir(out_dir) == False):
        os.mkdir(out_dir)
    out_dir = os.path.join(cur_dir, "decompressed_images")
    if (os.path.isdir(out_dir) == False):
        os.mkdir(out_dir)
    GUI_output = ""
    # image_path = "images/IC5.bmp"
    image_name = image_path.split("/")[-1].split(".")[0]
    # Load the original image
    image = LM.load_image(image_path)
    """Checking the image is grayscale or rgb"""
    # if len is 2 then no rgb component
    if len(image.shape) == 2:
        print("Original Image")
        LM.display_image(image, "Grayscale", "Original Image")
        # Lossy Compression
        """Singular value compression on grayscale image with radius passed to func"""
        com_svd = LM.svd_compression_gray(image, int(svd_radius))
        print("SVD compressed image")
        LM.display_image(com_svd, "Grayscale", "SVD Compressed Image")
        out_path_svd = LM.save_image(com_svd, "compressed_images/" + image_name + "_svd_compressed")

        """Fourier Transform compression on grayscale image with keep percentage passed to func"""
        com_fft = LM.fft_compression_gray(image, float(fft_keep))
        print("Fourier Transform compressed image")
        LM.display_image(com_fft, "Grayscale", "Fourier Compressed Image")
        out_path_fft = LM.save_image(com_fft, "compressed_images/" + image_name + "_fft_compressed")
    else:
        LM.display_image(image, "RGB", "Original Image")
        # Lossy Compression
        """Singular value compression on RGB image with radius 100"""
        com_svd = LM.svd_compression_rgb(image, int(svd_radius))
        print("SVD compressed image")
        LM.display_image(com_svd, "RGB", "SVD compressed image")
        out_path_svd = LM.save_image(com_svd, "compressed_images/" + image_name + "_svd_compressed")

        """Fourier Transform compression on RGB image with keep percentage 0.1"""
        com_fft = LM.fft_compression_rgb(image, float(fft_keep))
        print("Fourier Transform compressed image")
        LM.display_image(com_fft, "RGB", "FFT compressed image")
        out_path_fft = LM.save_image(com_fft, "compressed_images/" + image_name + "_fft_compressed")

    """Lossless Compression"""
    """Huffman Encoding of the image"""
    # Huffman output name
    out_name = "compressed_" + image_name + ".bin"
    decompressed_name = "decompressed_" + image_name + ".bmp"
    out_name = "./compressed_images/" + out_name
    decompressed_name = "./decompressed_images/" + decompressed_name
    # compress to binary file
    HC.compress_image(image_path, out_name)
    # decompress to image
    HC.decompress_image(out_name, decompressed_name)

    decom_image = LM.load_image(decompressed_name)

    if len(image.shape) == 2:
        print("Huffman Decompressed Image")
        LM.display_image(decom_image, "Grayscale", "Huffman Decompressed Image")
    else:
        print("Huffman Decompressed Image")
        LM.display_image(decom_image, "RGB", "Huffman Decompressed Image")

    """Displaying all the compression rates from the both lossy and lossless compression"""
    GUI_output += "SVD Compression Rate: " + str(round(LM.CompressionRate(image_path, out_path_svd), 4)) + "\n"
    Y = np.square(np.subtract(image, com_svd)).mean()
    GUI_output += "MSE of Original and SVD compressed image: " + str(round(Y)) + "\n"
    GUI_output += "Fourier Transform Compression Rate: " + str(round(LM.CompressionRate(image_path, out_path_fft), 4)) + "\n"
    Y = np.square(np.subtract(image, com_fft)).mean()
    GUI_output += "MSE of Original and FFT compressed image: " + str(round(Y)) + "\n"
    GUI_output += "Huffman Coding Compression Rate: " + str(round(LM.CompressionRate(image_path, decompressed_name), 4)) + "\n"
    Y = np.square(np.subtract(image, decom_image)).mean()
    GUI_output += "MSE of Original and Huffman Decompressed image:" + str(round(Y)) + "\n"

    return GUI_output
