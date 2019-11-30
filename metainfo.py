import sys
import hashlib
import os
import torrent_parser
import time



def generate_hash(piece, hash_func):
    h = hash_func(piece.encode())
    return h.hexdigest()

def generate_pieces(paths, piece_length):
    pieces = []
    for path in paths:
        with open(path) as file:
            while True:
                piece = file.read(piece_length)
                if not piece:
                    break
                pieces.append(generate_hash(piece, hashlib.sha1))
    return pieces

def create_metainfo(paths, announce, announce_list=[], mode="single-file", piece_length=256*1024, encoding="utf-8", comment="", created_by=""):
    metainfo = {
        "info": {
            "piece_length": piece_length,
            "pieces": generate_pieces(paths, piece_length)
        },

        "announce": announce,
        "announce-list": announce_list,
        "comment": comment,
        "created_by": created_by,
        "creation_date": int(time.time()),
        "encoding": encoding
    }

    if mode == "single-file":
        with open(paths[0]) as file:
            metainfo["info"]["name"] = file.name
            metainfo["info"]["length"] = os.stat(paths[0]).st_size

    elif mode == "multiple-file":
        files = []
        for path in paths:
            with open(path) as f:
                files.append({'path': path, 'length': os.stat(path).st_size})
        metainfo["info"]["files"] = files

    else: raise Exception("Invalid file mode")
    print(metainfo['info']['pieces'])
    return metainfo

def create_torrent(metainfo_dict):
    name = metainfo_dict["info"]["name"] + ".torrent"
    torrent_parser.create_torrent_file(name, metainfo_dict)
    return name

def decode_torrent(torrent_name):
    return torrent_parser.parse_torrent_file(torrent_name)