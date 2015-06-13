# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Copyright (c) 2015 Digi International, Inc.
import sys
import xml.etree.ElementTree as ET

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

        params = {"embed": "true"}
        if condition is not None:
            params["condition"] = condition.compile()

        for device_json in self._conn.iter_json_pages("/ws/DeviceCore", page_size=page_size, **params):
            yield Device(self._conn, self._sci, device_json)

    def get_group_tree_root(self, page_size=1000):
        r"""Return the root group for this accounts' group tree

        This will return the root group for this tree but with all links
        between nodes (i.e. children starting from root) populated.

        Examples::

            # print the group hierarchy to stdout
            dc.devicecore.get_group_tree_root().print_subtree()

            # gather statistics about devices in each group including
            # the count from its subgroups (recursively)
            #
            # This also shows how you can go from a group reference to devices
            # for that particular group.
            stats = {}  # group -> devices count including children
            def count_nodes(group):
                count_for_this_node = \
                    len(list(dc.devicecore.get_devices(group_path == group.get_path())))
                subnode_count = 0
                for child in group.get_children():
                    subnode_count += count_nodes(child)
                total = count_for_this_node + subnode_count
                stats[group] = total
                return total
            count_nodes(dc.devicecore.get_group_tree_root())

        :param int page_size: The number of results to fetch in a
            single page.  In general, the default will suffice.
        :returns: The root group for this device cloud accounts group
            hierarchy.

        """

        # first pass, build mapping
        group_map = {}  # map id -> group
        page_size = validate_type(page_size, *six.integer_types)
        for group in self.get_groups(page_size=page_size):
            group_map[group.get_id()] = group

        # second pass, find root and populate list of children for each node
        root = None
        for group_id, group in group_map.items():
            if group.is_root():
                root = group
            else:
                parent = group_map[group.get_parent_id()]
                parent.add_child(group)
        return root

    def get_groups(self, condition=None, page_size=1000):
        """Return an iterator over all groups in this device cloud account

        Optionally, a condition can be specified to limit the number of
        groups returned.

        Examples::

            # Get all groups and print information about them
            for group in dc.devicecore.get_groups():
                print group

            # Iterate over all devices which are in a group with a specific
            # ID.
            group = dc.devicore.get_groups(group_id == 123)[0]
            for device in dc.devicecore.get_devices(group_path == group.get_path()):
                print device.get_mac()

        :param condition: A condition to use when filtering the results set.  If
            unspecified, all groups will be returned.
        :param int page_size: The number of results to fetch in a
            single page.  In general, the default will suffice.
        :returns: Generator over the groups in this device cloud account.  No
            guarantees about the order of results is provided and child links
            between nodes will not be populated.

        """
        query_kwargs = {}
        if condition is not None:
            query_kwargs["condition"] = condition.compile()
        for group_data in self._conn.iter_json_pages("/ws/Group", page_size=page_size, **query_kwargs):
            yield Group.from_json(group_data)

    def delete_device(self, dev):
        """ Delete a from the cloud account associated with the handle.

        :raises DeviceCloudHttpException: If there is an unexpected error reported by the device cloud.
        :param dev: Device object of the device to delete.
        :return: the Response from the delete request.
        """
        return self._conn.delete('/ws/DeviceCore/%s' % dev.get_device_id())

    def provision_device(self, **kwargs):
        """Provision a single device with the specified information

        This API call provisions a new device on this cloud account.  In order for this
        to work, a `mac_address`, `device_id`, or `imei` must be provided.  All
        other parameters are optional and can be specified in addition to the primary
        identifier for the device.

        This request will always return a dictionary unless the request fails altogether.  The
        dictionary returned will have the following form::

            {
                "error": <bool>,
                "error_msg": <string|None>,
                "location": <string|None>,
            }

        :param str mac_address: The MAC address of the device being added as a string in
            the form "00:00:00:00:00:00".  This is one of the options for the required
            primary id.
        :param str device_id: The ID of the device to add.  This is the 'devConnectwareId'
            referenced in the API docs and should look like "00000000-00000000-000000FF-FF000000".
            This is one of the options for the required primary id.
        :param str imei: The IMEI of the device to be added (if no MAC/ID available).  This is one
            of the options for the required primary id.
        :param str group_path: (optional) Path of group that this device should be added to.
        :param str metadata: (optional) Arbitrary metadata to associate with this device.
        :param float map_lat: (optional) Latitude of this device in degrees
        :param float map_long: (optional) Longitude of this device in degrees
        :param str contact: (optional) Contact associted with this device (or whatever you want).
        :param str description: (optional) Textual description of this device.

        :raises DeviceCloudHttpException: If there is an unexpected error reported by the device cloud.
        :raises ValueError: If any input fields are known to have a bad form.
        :return: A dictionary matching the format specified above.

        """
        # This snippet is from the device cloud API Explorer and shows the pieces of
        # information that may be specified when adding a device.
        #
        # <DeviceCore>
        #   <!--Devices can be created by MAC address, IMEI
        #       (generally only if the device has no MAC address), or deviceID. -->
        #   <!-- <devMac>00:00:00:00:00:00</devMac> -->
        #   <!-- <devCellularModemId>112222223333334</devCellularModemId> -->
        #   <!-- <devConnectwareId>00000000-00000000-000000FF-FF000000</devConnectwareId> -->
        #   <!-- Optional elements that can be included to describe the device. -->
        #   <!-- <grpPath>test</grpPath> -->
        #   <!-- <dpUserMetaData>In the test lab.</dpUserMetaData> -->
        #   <!-- <dpTags>needs-upgrade</dpTags> -->
        #   <!-- <dpMapLat>44.0</dpMapLat>  (will be overwritten if the device reports a value)-->
        #   <!-- <dpMapLong>-92.5</dpMapLong>  (will be overwritten if the device reports a value) -->
        #   <!-- <dpContact>Joe</dpContact>  (will be overwritten if the device reports a value) -->
        #   <!-- <dpDescription>Test device</dpDescription>  (will be overwritten if the device reports a value) -->
        # </DeviceCore>

        results = self.provision_devices([kwargs, ])
        return results[0]

    def provision_devices(self, devices):
        """Provision multiple devices with a single API call

        This method takes an iterable of dictionaries where the values in the dictionary are
        expected to match the arguments of a call to :meth:`provision_device`.  The
        contents of each dictionary will be validated.

        :param list devices: An iterable of dictionaries each containing information about
            a device to be provision.  The form of the dictionary should match the keyword
            arguments taken by :meth:`provision_device`.
        :raises DeviceCloudHttpException: If there is an unexpected error reported by the device cloud.
        :raises ValueError: If any input fields are known to have a bad form.
        :return: A list of dictionaries in the form described for :meth:`provision_device` in the
            order matching the requested device list.  Note that it is possible for there to
            be mixed success and error when provisioning multiple devices.

        """
        # Validate all the input for each device provided
        sio = six.StringIO()

        def write_tag(tag, val):
            sio.write("<{tag}>{val}</{tag}>".format(tag=tag, val=val))

        def maybe_write_element(tag, val):
            if val is not None:
                write_tag(tag, val)
                return True
            return False

        sio.write("<list>")
        for d in devices:
            sio.write("<DeviceCore>")

            mac_address = d.get("mac_address")
            device_id = d.get("device_id")
            imei = d.get("imei")
            if mac_address is not None:
                write_tag("devMac", mac_address)
            elif device_id is not None:
                write_tag("devConnectwareId", device_id)
            elif imei is not None:
                write_tag("devCellularModemId", imei)
            else:
                raise ValueError("mac_address, device_id, or imei must be provided for device %r" % d)

            # Write optional elements if present.
            maybe_write_element("grpPath", d.get("group_path"))
            maybe_write_element("dpUserMetaData", d.get("metadata"))
            maybe_write_element("dpTags", d.get("tags"))
            maybe_write_element("dpMapLong", d.get("map_long"))
            maybe_write_element("dpMapLat", d.get("map_lat"))
            maybe_write_element("dpContact", d.get("contact"))
            maybe_write_element("dpDescription", d.get("description"))

            sio.write("</DeviceCore>")
        sio.write("</list>")

        # Send the request, set the Accept XML as a nicety
        results = []
        response = self._conn.post("/ws/DeviceCore", sio.getvalue(), headers={'Accept': 'application/xml'})
        root = ET.fromstring(response.content)  # <result> tag is root of <list> response
        for child in root:
            if child.tag.lower() == "location":
                results.append({
                    "error": False,
                    "error_msg": None,
                    "location": child.text
                })
            else:  # we expect "error" but handle generically
                results.append({
                    "error": True,
                    "location": None,
                    "error_msg": child.text
                })

        return results


