import re
import os


class WechatImageDecoder:
    def __init__(self, dat_file):
        self.dat_file = dat_file.lower()

    def decode(self):
        if re.match(r'.+\.dat$', self.dat_file):
            return self._decode_pc_dat()
        else:
            raise Exception('Unknown file type')

    def _decode_pc_dat(self):

        def do_magic(header_code, buf):
            return header_code ^ list(buf)[0] if buf else 0x00

        def decode(magic, buf):
            return bytearray([b ^ magic for b in list(buf)])

        def guess_encoding(buf):
            headers = {
                'jpg': (0xff, 0xd8),
                'png': (0x89, 0x50),
                'gif': (0x47, 0x49),
            }
            for encoding in headers:
                header_code, check_code = headers[encoding]
                magic = do_magic(header_code, buf)
                _, code = decode(magic, buf[:2])
                if check_code == code:
                    return (encoding, magic)
            raise Exception('Decode failed')

        with open(self.dat_file, 'rb') as f:
            buf = bytearray(f.read())
        file_type, magic = guess_encoding(buf)

        img_file = os.path.splitext(self.dat_file)[0] + '.' + file_type
        with open(img_file, 'wb') as f:
            new_buf = decode(magic, buf)
            f.write(new_buf)

        return img_file  # 返回解密后的文件路径
