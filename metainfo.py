import sys
import hashlib


def generate_hash(piece, hash_func):
    h = hash_func(piece.encode())
    return int.from_bytes(h.digest(), byteorder = sys.byteorder)



# def create_metainfo(files, mode, piece_length=256*1024):


#     metainfo = {
#         "info": {
#             "piece length": piece_length

#         }
#     }

