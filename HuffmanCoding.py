import time
from collections import Counter
from itertools import chain
from PIL import Image
from PIL import ImageChops
import InputBitStream
import OutputBitStream


# This function counts the number of values and returns them sorted array of pixels and count from low to high count
def count_symbols(image):
    all_pixels = image.getdata()
    rgb_values = chain.from_iterable(all_pixels)
    counts = Counter(rgb_values).items()
    return sorted(counts, key=lambda x: x[::-1])


# this builds a tree using the counts of each pixel value
def build_tree(counts):
    # reverse each entry so it is now (count, symbol)
    nodes = [entry[::-1] for entry in counts]
    # While the tree is not 1 node only
    while len(nodes) > 1:
        # take the "bottom" two nodes
        smallest_two = tuple(nodes[0:2])
        # this gets the rest of the tree
        tree = nodes[2:] # all the others
        # here we combine the frequency of the lowest frequency nodes
        new_freq = smallest_two[0][0] + smallest_two[1][0]
        # Create a new tree adding the combined two smallest at end
        nodes = tree + [(new_freq, smallest_two)]
        # sort the new frequency object into the right place
        nodes.sort()
    # Return the single tree inside the list
    return nodes[0]


# trims the tree and combines
def trim_tree(tree):
    # the main tree
    p = tree[1]
    # if Node, trim left then right and recombine
    if type(p) is tuple:
        return (trim_tree(p[0]), trim_tree(p[1]))
    # if not tuple then leaf, so return
    return p


# This is going to search the tree recusively
def assign_codes_implicit(codes, node, pat):
    # if it is a branch, recurse
    if type(node) == tuple:
        assign_codes_implicit(codes, node[0], pat + [0]) # Branch point. Do the left branch
        assign_codes_implicit(codes, node[1], pat + [1]) # then do the right branch.
    # if leaf then do not continue
    else:
        codes[node] = pat # A leaf. set its code


# This will create a dict of all the codes which we will be wanting to use to encode
def assign_codes(tree):
    codes = {}
    assign_codes_implicit(codes, tree, [])
    return codes


# Calculates the compressed size of the image (what it will be)
def compressed_size(counts, codes):
    header_size = 2 * 16 # height and width as 16 bit values

    tree_size = len(counts) * (1 + 8) # Leafs: 1 bit flag, 8 bit symbol each
    tree_size += len(counts) - 1 # Nodes: 1 bit flag each
    if tree_size % 8 > 0: # Padding to next full byte
        tree_size += 8 - (tree_size % 8)

    # Sum for each symbol of count * code length
    pixels_size = sum([count * len(codes[symbol]) for symbol, count in counts])
    if pixels_size % 8 > 0: # Padding to next full byte
        pixels_size += 8 - (pixels_size % 8)

    return (header_size + tree_size + pixels_size) / 8


# encodes the header which has all the information about the size of the image
def encode_header(image, bitstream):
    height_bits = pad_bits(to_binary_list(image.height), 16)
    bitstream.write_bits(height_bits)
    width_bits = pad_bits(to_binary_list(image.width), 16)
    bitstream.write_bits(width_bits)


# this encodes the tree. This is used for encoding and decoding the image
def encode_tree(tree, bitstream):
    if type(tree) == tuple: # Note - write 0 and encode children
        bitstream.write_bit(0)
        encode_tree(tree[0], bitstream)
        encode_tree(tree[1], bitstream)
    else: # Leaf - write 1, followed by 8 bit symbol
        bitstream.write_bit(1)
        symbol_bits = pad_bits(to_binary_list(tree), 8)
        bitstream.write_bits(symbol_bits)


# this uses the codes to encode with the bitstream, writing the next pixel value
def encode_pixels(image, codes, bitstream):
    for pixel in image.getdata():
        for value in pixel:
            bitstream.write_bits(codes[value])


