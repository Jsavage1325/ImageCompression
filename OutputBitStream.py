# Class for writing bits to file
class OutputBitStream(object):
    def __init__(self, file_name):
        self.file_name = file_name
        self.file = open(self.file_name, 'wb')
        self.bytes_written = 0
        self.buffer = []

    # returns binary list as integer
    def from_binary_list(self, bits):
        result = 0
        for bit in bits:
            result = (result << 1) | bit
        return result

    def write_bit(self, value):
        self.write_bits([value])

    def write_bits(self, values):
        self.buffer += values
        while len(self.buffer) >= 8:
            self._save_byte()

    def flush(self):
        if len(self.buffer) > 0: # Add trailing zeros to complete a byte and write it
            self.buffer += [0] * (8 - len(self.buffer))
            self._save_byte()
        assert(len(self.buffer) == 0)

    def _save_byte(self):
        bits = self.buffer[:8]
        self.buffer[:] = self.buffer[8:]

        byte_value = self.from_binary_list(bits)
        self.file.write(bytes([byte_value]))
        self.bytes_written += 1

    def close(self):
        self.flush()
        self.file.close()