class Group(object):
    """Provides access to information about a group in the device cloud

    .. note::

       This is primarily a container object and does not provide any functions itself at
       this time.  Information from here can be used along with other APIs to, for example,
       get all devices with a given group path.  This may change in the future.

    """

    def __init__(self, group_id, name, description, path, parent_id):
        self._id = group_id
        self._name = name
        self._description = description
        self._path = path
        self._parent_id = parent_id
        self._children = []

    @classmethod
    def from_json(cls, json_data):
        """Build and return a new Group object from json data (used internally)"""
        # Example Data:
        # { "grpId": "11817", "grpName": "7603_Etherios", "grpDescription": "7603_Etherios root group",
        #   "grpPath": "\/7603_Etherios\/", "grpParentId": "1"}
        return cls(
            group_id=json_data["grpId"],
            name=json_data["grpName"],
            description=json_data.get("grpDescription", ""),
            path=json_data["grpPath"],
            parent_id=json_data["grpParentId"],
        )

    def __repr__(self):
        return "Group(group_id={!r}, name={!r}, description{!r}, path={!r}, parent_id={!r})".format(
            self._id, self._name, self._description, self._path, self._parent_id
        )

    def print_subtree(self, fobj=sys.stdout, level=0):
        """Print this group node and the subtree rooted at it"""
        fobj.write("{}{!r}\n".format(" " * (level * 2), self))
        for child in self.get_children():
            child.print_subtree(fobj, level + 1)

    def is_root(self):
        """Return True if the group is the root for this account"""
        return self.get_parent_id() == "1"

    def add_child(self, group):
        """Add a child group reference to this one"""
        self._children.append(group)

    def get_children(self):
        """Return each child :class:`Group` of this one in a list"""
        return self._children[:]

    def get_id(self):
        """Get the ID of this group as as string"""
        return self._id

    def get_name(self):
        """Get the name of this group as a string"""
        return self._name

    def get_description(self):
        """Get the description of this group as a string"""
        return self._description

    def get_path(self):
        """Get the full path of this group as a string"""
        return self._path

    def get_parent_id(self):
        """Get the ID of this groups parent as a string"""
        return self._parent_id


class Device(object):
    """Interface to a device in the device cloud"""

    # TODO: provide ability to set/update available data items
    # TODO: add/remove tags

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