# this is the function which actually compresses the image
def compress_image(in_file_name, out_file_name):
    print('Compressing "%s" -> "%s"' % (in_file_name, out_file_name))
    image = Image.open(in_file_name)
    print('Image shape: (height=%d, width=%d)' % (image.height, image.width))
    size_raw = raw_size(image.height, image.width)
    print('RAW image size: %d bytes' % size_raw)
    counts = count_symbols(image)
    print('Counts: %s' % counts)
    tree = build_tree(counts)
    print('Tree: %s' % str(tree))
    trimmed_tree = trim_tree(tree)
    print('Trimmed tree: %s' % str(trimmed_tree))
    codes = assign_codes(trimmed_tree)
    print('Codes: %s' % codes)

    size_estimate = compressed_size(counts, codes)
    print('Estimated size: %d bytes' % size_estimate)

    print('Writing...')
    stream = OutputBitStream.OutputBitStream(out_file_name)
    print('* Header offset: %d' % stream.bytes_written)
    encode_header(image, stream)
    stream.flush() # Ensure next chunk is byte-aligned
    print('* Tree offset: %d' % stream.bytes_written)
    encode_tree(trimmed_tree, stream)
    stream.flush() # Ensure next chunk is byte-aligned
    print('* Pixel offset: %d' % stream.bytes_written)
    encode_pixels(image, codes, stream)
    stream.close()

    size_real = stream.bytes_written
    print('Wrote %d bytes.' % size_real)

    print('Estimate is %scorrect.' % ('' if size_estimate == size_real else 'in'))
    print('Compression ratio: %0.2f' % (float(size_raw) / size_real))

    return


# returns binary list as integer
def from_binary_list(bits):
    result = 0
    for bit in bits:
        result = (result << 1) | bit
    return result


# converts an integer to a list of binary bits
def to_binary_list(n):
    return [n] if (n <= 1) else to_binary_list(n >> 1) + [n & 1]


# this function pads lists of bits to ensure correct size
def pad_bits(bits, n):
    assert (n >= len(bits))
    return [0] * (n - len(bits)) + bits


def decode_header(bitstream):
    height = from_binary_list(bitstream.read_bits(16))
    width = from_binary_list(bitstream.read_bits(16))
    return (height, width)


# https://stackoverflow.com/a/759766/3962537
def decode_tree(bitstream):
    flag = bitstream.read_bits(1)[0]
    if flag == 1: # Leaf, read and return symbol
        return from_binary_list(bitstream.read_bits(8))
    left = decode_tree(bitstream)
    right = decode_tree(bitstream)
    return (left, right)


def decode_value(tree, bitstream):
    bit = bitstream.read_bits(1)[0]
    node = tree[bit]
    if type(node) == tuple:
        return decode_value(node, bitstream)
    return node

def decode_pixels(height, width, tree, bitstream):
    pixels = bytearray()
    for i in range(height * width * 3):
        pixels.append(decode_value(tree, bitstream))
    return Image.frombytes('RGB', (width, height), bytes(pixels))


# this function decompresses the image
def decompress_image(in_file_name, out_file_name):
    print('Decompressing "%s" -> "%s"' % (in_file_name, out_file_name))

    print('Reading...')
    stream = InputBitStream.InputBitStream(in_file_name)
    print('* Header offset: %d' % stream.bytes_read)
    height, width = decode_header(stream)
    stream.flush() # Ensure next chunk is byte-aligned
    print('* Tree offset: %d' % stream.bytes_read)
    trimmed_tree = decode_tree(stream)
    stream.flush() # Ensure next chunk is byte-aligned
    print('* Pixel offset: %d' % stream.bytes_read)
    image = decode_pixels(height, width, trimmed_tree, stream)
    stream.close()
    print('Read %d bytes.' % stream.bytes_read)

    print('Image size: (height=%d, width=%d)' % (height, width))
    print('Trimmed tree: %s' % str(trimmed_tree))
    image.save(out_file_name)


# calculates raw size (header_size + pixel_size)/8
def raw_size(width, height):
    header_size = 2 * 16 # height and width as 16 bit values
    pixels_size = 3 * 8 * width * height # 3 channels, 8 bits per channel
    return (header_size + pixels_size) / 8


# this checks to confirm lossless compression and decompression
def images_equal(file_name_a, file_name_b):
    image_a = Image.open(file_name_a)
    image_b = Image.open(file_name_b)

    diff = ImageChops.difference(image_a, image_b)

    return diff.getbbox() is None










