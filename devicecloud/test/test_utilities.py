import json
import httpretty


def _cloud_uri(path):
    return "https://login.etherios.com{}".format(path)


def prepare_json_response(method, path, data):
    # TODO: should probably assert on more request headers and respond with correct content type, etc.
    httpretty.register_uri(
        method,
        _cloud_uri(path),
        json.dumps(data))
