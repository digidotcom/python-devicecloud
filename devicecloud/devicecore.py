# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2014 Etherios, Inc. All rights reserved.
# Etherios, Inc. is a Division of Digi International.

from devicecloud.apibase import APIBase
from devicecloud.conditions import Attribute, Expression
from devicecloud.util import iso8601_to_dt, validate_type
import six


dev_mac = Attribute('devMac')
group_id = Attribute('grpId')
group_path = Attribute('grpPath')
dev_connectware_id = Attribute('devConnectwareId')
# TODO: Can we support location based device lookups? (e.g. lat/long?)


ADD_GROUP_TEMPLATE = \
"""
<DeviceCore>
    <devConnectwareId>{connectware_id}</devConnectwareId>
    <grpPath>{group_path}</grpPath>
</DeviceCore>
"""


class DeviceCoreAPI(APIBase):
    """Encapsulate DeviceCore interface"""

    def __init__(self, conn, sci):
        APIBase.__init__(self, conn)
        self._sci = sci

    def get_devices(self, condition=None, page_size=1000):
        """Iterates over each :class:`Device` for this device cloud account

        Examples::

            # get a list of all devices
            all_devices = list(dc.devicecore.get_devices())

            # build a mapping of devices by their vendor id using a
            # dict comprehension
            devices = dc.devicecore.get_devices()  # generator object
            devs_by_vendor_id = {d.get_vendor_id(): d for d in devices}

            # iterate over all devices in 'minnesota' group and
            # print the device mac and location
            for device in dc.get_devices(group_path == 'minnesota'):
                print "%s at %s" % (device.get_mac(), device.get_location())

        :param condition: An :class:`.Expression` which defines the condition
            which must be matched on the devicecore.  If unspecified,
            an iterator over all devices will be returned.
        :param int page_size: The number of results to fetch in a
            single page.  In general, the default will suffice.
        :returns: Iterator over each :class:`~Device` in this device cloud
            account in the form of a generator object.
        """

        condition = validate_type(condition, type(None), Expression, *six.string_types)
        page_size = validate_type(page_size, *six.integer_types)
        offset = 0
        remaining_size = 1  # just needs to be non-zero

        while remaining_size > 0:
            req = (
                "/ws/DeviceCore?embed=true"
                "&start={offset}"
                "&size={page_size}".format(
                    page_size=page_size,
                    offset=offset)
            )
            if condition is not None:
                req = "".join([req, "&condition={0}".format(condition.compile())])
            response = self._conn.get_json(req)
            offset += page_size
            remaining_size = int(response.get("remainingSize", "0"))
            for device_json in response.get("items", []):
                yield Device(self._conn, self._sci, device_json)


