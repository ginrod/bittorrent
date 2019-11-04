import sys
import hashlib


def generate_hash(piece, hash_func):
    h = hash_func(piece.encode())
    return int.from_bytes(h.digest(), byteorder = sys.byteorder)

def generate_pieces(_file, piece_length):
    pieces = []
    while True:
        piece = _file.read(piece_length)
        if not piece:
            break
        pieces.append(generate_hash(piece, hashlib.sha1))
    return pieces
