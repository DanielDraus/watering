import network


class Crypt:
    __AUTH_SIZE = 256
    __KEY = network.WLAN(network.STA_IF).config('mac')

    def __make_stream(self, stream_l):
        i, j = 0, 0
        while True:
            i = (i + 1) % self.__AUTH_SIZE
            j = (j + stream_l[i]) % self.__AUTH_SIZE
            stream_l[i], stream_l[j] = stream_l[j], stream_l[i]
            yield stream_l[(stream_l[i] + stream_l[j]) % self.__AUTH_SIZE]

    def encryptRC4(self, plaintext, hexformat=False):
        key = self.__KEY
        try:
            key, plaintext = bytes(key), bytearray(plaintext)  # necessary for py2, not for py3
        except TypeError:
            raise Exception(key, plaintext)
        S = list(range(self.__AUTH_SIZE))
        j = 0
        for i in range(self.__AUTH_SIZE):
            j = (j + S[i] + key[i % len(key)]) % self.__AUTH_SIZE
            S[i], S[j] = S[j], S[i]
        keystream = self.__make_stream(S)
        return b''.join(b"%02X" % (c ^ next(keystream)) for c in plaintext) if hexformat else bytearray(
            c ^ next(keystream) for c in plaintext)
