import json, hashlib, torrent_parser

def load_json(path):
    data = {}
    try:
        with open(path) as json_file:
            data = parse_from_json(json.load(json_file))
    except:
        # dump_json(data, path)
        pass

    return data

def get_infohash(metainfo):
    return hashlib.sha1(torrent_parser.encode(metainfo["info"])).hexdigest()