class Device(object):
    """Interface to a device in the device cloud"""

    # TODO: provide ability to set/update available data items
    # TODO: add/remove tags
    # TODO: provision a new device (probably add top-level method for this)

    def __init__(self, conn, sci, device_json):
        self._conn = conn
        self._sci = sci
        self._device_json = device_json

    def __repr__(self):
        return "Device(%r, %r)" % (self.get_connectware_id(), self.get_mac())

    def get_device_json(self, use_cached=True):
        """Get the JSON metadata for this device as a python data structure

        If ``use_cached`` is not True, then a web services request will be made
        synchronously in order to get the latest device metatdata.  This will
        update the cached data for this device.

        """
        if not use_cached:
            devicecore_data = self._conn.get_json(
                "/ws/DeviceCore/{}".format(self.get_device_id()))
            self._device_json = devicecore_data["items"][0]  # should only be 1
        return self._device_json

    def get_tags(self, use_cached=True):
        """Get the list of tags for this device"""
        device_json = self.get_device_json(use_cached)
        potential_tags = device_json.get("dpTags")
        if potential_tags:
            return potential_tags.split(",")
        else:
            return []

    def is_connected(self, use_cached=True):
        """Return True if the device is currrently connect and False if not"""
        device_json = self.get_device_json(use_cached)
        return int(device_json.get("dpConnectionStatus")) > 0

    def get_connectware_id(self, use_cached=True):
        """Get the connectware id of this device (primary key)"""
        device_json = self.get_device_json(use_cached)
        return device_json.get("devConnectwareId")

    def get_device_id(self, use_cached=True):
        """Get this device's device id"""
        device_json = self.get_device_json(use_cached)
        return device_json["id"].get("devId")

    def get_ip(self, use_cached=True):
        """Get the last known IP of this device"""
        device_json = self.get_device_json(use_cached)
        return device_json.get("dpLastKnownIp")

    def get_mac(self, use_cached=True):
        """Get the MAC address of this device"""
        device_json = self.get_device_json(use_cached)
        return device_json.get("devMac")

    def get_mac_last4(self, use_cached=True):
        """Get the last 4 characters in the device mac address hex (e.g. 00:40:9D:58:17:5B -> 175B)

        This is useful for use as a short reference to the device.  It is not guaranteed to
        be unique (obviously) but will often be if you don't have too many devices.

        """
        chunks = self.get_mac(use_cached).split(":")
        mac4 = "%s%s" % (chunks[-2], chunks[-1])
        return mac4.upper()

    def get_registration_dt(self, use_cached=True):
        """Get the datetime of when this device was added to the device cloud"""
        device_json = self.get_device_json(use_cached)
        start_date_iso8601 = device_json.get("devRecordStartDate")
        if start_date_iso8601:
            return iso8601_to_dt(start_date_iso8601)
        else:
            return None

    def get_meid(self, use_cached=True):
        """Return the meid as a string of this device if it has one or None"""
        return self.get_device_json(use_cached).get("devCellularModemId")

    def get_customer_id(self, use_cached=True):
        """Get the automatically generated customer id for this device"""
        return self.get_device_json(use_cached).get("cstId")

    def get_group_id(self, use_cached=True):
        """Get the id of the group with which this device is associated"""
        return self.get_device_json(use_cached).get("grpId")

    def get_group_path(self, use_cached=True):
        """Get the path of the group with which this device is associated"""
        return self.get_device_json(use_cached).get("grpPath")

    def get_vendor_id(self, use_cached=True):
        """Get the vendor id associated with this device if any"""
        return self.get_device_json(use_cached).get("dvVendorId")

    def get_device_type(self, use_cached=True):
        """Get the device type of this device if present"""
        return self.get_device_json(use_cached).get("dpDeviceType")

    def get_firmware_level(self, use_cached=True):
        """Get the firmware level of this device if present"""
        return self.get_device_json(use_cached).get("dpFirmwareLevel")

    def get_firmware_level_description(self, use_cached=True):
        """Get the firmware level as a string (rather than a number)"""
        return self.get_device_json(use_cached).get("dpFirmwareLevelDesc")

    # TODO: restricted status can also be set via PUT
    def get_restricted_status(self, use_cached=True):
        """Get the restricted status of this device

        The value here will be returned as an integer with 3 potential values:

        1. 0 - unrestricted
        2. 2 - restricted
        3. 3 - untrusted

        """
        return self.get_device_json(use_cached).get("dpRestrictedStatus")

    def get_last_known_ip(self, use_cached=True):
        """Get the last known IP address of this device"""
        return self.get_device_json(use_cached).get("dpLastKnownIp")

    def get_global_ip(self, use_cached=True):
        """Get the last known global IP from which a device connected (out of NAT)"""
        return self.get_device_json(use_cached).get("dpGlobalIp")

    def get_last_connected_dt(self, use_cached=True):
        """Get the datetime that the device last connected to the device cloud"""
        return iso8601_to_dt(self.get_device_json(use_cached).get("dpLastConnectTime"))

    def get_contact(self, use_cached=True):
        """Get the contact (if any) associated with this device"""
        return self.get_device_json(use_cached).get("dpContact")

    def get_description(self, use_cached=True):
        """Get the description associated with this device"""
        return self.get_device_json(use_cached).get("dpDescription")

    def get_location(self, use_cached=True):
        """Get the location (string) associated with this device"""
        return self.get_device_json(use_cached).get("dpLocation")

    def get_latlon(self, use_cached=True):
        """Get a tuple with device latitude and longitude... these may be None"""
        device_json = self.get_device_json(use_cached)
        lat = device_json.get("dpMapLat")
        lon = device_json.get("dpMapLong")
        return (float(lat) if lat else None,
                float(lon) if lon else None, )

    def get_user_metadata(self, use_cached=True):
        """Get the user metadata for this device (string) if present"""
        return self.get_device_json(use_cached).get("dpUserMetaData")

    def get_zb_pan_id(self, use_cached=True):
        """Get the Zigbee PAN ID from the device if present"""
        return self.get_device_json(use_cached).get("dpPanId")

    def get_zb_extended_address(self, use_cached=True):
        """Get the Zigbee extended address of this device if present"""
        return self.get_device_json(use_cached).get("xpExtAddr")

    def get_server_id(self, use_cached=True):
        """Get the ID of the server this device is currently connected to"""
        return self.get_device_json(use_cached).get("dpServerId")

    def get_provision_id(self, use_cached=True):
        """Get the provisioning ID of this device if used"""
        return self.get_device_json(use_cached).get("provisionId")

    # TODO: need to research to see if this can actually be retried
    # TODO: should add support for setting this password via the API
    def get_current_connect_pw(self, use_cached=True):
        """Get the current connection password for this device"""
        return self.get_device_json(use_cached).get("dpCurrentConnectPw")

    def add_to_group(self, group_path):
        """Add a device to a group, if the group doesn't exist it is created

        :param group_path: Path or "name" of the group
        """

        if self.get_group_path() != group_path:
            post_data = ADD_GROUP_TEMPLATE.format(connectware_id=self.get_connectware_id(),
                                                  group_path=group_path)
            self._conn.put('/ws/DeviceCore', post_data)

            # Invalidate cache
            self._device_json = None

    def remove_from_group(self):
        """Place a device back into the root group"""

        if self.get_group_path() != '':
            post_data = ADD_GROUP_TEMPLATE.format(connectware_id=self.get_connectware_id(),
                                                  group_path='')
            self._conn.put('/ws/DeviceCore', post_data)

            # Invalidate cache
            self._device_json = None