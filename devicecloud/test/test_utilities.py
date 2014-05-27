import json
import httpretty


def _cloud_uri(path):
    return "https://login.etherios.com{}".format(path)


def prepare_response(method, path, data, status=200):
    # TODO: should probably assert on more request headers and respond with correct content type, etc.
    httpretty.register_uri(
        method,
        _cloud_uri(path),
        data,
        status=status)


def prepare_json_response(method, path, data):
    prepare_response(method, path, json.dumps(data))

