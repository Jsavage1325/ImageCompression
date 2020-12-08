import os
import cv2
import numpy as np
from matplotlib import pyplot as plt
from skimage.measure import compare_ssim
import HuffmanCoding as HC
import imageio
import PySimpleGUI as sg


def load_image(path):
    """ Load image from path. Return a numpy array """
    input_image = imageio.imread(path)
    return input_image


def display_image(image, image_type, title):
    """Display image"""
    img = plt.imshow(image)
    if image_type == "Grayscale":
        img.set_cmap('gray')
    plt.axis('off')
    plt.title(title)
    plt.show()


def save_image(image, name):
    """Save image to the desired path"""
    compressed_image = image
    cv2.imwrite(str(name) + ".png", compressed_image)
    return str(name) + ".png"


def CompressionRate(sourceFile, compressedFile):
    """Calculates the compression rate of the Original file and Compressed File"""
    source_size = os.path.getsize(sourceFile)
    compressed_size = os.path.getsize(compressedFile)
    compression_rate = (source_size + 0.0) / (compressed_size + 0.0)
    print("Source_size: " + str(source_size))
    print("Compressed_size: " + str(compressed_size))
    return compression_rate


def svd_compression_rgb(img, k):
    """Takes image array and radius and returns the SVD compressed image"""
    """Firstly seprates all the r,g,and b colour array and seperately construct approx image for each colour.
        Then combines each value and obtain combine compressed image"""
    r = img[:, :, 0]
    g = img[:, :, 1]
    b = img[:, :, 2]

    ur, sr, vr = np.linalg.svd(r, full_matrices=False)
    sr = np.diag(sr)
    ug, sg, vg = np.linalg.svd(g, full_matrices=False)
    sg = np.diag(sg)
    ub, sb, vb = np.linalg.svd(b, full_matrices=False)
    sb = np.diag(sb)
    rr = ur[:, :k] @ sr[0:k, :k] @ vr[:k, :]
    rg = ug[:, :k] @ sg[0:k, :k] @ vg[:k, :]
    rb = ub[:, :k] @ sb[0:k, :k] @ vb[:k, :]

    rimg = np.zeros(img.shape)
    rimg[:, :, 0] = rr
    rimg[:, :, 1] = rg
    rimg[:, :, 2] = rb

    for ind1, row in enumerate(rimg):
        for ind2, col in enumerate(row):
            for ind3, value in enumerate(col):
                if value < 0:
                    rimg[ind1, ind2, ind3] = abs(value)
                if value > 255:
                    rimg[ind1, ind2, ind3] = 255

    compressed_image = rimg.astype(np.uint8)

    return compressed_image


def svd_compression_gray(image, k):
    # Construct approximate image
    U, S, VT = np.linalg.svd(image, full_matrices=False)
    S = np.diag(S)
    Xapprox = U[:, :k] @ S[0:k, :k] @ VT[:k, :]
    return Xapprox


def fft_compression_rgb(image, keep):
    """Takes image array and keep ratio and returns the fourier transformed compressed image"""

    """Firstly seprates all the r,g,and b colour array and seperately applies forward fourier transformation
        the sort by magnitude and then find small indices in each and keep threshold small indices
        and applies inverse fourier transformation to get compressed r,g and b values. Then combines each
        value and obtain combine compressed image"""
    r = image[:, :, 0]
    g = image[:, :, 1]
    b = image[:, :, 2]
    Br = np.fft.fft2(r)
    Bg = np.fft.fft2(g)
    Bb = np.fft.fft2(b)

    Brsort = np.sort(np.abs(Br.reshape(-1)))  # sort by magnitude
    Bgsort = np.sort(np.abs(Bg.reshape(-1)))  # sort by magnitude
    Bbsort = np.sort(np.abs(Bb.reshape(-1)))  # sort by magnitude

    threshr = Brsort[int(np.floor((1 - keep) * len(Brsort)))]
    indr = np.abs(Br) > threshr  # Find small indices
    Atlowr = Br * indr  # Threshold small indices
    Alowr = np.fft.ifft2(Atlowr).real  # Compressed image

    threshg = Bgsort[int(np.floor((1 - keep) * len(Bgsort)))]
    indg = np.abs(Bg) > threshg  # Find small indices
    Atlowg = Bg * indg  # Threshold small indices
    Alowg = np.fft.ifft2(Atlowg).real  # Compressed image

    threshb = Bbsort[int(np.floor((1 - keep) * len(Bbsort)))]
    indb = np.abs(Bb) > threshb  # Find small indices
    Atlowb = Bb * indb  # Threshold small indices
    Alowb = np.fft.ifft2(Atlowb).real  # Compressed image

    rimg = np.zeros(image.shape)
    rimg[:, :, 0] = Alowr
    rimg[:, :, 1] = Alowg
    rimg[:, :, 2] = Alowb

    for ind1, row in enumerate(rimg):
        for ind2, col in enumerate(row):
            for ind3, value in enumerate(col):
                if value < 0:
                    rimg[ind1, ind2, ind3] = abs(value)
                if value > 255:
                    rimg[ind1, ind2, ind3] = 255

    compressed_image = rimg.astype(np.uint8)

    return compressed_image


def fft_compression_gray(image, keep):
    Bt = np.fft.fft2(image)  # Forward Fourier transformation
    Btsort = np.sort(np.abs(Bt.reshape(-1)))  # sort by magnitude
    # Zero out all small coefficients and inverse transform
    thresh = Btsort[int(np.floor((1 - keep) * len(Btsort)))]
    ind = np.abs(Bt) > thresh  # Find small indices
    Atlow = Bt * ind  # Threshold small indices
    Alow = np.fft.ifft2(Atlow).real  # Compressed image

    return Alow




