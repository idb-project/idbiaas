import unittest
import libcloud.compute.types

import idbiaas

do_zone_config = {
    "idb": {
        "url": "http://example.org",
        "token": "idbtoken",
        "create": False
    },
    "driver": {
        "name":  libcloud.compute.types.Provider.DIGITAL_OCEAN,
        "token": "testtoken",
        "version": "v2"
    }
}

libvirt_zone_config = {
    "idb":{
        "url": "http://example.org",
        "token": "idbtoken",
        "create": False
    },
    "driver": {
        "name": libcloud.compute.types.Provider.LIBVIRT,
        "hosts": [{
            "name": "host0.example.org",
            "user": "testuser"
            },
            {
            "name": "host1.example.org",
            "user": "testuser"
            }
        ]
    }
}

class ZoneTest(unittest.TestCase):

    def test_from_dict_digitalocean(self):
        x = idbiaas.Zone.from_dict(do_zone_config)
        self.assertIsInstance(x, idbiaas.DigitalOceanZone)
        self.assertEqual(x.token, "testtoken")
        self.assertEqual(x.version, "v2")

    def test_from_dict_libvirt(self):
        x = idbiaas.Zone.from_dict(libvirt_zone_config)
        self.assertIsInstance(x, idbiaas.LibvirtZone)
        self.assertEqual(len(x.hosts), 2)
        self.assertEqual(x.hosts[0].name, "host0.example.org")
        self.assertEqual(x.hosts[0].user, "testuser")
        self.assertEqual(x.hosts[1].name, "host1.example.org")
        self.assertEqual(x.hosts[1].user, "testuser")


class LibvirtZoneTest(unittest.TestCase):
    def test_from_dict(self):
        x = idbiaas.LibvirtZone.from_dict(libvirt_zone_config["driver"])
        self.assertIsInstance(x, idbiaas.LibvirtZone)
        self.assertEqual(len(x.hosts), 2)
        self.assertEqual(x.hosts[0].name, "host0.example.org")
        self.assertEqual(x.hosts[0].user, "testuser")
        self.assertEqual(x.hosts[1].name, "host1.example.org")
        self.assertEqual(x.hosts[1].user, "testuser")

    def test_hosts_from_dict(self):
        x = idbiaas.LibvirtZone.hosts_from_dict(libvirt_zone_config["driver"]["hosts"])
        self.assertIsInstance(x, list)
        self.assertEqual(len(x), 2)


if __name__ == '__main__':
    unittest.main()
