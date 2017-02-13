import unittest
import libcloud.compute.types

import idbiaas


class ZoneTest(unittest.TestCase):

    def test_from_dict_digitalocean(self):
        d = {
            "url": "http://example.org",
            "token": "idbtoken",
            "create": False,
            "driver": {
                "name":  libcloud.compute.types.Provider.DIGITAL_OCEAN,
                "token": "testtoken",
                "version": "v2"
            }
        }

        x = idbiaas.Zone.from_dict(d)
        self.assertIsInstance(x, idbiaas.DigitalOceanZone)
        self.assertEqual(x.dotoken, "testtoken")
        self.assertEqual(x.version, "v2")

    def test_from_dict_libvirt(self):
        d = {
            "url": "http://example.org",
            "token": "idbtoken",
            "create": False,
            "driver": {
                "name": libcloud.compute.types.Provider.LIBVIRT,
            },
            "hosts": [{
                "name": "host.example.org",
                "user": "testuser"
            }]
        }

        x = idbiaas.Zone.from_dict(d)
        self.assertIsInstance(x, idbiaas.LibvirtZone)
        self.assertEqual(len(x.hosts), 1)
        self.assertEqual(x.hosts[0].name, "host.example.org")
        self.assertEqual(x.hosts[0].user, "testuser")


class LibvirtZoneTest(unittest.TestCase):

    def test_from_dict(self):
        d = {
            "url": "http://example.org",
            "token": "idbtoken",
            "create": False,
            "driver": {
                "name": libcloud.compute.types.Provider.LIBVIRT,
            },
            "hosts": [{
                "name": "host.example.org",
                "user": "testuser"
            }]
        }

        x = idbiaas.LibvirtZone.from_dict(d)
        self.assertIsInstance(x, idbiaas.LibvirtZone)
        self.assertEqual(len(x.hosts), 1)
        self.assertEqual(x.hosts[0].name, "host.example.org")
        self.assertEqual(x.hosts[0].user, "testuser")

    def test_hosts_from_dict(self):
        d = [{
            "name": "host0.example.org",
            "user": "testuser0"
        }, {
            "name": "host1.example.org",
            "user": "testuser1"
        }]

        x = idbiaas.LibvirtZone.hosts_from_dict(d)
        self.assertIsInstance(x, list)
        self.assertEqual(len(x), 2)


if __name__ == '__main__':
    unittest.main()
