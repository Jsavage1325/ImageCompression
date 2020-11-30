import time

from bitarray._bitarray import bitarray
from matplotlib import image
import numpy as np
import bitarray as ba
import pandas as pd
from numpy import genfromtxt
from numpy import savetxt
from matplotlib import pyplot as plt
# load image as pixel array (numpy array


# we will ues this to get the frequency of all the pixels in an image
def get_sorted_frequency_list(image):
    # find the most commonly occuring values
    (values, counts) = np.unique(image, return_counts=True)

    # the below loop prints the count of each pixel
    # for v in range(len(values)):
    #     print(str(values[v]) + " has a count of " + str(counts[v]))

    # create a numpy array with the values and counts
    value_counts = np.c_[counts, values]
    # sort our value counts by count
    value_counts.sort(axis=0)

    # now we are arranging our counts
    positioned_values = []
    stored_already = []
    for v in value_counts:
        # get the index of the ordered value in counts
        result = np.where(counts == v[0])
        if len(result[0]) == 2:
            result_0 = result[0][0]
            result_1 = result[0][1]
            stored = False
            for s in stored_already:
                if s == result_1:
                    stored = True
            if not stored:
                stored_already.append(result_0)
                stored_already.append(result_1)
                positioned_values.append(int(values[result_0]))
                positioned_values.append(int(values[result_1]))
        else:
            result = str(result[0])[1:-1]
            result = int(result)
            # insert so that the most common values are at top
            positioned_values.insert(0, int(values[result]))

    # convert this to a numpy array
    pos_values = np.asarray(positioned_values, dtype=object)

    # returned as values from high to low
    return pos_values


# we need to split our rgb values as we will be constructing different trees for each of them
def split_rgb(image):
    x,y,c = image.shape
    red = np.empty((x, y))
    green = np.empty((x, y))
    blue = np.empty((x, y))
    for a in range(x):
        for b in range(y):
            red[a, b] = image[a, b, 0]
            green[a, b] = image[a, b, 1]
            blue[a, b] = image[a, b, 2]

    return red, green, blue


# this function creates a unique dictionary for each array
def create_dictionary(arr):
    # read csv into array of some sort
    codes = open("unique_codes.txt", "r")
    lines = codes.readlines()
    codes = []
    dict = {}
    for l in lines:
        codes.append(l.split("\n")[0])
    for i in range(len(arr)):
        dict[arr[i]] = codes[i]
    return dict


def encode(x, y, arr, order):
    dict = create_dictionary(order)
    # grab the indexes of each value and make them an array
    encoded = ""
    for i in range(x):
        for j in range(y):
            encoded += dict[int(arr[i][j])]
    # now we have all of our indexes, we loop through and create a string with all the 0's and 1's
    return encoded


def to_binary(num):
    binary = str(bin(x))[2:]
    return binary


def compress_save(x, y, red, green, blue, order_red, order_green, order_blue):
    # will be stored in the format x y red_dict encoded_red green_dict encoded green blue_dict encoded_blue
    # convert x and y to binary
    # binx = to_binary(x)
    # biny = to_binary(y)
    # we will attempt to write non binary numbers to file and see if this affects the size
    # ToDo make this save as a binary file rather than the current file type
    # Need to ensure they are not being saved as strings etc
    # current file size = 233mb (ouch)
    # encode all of the bit arrays
    red_encode = encode(x, y, red, order_red)
    green_encode = encode(x, y, green, order_green)
    blue_encode = encode(x, y, blue, order_blue)

    newFileByteArray = bytearray(x, y, order_red, red_encode, order_green,
                                 green_encode, order_blue, blue_encode)
    newfile = open("encoded_image", 'wb')
    newfile.write((''.join(chr(i) for i in newFileByteArray)).encode('charmap'))



if __name__ == "__main__":
    image = image.imread("./Images/IC1.bmp")
    x,y,c = image.shape
    # print(x)
    # print(to_binary(x))
    # print(y)
    # print(to_binary(y))
    red, green, blue = split_rgb(image)
    sorted_red = get_sorted_frequency_list(red)
    # red_dictionary = create_dictionary(sorted_red)
    sorted_green = get_sorted_frequency_list(green)
    # green_dictionary = create_dictionary(sorted_green)
    sorted_blue = get_sorted_frequency_list(blue)
    # blue_dictionary = create_dictionary(sorted_blue)
    compress_save(x, y, red, green, blue, sorted_red, sorted_green, sorted_blue)

