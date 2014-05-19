from apibase import APIBase
import json


class DeviceCoreAPI(APIBase):
    def list_devices(self):
        devicecore_response = self._conn.get("/ws/DeviceCore/.json")
        json_dump = json.loads(devicecore_response)["items"]
        devices = []
        for device_json in json_dump:
            devices.append(Device.from_json(device_json))
        return devices


class Device(object):
    """Interface to a device in the device cloud"""

    # TODO: provide access to additional data items (lat/lon/etc.)
    # TODO: provide ability to set/update available data items
    # TODO: add/remove tags
    # TODO: add device to group
    # TODO: remove device from a group
    # TODO: provision a new device (probably add top-level method for this)

    @classmethod
    def from_json(cls, device_json):
        mac = device_json.get("devMac")
        connectware_id = device_json.get("devConnectwareId")
        device_id = device_json["id"].get("devId")
        ip = device_json.get("dpLastKnownIp")

        potential_tags = device_json.get("dpTags")
        if potential_tags:
            tags = potential_tags.split(",")
        else:
            tags = []

        connected = (int(device_json.get("dpConnectionStatus")) > 0)

        return cls(mac, connectware_id, device_id, ip, tags, connected)

    def __init__(self, mac, connectware_id, device_id, ip, tags, connected):
        self._mac = mac
        self._connectware_id = connectware_id
        self._device_id = device_id
        self._ip = ip
        self._tags = tags

    def __repr__(self):
        return "Device(%r, %r)" % (self._connectware_id, self._mac)

    def get_tags(self):
        """Get the list of tags for this device"""
        return self._tags

    def get_connectware_id(self):
        """Get the connectware id of this device (primary key)"""
        return self._connectware_id

    def get_device_id(self):
        """Get this device's device id"""
        return self._device_id

    def get_ip(self):
        """Get the last known IP of this device"""
        return self._ip

    def get_mac(self):
        """Get the MAC address of this device"""
        return self._mac

    def get_mac_last4(self):
        """Get the last 4 characters in the device mac address hex (e.g. 00:40:9D:58:17:5B -> 175B)

        This is useful for use as a short reference to the device.  It is not guaranteed to
        be unique (obviously) but will often be if you don't have too many devices.

        """
        chunks = self._mac.split(":")
        mac4 = "%s%s" % (chunks[-2], chunks[-1])
        return mac4.upper()
