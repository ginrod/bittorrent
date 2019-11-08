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

def concat_pieces(pieces):
    result = ""
    for piece in pieces:
        result += piece
    return result

def create_metainfo(paths, announce, announce_list=[], mode="single-file", piece_length=256*1024, encoding="utf-8", comment="", created_by=""):
    metainfo = {
        "info": {
            "piece_length": piece_length,
            "pieces": concat_pieces(generate_pieces(paths, piece_length))
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

    return (metainfo["info"]["name"], torrent_parser.encode(metainfo))

def create_torrent(name_and_metainfo):
    name, bencoded_metainfo = name_and_metainfo
    with open(name + ".torrent", "w") as torrent:
        torrent.write(str(bencoded_metainfo))
    return name

# def decode_torrent(torrent_name):
#     metainfo = None
#     with open(torrent_name) as torrent:
#         data_bencoded = ""
#         r = torrent.read(1024)
#         while r:
#             data_bencoded += r
#             r = torrent.read(1024)
#         metainfo = torrent_parser.decode(data_bencoded, encoding="utf-8")
#     return metainfo
    
# name, metainfo = create_metainfo(["metainfo.py"], "tracker.com", piece_length=100, comment="This is a comment", created_by="BitTorrentMatcom")
# dotTorrent = create_torrent((name, metainfo))
# print(decode_torrent("metainfo.py.torrent"))
