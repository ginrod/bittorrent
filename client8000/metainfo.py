import sys, hashlib, os, torrent_parser, time

MAX_PIECE_SIZE = 1024 * 1024

def generate_hash(piece, hash_func):
    h = hash_func(piece)
    return h.hexdigest()

def generate_pieces(paths, piece_length):
    pieces = []
    i = 0
    for path in paths:
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

def create_metainfo(paths, announce, announce_list=[], mode="single-file", encoding="utf-8", comment="", created_by="", multiple_file_name="torent_files"):
    size = os.stat(paths[0]).st_size
    # piece_length = choose_piece_length(size)
    piece_length = MAX_PIECE_SIZE
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
            metainfo["info"]["name"] = paths[0]

            try:
                metainfo["info"]["short_name"] = file.name[file.name.rfind('/') + 1: file.name.rfind('.')]
            except:
                metainfo["info"]["short_name"] = file.name[file.name.rfind('/') + 1:]

            try:
                metainfo["info"]["extension"] = file.name[file.name.rfind('.'):]
            except:
                metainfo["info"]["extension"] = "None"

            metainfo["info"]["length"] = size
            metainfo["info"]["no_pieces"] = metainfo["info"]["length"] // metainfo["info"]["piece_length"] + 1

    elif mode == "multiple-file":
        files = []
        for path in paths:
            with open(path) as f:
                files.append({'path': path, 'length': os.stat(path).st_size})
        metainfo["info"]["files"] = files

        metainfo["info"]["short_name"] = multiple_file_name
        metainfo['info']['extension'] = ""

    else: raise Exception("Invalid file mode")

    return metainfo

def create_torrent(metainfo_dict):
    name = metainfo_dict["info"]["name"] + ".torrent"
    torrent_parser.create_torrent_file(name, metainfo_dict)
    return name

def decode_torrent(torrent_name):
    return torrent_parser.parse_torrent_file(torrent_name)
