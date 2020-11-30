from PIL import Image

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

def encode_header(image, bitstream):
    height_bits = pad_bits(to_binary_list(image.height), 16)
    bitstream.write_bits(height_bits)
    width_bits = pad_bits(to_binary_list(image.width), 16)
    bitstream.write_bits(width_bits)

def encode_tree(tree, bitstream):
    if type(tree) == tuple: # Note - write 0 and encode children
        bitstream.write_bit(0)
        encode_tree(tree[0], bitstream)
        encode_tree(tree[1], bitstream)
    else: # Leaf - write 1, followed by 8 bit symbol
        bitstream.write_bit(1)
        symbol_bits = pad_bits(to_binary_list(tree), 8)
        bitstream.write_bits(symbol_bits)

def encode_pixels(image, codes, bitstream):
    for pixel in image.getdata():
        for value in pixel:
            bitstream.write_bits(codes[value])

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
    stream = OutputBitStream(out_file_name)
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

    def decode_header(bitstream):
        height = from_binary_list(bitstream.read_bits(16))
        width = from_binary_list(bitstream.read_bits(16))
        return (height, width)

    # https://stackoverflow.com/a/759766/3962537
    def decode_tree(bitstream):
        flag = bitstream.read_bits(1)[0]
        if flag == 1:  # Leaf, read and return symbol
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

    def decompress_image(in_file_name, out_file_name):
        print('Decompressing "%s" -> "%s"' % (in_file_name, out_file_name))

        print('Reading...')
        stream = InputBitStream(in_file_name)
        print('* Header offset: %d' % stream.bytes_read)
        height, width = decode_header(stream)
        stream.flush()  # Ensure next chunk is byte-aligned
        print('* Tree offset: %d' % stream.bytes_read)
        trimmed_tree = decode_tree(stream)
        stream.flush()  # Ensure next chunk is byte-aligned
        print('* Pixel offset: %d' % stream.bytes_read)
        image = decode_pixels(height, width, trimmed_tree, stream)
        stream.close()
        print('Read %d bytes.' % stream.bytes_read)

        print('Image size: (height=%d, width=%d)' % (height, width))
        print('Trimmed tree: %s' % str(trimmed_tree))
        image.save(out_file_name)

