from apibase import APIBase
import json


class DeviceCoreAPI(APIBase):
    def get_devices(self):
        devicecore_response = self._conn.get("/ws/DeviceCore/.json")
        json_dump = json.loads(devicecore_response)["items"]
        devices = []
        for device_json in json_dump:
            devices.append(Device.from_json(device_json))
        return devices


class Device(object):
    """Interface to a device in the device cloud"""

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
        self.mac = mac
        self.connectware_id = connectware_id
        self.device_id = device_id
        self.ip = ip
        self.tags = tags

    def __repr__(self):
        return "Device(%r, %r)" % (self.connectware_id, self.mac)

    def mac_as_last_4(self):
        chunks = self.mac.split(":")
        mac4 = "%s%s" % (chunks[-2], chunks[-1])
        return mac4.upper()
