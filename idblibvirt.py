#! /usr/bin/env python
"""IDB libcloud adapter"""

import argparse
import json

import requests

import libcloud.compute.types
import libcloud.compute.providers


class UnknownDriverError(Exception):
    pass


class InvalidZoneConfigError(Exception):
    pass


class Zone(object):

    create = False

    @classmethod
    def from_dict(cls, dict_config):
        """Get a matching zone object for a configuration stored in a dict."""
        try:
            # select right zone class by driver name
            name = dict_config["driver"]["name"]
            if name == "digitalocean":
                return DigitalOceanZone.from_dict(dict_config)
            elif name == "libvirt":
                return LibvirtZone.from_dict(dict_config)
            else:
                raise UnknownDriverError("Unknown driver: " + name)
        except KeyError as expt:
            print dict_config
            raise InvalidZoneConfigError(
                "Invalid zone configuration: " + expt.message)

    def __init__(self, url, create):
        self.url = url
        self.create = create

    def machines(self):
        """This is not implemented here."""
        raise Exception("There are no exceptions, only happy little mistakes.")


class LibvirtVMHost(object):
    """Libvirt VM Host definition."""

    @classmethod
    def from_dict(cls, dict_host):
        """Return a LibvirtVMHost object from a dictionary definition."""
        return LibvirtVMHost(dict_host["name"], dict_host["user"])

    def __init__(self, name, user):
        self.name = name
        self.user = user

    def uri(self):
        """Return an uri for usage with libcloud."""
        return 'qemu+ssh://' + self.user + '@' + self.name + '/system'


class LibvirtZone(Zone):
    """Implements crawling libvirt hosts for vm nodes."""

    @classmethod
    def from_dict(cls, dict_config):
        hosts = LibvirtZone.hosts_from_dict(dict_config["hosts"])
        return LibvirtZone(dict_config["url"], dict_config["create"], hosts)

    @classmethod
    def hosts_from_dict(cls, dict_hosts):
        """Return a list of LibvirtVMHost objects from a dictionary definition."""
        hosts = []
        for host in dict_hosts:
            hosts.append(LibvirtVMHost.from_dict(host))
        return hosts

    def __init__(self, url, create, hosts):
        super(LibvirtZone, self).__init__(url, create)
        self.hosts = hosts

    def machines(self):
        idb_machines = []

        for host in self.hosts:
            driver = libcloud.compute.providers.get_driver(
                libcloud.compute.types.Provider.LIBVIRT)(uri=host.uri())

            nodes = driver.list_nodes()
            for node in nodes:
                idb_machines.append(IDBMachine(
                    self.create, node.name, driver.ex_get_hypervisor_hostname()))

        return idb_machines


class DigitalOceanZone(Zone):

    @classmethod
    def from_dict(cls, dict_config):
        return DigitalOceanZone(dict_config["url"], dict_config["create"], dict_config["driver"]["token"], dict_config["driver"]["version"])

    def __init__(self, url, create, token, version):
        super(DigitalOceanZone, self).__init__(url, create)
        self.token = token
        self.version = version

    def machines(self):
        idb_machines = []

        driver = libcloud.compute.providers.get_driver(
            libcloud.compute.types.Provider.DIGITAL_OCEAN)(self.token, api_version=self.version)

        nodes = driver.list_nodes()
        for node in nodes:
            idb_machines.append(IDBMachine(
                self.create, node.name, ""))

        return idb_machines


class IDBMachine(object):
    """IDB Machine object"""

    def __init__(self, create, fqdn, vmhost):
        self.fqdn = fqdn
        self.vmhost = vmhost
        self.device_type_id = 2
        self.create = create

    def dict(self):
        """Returns the machine informations as a dictionary."""
        return {"create": self.create, "fqdn": self.fqdn, "vmhost": self.vmhost,
                "device_type_id": self.device_type_id}


class IDBLibvirt(object):

    @classmethod
    def get_config(cls, url, token):
        """Load config for this adapter from the idb."""
        res = requests.get(url + "/cloud_providers",
                           headers={"X-IDB-API-Token": token})
        res.raise_for_status()
        return res.json()

    @classmethod
    def zones_from_dict(cls, json_config):
        """Create zones from json configuration."""
        zones = []
        for zone in json_config["zones"]:
            zones.append(Zone.from_dict(zone))

        return zones

    @classmethod
    def machines(cls, zones):
        machines = []
        for zone in zones:
            machines = machines + zone.machines()

    @classmethod
    def json_machines(cls, machines):
        return json.dumps({"machines": [x.dict() for x in machines]})

    @classmethod
    def submit_machines(cls, url, token, json_machines):
        requests.put(url + "machines",
                     headers={
                         "X-IDB-API-Token": token,
                         "Content-Type": "application/json"
                     }, data=json_machines)

    def run(self):
        json_config = IDBLibvirt.get_config(self.url, self.token)
        zones = IDBLibvirt.zones_from_dict(json_config)
        machines = IDBLibvirt.machines(zones)
        json_machines = IDBLibvirt.json_machines(machines)
        IDBLibvirt.submit_machines(self.url, self.token, json_machines)

    def __init__(self, url, token):
        self.url = url
        self.token = token

if __name__ == "__main__":
    pass
