import datetime


def iso8601_to_dt(iso8601):
    """Given an ISO8601 string as returned by the device cloud, convert to a datetime object"""
    return datetime.datetime.strptime(iso8601, "%Y-%m-%dT%H:%M:%S.%fZ")
