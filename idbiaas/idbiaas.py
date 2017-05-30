#! /usr/bin/env python
"""IDB infrastructure-as-a-service (iaas) adapter"""

import logging
import argparse
import json
import itertools

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

        idb = None
        try:
            idb = IDB.from_dict(dict_config["idb"])
        except KeyError as expt:
            raise InvalidZoneConfigError("Invalid zone configuration: " + expt.message)

        zone = None
    
        try:
            # select right zone class by driver name
            name = dict_config["driver"]["name"]
            if name == "digitalocean":
                zone = DigitalOceanZone.from_dict(dict_config["driver"])
            elif name == "libvirt":
                zone = LibvirtZone.from_dict(dict_config["driver"])
            else:
                raise UnknownDriverError("Unknown driver: " + name)
        except KeyError as expt:
            raise InvalidZoneConfigError(
                "Invalid zone configuration: " + expt.message)

        zone.idb = idb
        
        return zone

    @property
    def idb(self):
        return self._idb

    @idb.setter
    def idb(self, idb):
        self._idb = idb


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

        return LibvirtZone(hosts)

    @classmethod
    def hosts_from_dict(cls, dict_hosts):
        """Return a list of LibvirtVMHost objects from a dictionary definition."""
        hosts = []
        for host in dict_hosts:
            hosts.append(LibvirtVMHost.from_dict(host))
        return hosts

    def __init__(self, hosts):
        self.hosts = hosts

    def machines(self):
        idb_machines = []

        for host in self.hosts:
            logging.info("LibvirtZone: retrieving nodes from %s", host.uri())

            try:
                driver = libcloud.compute.providers.get_driver(
                    libcloud.compute.types.Provider.LIBVIRT)(uri=host.uri())

                nodes = driver.list_nodes()
                for node in nodes:
                    logging.debug("LibvirtZone: got node %s", node)
                    idb_machines.append(IDBMachine(
                        node.name, driver.ex_get_hypervisor_hostname(),
                        node.extra['vcpu_count'], node.extra['used_memory']))
            except Exception as e:
                logging.error("LibvirtZone: %s, continuing with next host", e)

        return idb_machines


class DigitalOceanZone(Zone):

    @classmethod
    def from_dict(cls, dict_config):
        return DigitalOceanZone(dict_config["token"], dict_config["version"])

    def __init__(self, token, version):
        self.token = token
        self.version = version

    def machines(self):
        logging.info("DigitalOceanZone: retrieving nodes")
        idb_machines = []

        try:
            driver = libcloud.compute.providers.get_driver(
                libcloud.compute.types.Provider.DIGITAL_OCEAN)(self.token, api_version=self.version)

            nodes = driver.list_nodes()
            for node in nodes:
                logging.debug("DigitalOceanZone: got node %s", node)
                idb_machines.append(IDBMachine(node.name, "", node.extra["vcpus"], node.extra["memory"]))
        except Exception as e:
            logging.error("DigitalOceanZone: %s, continuing with next host", e)

        return idb_machines


class IDBMachine(object):
    """IDB Machine object"""

    def __init__(self, fqdn, vmhost, cpu, ram):
        self.fqdn = fqdn
        self.vmhost = vmhost
        self.device_type_id = 2
        self.cpu = cpu
        self.ram = ram

    def dict(self):
        """Returns the machine informations as a dictionary."""
        return {"fqdn": self.fqdn, "vmhost": self.vmhost,
                "device_type_id": self.device_type_id,
                "cores": self.cpu, "ram": self.ram}


class IDB(object):
    """IDB API"""

    @classmethod
    def from_dict(cls,dict_config):
        create = False
        verify = True
        chunksize = 10
        if dict_config.has_key("create"):
            create = dict_config["create"]
        
        if dict_config.has_key("verify"):
            verify = dict_config["verify"]

        if dict_config.has_key("chunksize"):
            chunksize = dict_config["chunksize"]

        return IDB(dict_config["url"], dict_config["token"],create,verify,chunksize)

    def __init__(self, url, token, create=False, verify=True, chunksize=10):
        self.url = url
        self.token = token
        self.create = create
        self.verify = verify
        self.chunksize = chunksize

    # group items of an iterable into chunks of size n
    # http://stackoverflow.com/a/434411
    def grouper(self, iterable, n, fillvalue=None):
        args = [iter(iterable)] * n
        return itertools.izip_longest(*args, fillvalue=fillvalue)

    def json_machines(self, machines):
        """Converts machines list to IDB compatible json."""
        return json.dumps({"create_machine": self.create, "machines": [x.dict() for x in machines if x != None]})

    def submit_machines(self, machines):
        """Submit machines to the IDB."""

        logging.info("Sending machines in zone %s to IDB API at %s",
                     self.__class__.__name__, self.url)

        for machines_chunk in self.grouper(machines, 2):
            json_machines = self.json_machines(machines_chunk)

            req = requests.Request("PUT", self.url + "/machines", headers={
                "X-IDB-API-Token": self.token,
                "Content-Type": "application/json"
            }, data=json_machines)

            prepared = req.prepare()

            logging.debug("{} {}\n{}\n{}".format(prepared.method, prepared.url,
                                                '\n'.join('{}: {}'.format(k, v) for k, v in prepared.headers.items()),
                                                prepared.body))

            s = requests.Session()
            s.verify = self.verify
            res = s.send(prepared)

            logging.debug("%s\n%s", res.status_code, res.text.encode('utf-8'))


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
            zone.idb.submit_machines(machines)

    def run(self):
        zones = IDBIaas.zones_from_dict(self.config)
        self.run_zones(zones)

    def __init__(self, config):
        self.config = config


def main():
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
    parser.add_argument('--verify', dest='verify', action='store_true', help="Verify SSL certificate chain when retrieving config")
    parser.add_argument('--no-verify', dest='verify', action='store_false', help="Don't verify SSL certificate chain when retrieving config")

    logging_group = parser.add_mutually_exclusive_group()
    logging_group.add_argument("--critical", action='store_const', dest='loglevel', const=logging.CRITICAL, help="Log critical errors.")
    logging_group.add_argument("--error", action='store_const', dest='loglevel', const=logging.ERROR, help="Log errors and above")
    logging_group.add_argument("--warning", action='store_const', dest='loglevel', const=logging.WARNING, help="Log warnings and above")
    logging_group.add_argument("--info", action='store_const', dest='loglevel', const=logging.INFO, help="Log informational messages and above")
    logging_group.add_argument("--debug", action='store_const', dest='loglevel', const=logging.DEBUG, help="Log debug information and above")
    parser.set_defaults(loglevel=logging.WARNING)

    args = parser.parse_args()

    logging.basicConfig(level=args.loglevel)

    config = None
    if args.url:
        logging.info("Fetching config from %s", args.url)
        config = IDBIaas.url_config(args.url, args.token, args.verify)
    elif args.config:
        logging.info("Using config file %s", args.config.name)
        config = IDBIaas.file_config(args.config)
    else:
        logging.critical("No url or file config.")
        return

    idbiaas = IDBIaas(config)
    idbiaas.run()


if __name__ == "__main__":
    main()
