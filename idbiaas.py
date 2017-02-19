#! /usr/bin/env python
"""IDB infrastructure-as-a-service (iaas) adapter"""

import logging
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
    def verifies(cls, dict_config):
        """Verify returns the value of the "verify" key, or True if it doesn't exist."""
        if dict_config.has_key("verify") and dict_config["verify"] is False:
            return False
        
        return True

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
            raise InvalidZoneConfigError(
                "Invalid zone configuration: " + expt.message)

    def __init__(self, url, token, create, verify):
        self.url = url
        self.token = token
        self.create = create
        self.verify = verify

    def submit_machines(self, machines):
        """Submit machines to the IDB."""
        json_machines = self.json_machines(machines)
        logging.info("Sending machines in zone %s to IDB API at %s",
                     self.__class__.__name__, self.url)

        req = requests.Request("PUT", self.url + "/machines", headers={
            "X-IDB-API-Token": self.token,
            "Content-Type": "application/json"
        }, data=json_machines)

        prepared = req.prepare()

        logging.info("{} {}\n{}\n{}".format(prepared.method, prepared.url,
                                            '\n'.join('{}: {}'.format(k, v) for k, v in prepared.headers.items()),
                                            prepared.body))

        s = requests.Session()
        s.verify = self.verify
        res = s.send(prepared)

        logging.info("{}\n{}".format(res.status_code, res.text))

    def json_machines(self, machines):
        """Converts machines list to IDB compatible json."""
        return json.dumps({"create_machine": self.create, "machines": [x.dict() for x in machines]})

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

        return LibvirtZone(dict_config["url"], dict_config["token"],
                           dict_config["create"], Zone.verifies(dict_config), hosts)

    @classmethod
    def hosts_from_dict(cls, dict_hosts):
        """Return a list of LibvirtVMHost objects from a dictionary definition."""
        hosts = []
        for host in dict_hosts:
            hosts.append(LibvirtVMHost.from_dict(host))
        return hosts

    def __init__(self, url, token, create, verify, hosts):
        super(LibvirtZone, self).__init__(url, token, create, verify)
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

        return DigitalOceanZone(dict_config["url"], dict_config["token"],
                                dict_config["create"], Zone.verifies(dict_config),
                                dict_config["driver"]["token"],
                                dict_config["driver"]["version"])

    def __init__(self, url, idbtoken, create, verify, dotoken, version):
        super(DigitalOceanZone, self).__init__(url, idbtoken, create, verify)
        self.dotoken = dotoken
        self.version = version

        logging.info("IDBTOKEN:" + idbtoken)
        logging.info("TOKEN:" + dotoken)

    def machines(self):
        idb_machines = []

        driver = libcloud.compute.providers.get_driver(
            libcloud.compute.types.Provider.DIGITAL_OCEAN)(self.dotoken, api_version=self.version)

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
#        self.create = create

    def dict(self):
        """Returns the machine informations as a dictionary."""
        return {"fqdn": self.fqdn, "vmhost": self.vmhost,
                "device_type_id": self.device_type_id}


class IDBIaas(object):

    # BUG: This doesn't work currently (needs some changes in idb api).
    @classmethod
    def url_config(cls, url, token, verify):
        """Load config for this adapter from the idb."""
        res = requests.get(url + "/cloud_providers",
                           headers={"X-IDB-API-Token": token}, verify=verify)
        res.raise_for_status()
        return json.loads(res.json()[0]["config"])

    @classmethod
    def file_config(cls, fil):
        """Load config for this adapter from a local file."""
        dict_config = json.load(fil)
        return dict_config

    @classmethod
    def zones_from_dict(cls, dict_config):
        """Create zones from dict configuration."""
        zones = []
        for zone in dict_config["zones"]:
            zones.append(Zone.from_dict(zone))

        return zones

    @classmethod
    def run_zones(cls, zones):
        for zone in zones:
            machines = zone.machines()
            logging.info("Found machines in zone %s:", zone.__class__.__name__)
            for machine in machines:
                logging.info(machine.fqdn)
            zone.submit_machines(machines)

    def run(self):
        zones = IDBIaas.zones_from_dict(self.config)
        self.run_zones(zones)

    def __init__(self, config):
        self.config = config


def main():
    logging.basicConfig(level=10)
    parser = argparse.ArgumentParser(description='Update virtual machines to the IDB.')
    config_source_group = parser.add_mutually_exclusive_group(required=True)
    config_source_group.add_argument("--url", action="store", type=str,
                                     help="base url of the IDB API ",
                                     default=None)
    parser.add_argument("--token", action="store",
                        type=str, help="IDB API token",
                        default="my_super_secret_token")
    config_source_group.add_argument("--config", action="store",
                                     type=file, help="local configuration file")
    parser.add_argument("--verify", type=bool, default=True)
    args = parser.parse_args()

    config = None
    if args.url:
        logging.info("Fetching config from %s", args.url)
        config = IDBIaas.url_config(args.url, args.token, args.verify)
    elif args.config:
        logging.info("Using config file %s", args.config.name)
        config = IDBIaas.file_config(args.config)
    else:
        logging.error("No url or file config.")

    idbiaas = IDBIaas(config)
    idbiaas.run()


if __name__ == "__main__":
    main()
