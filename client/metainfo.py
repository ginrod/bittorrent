import sys, hashlib, os, torrent_parser, time

MAX_PIECE_SIZE = 1024 * 1024

def generate_hash(piece, hash_func):
    h = hash_func(piece)
    return h.hexdigest()

def generate_pieces(path, piece_length):
    pieces = []
    i = 0
    with open(path, "rb") as file:
        while True:
            piece = file.read(piece_length)
            if not piece:
                break
            pieces.append(generate_hash(piece, hashlib.sha1))
            print(f"Piece {i} generated")
            i += 1
    return pieces

def choose_piece_length(file_size):
    piece_length = 16 * 1024
    number_of_pieces = file_size / piece_length

    if piece_length >= file_size:
        return piece_length

    while number_of_pieces >= 1250 and piece_length < (1024*1024):
        piece_length += 1024
        number_of_pieces = file_size/piece_length

    return piece_length

def create_metainfo(path, announce, announce_list=[], encoding="utf-8", comment="", created_by="", multiple_file_name="torent_files"):
    size = os.stat(path).st_size
    # piece_length = choose_piece_length(size)
    piece_length = MAX_PIECE_SIZE
    metainfo = {
        "info": {
            "piece_length": piece_length,
            "pieces": generate_pieces(path, piece_length)
        },

        "announce": announce,
        "announce-list": announce_list,
        "comment": comment,
        "created_by": created_by,
        "creation_date": int(time.time()),
        "encoding": encoding
    }

    metainfo["info"]["name"] = os.path.basename(path)
    metainfo["info"]["length"] = size
    metainfo["info"]["no_pieces"] = metainfo["info"]["length"] // metainfo["info"]["piece_length"] + 1

    return metainfo

def create_torrent(metainfo_dict):
    name = metainfo_dict["info"]["name"] + ".torrent"
    torrent_parser.create_torrent_file(name, metainfo_dict)
    return name

def decode_torrent(torrent_name):
    return torrent_parser.parse_torrent_file(torrent_name)
