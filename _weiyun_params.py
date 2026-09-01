import hashlib, base64, json, sys

BLOCK = 524288  # 512KB

class StreamSHA1:
    def __init__(self):
        self.h = [0x67452301,0xEFCDAB89,0x98BADCFE,0x10325476,0xC3D2E1F0]
        self.buf = b""
    def _rotl(self, x, n):
        return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF
    def _process(self, chunk):
        w = [0]*80
        for j in range(16):
            w[j] = int.from_bytes(chunk[j*4:j*4+4], "big")
        for j in range(16, 80):
            w[j] = self._rotl(w[j-3] ^ w[j-8] ^ w[j-14] ^ w[j-16], 1)
        a,b,c,d,e = self.h
        for j in range(80):
            if j < 20:   f = (b & c) | ((~b & 0xFFFFFFFF) & d); k = 0x5A827999
            elif j < 40: f = b ^ c ^ d; k = 0x6ED9EBA1
            elif j < 60: f = (b & c) | (b & d) | (c & d); k = 0x8F1BBCDC
            else:        f = b ^ c ^ d; k = 0xCA62C1D6
            tmp = (self._rotl(a,5) + f + e + k + w[j]) & 0xFFFFFFFF
            e = d; d = c; c = self._rotl(b,30); b = a; a = tmp
        self.h = [(self.h[i] + v) & 0xFFFFFFFF for i, v in enumerate([a,b,c,d,e])]
    def update(self, data):
        self.buf += data
        while len(self.buf) >= 64:
            self._process(self.buf[:64])
            self.buf = self.buf[64:]
    def state_hex(self):
        return b"".join(h.to_bytes(4, "little") for h in self.h).hex()

def main(path):
    with open(path, "rb") as f:
        data = f.read()
    size = len(data)
    # file_sha + md5
    file_sha = hashlib.sha1(data).hexdigest()
    file_md5 = hashlib.md5(data).hexdigest()

    # streaming block_sha_list
    s = StreamSHA1()
    block_sha_list = []
    off = 0
    nblocks = (size + BLOCK - 1) // BLOCK
    for i in range(nblocks):
        chunk = data[off:off+BLOCK]
        is_last = (i == nblocks - 1)
        s.update(chunk)
        if is_last:
            # last block sha = standard file sha
            block_sha_list.append(file_sha)
        else:
            block_sha_list.append(s.state_hex())
        off += BLOCK

    # check_sha / check_data
    lastBlockSize = size % BLOCK
    if lastBlockSize == 0:
        lastBlockSize = BLOCK
    checkBlockSize = lastBlockSize % 128
    if checkBlockSize == 0:
        checkBlockSize = 128
    s2 = StreamSHA1()
    # process all non-last blocks
    off = 0
    for i in range(nblocks - 1):
        s2.update(data[off:off+BLOCK])
        off += BLOCK
    # process first (lastBlockSize - checkBlockSize) bytes of last block
    last = data[off:off+lastBlockSize]
    s2.update(last[:lastBlockSize - checkBlockSize])
    check_sha = s2.state_hex()
    check_data = base64.b64encode(last[lastBlockSize - checkBlockSize:]).decode()

    out = {
        "filename": path.split("/")[-1].split("\\")[-1],
        "file_size": size,
        "file_sha": file_sha,
        "file_md5": file_md5,
        "block_sha_list": block_sha_list,
        "check_sha": check_sha,
        "check_data": check_data,
    }
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main(sys.argv[1])