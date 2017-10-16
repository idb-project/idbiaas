# idbiaas

Adapter to read various sources supported by apache-libcloud and submit them to a IDB instance.

## Installation

If you are not root, create a virtualenv and activate it

	virtualenv venv
	. venv/bin/activate

Install idbiaas by running pip install

	pip install .

After these steps, you should have the `idbiaas` command installed in your virtualenv.

## Usage

Running idbiaas requires a configuration specifing zones to query information for. This configuration
could either be loaded from a local file, or remotely from a IDB instance.

### Remote Configuration 

To use a configuation stored in a IDB, run idbiaas with the `--url` and `--token` arguments:

	idbiaas --v2-url https://idb.example.org/api/v2 --token idb_api_token

or with API v3:

	idbiaas --v3-url https://idb.example.org/api/v3 --token idb_api_token --config-name myconfig

If the IDB instance has a self-signed certificate, you can use the `--no-verify` switch to disable
certificate checks.

### Local Configuration

To load a local configuration use the --config switch:

	idbiaas --config idbiaas_config.json

### Configuration

A idbiaas configuration is stored as JSON. The root object is an object with one field "zones".
The value of "zones" is an array consisting of zone objects.

#### Zone configuration

A zone object has thes keys:

- `idb`: IDB configuration
- `driver`: Driver configuration

#### IDB configuration

A IDB configuration object has these keys:

- `url`: URL where the IDB API is reached, eg. https://idb.example.org/api/v2
- `version`: API version to use, `2` or `3` (integer)
- `token`: IDB API token
- `create`: set to true to create nonexisting machines in the IDB

#### Driver configuration

The contents of a driver configuration object depend on which backend is used.
Currently supported are digital ocean and libvirt.

##### Digital Ocean

- `name`: digitalocean
- `token`: digital ocean api token
- `version`: digital ocean api version

Example:

	{
		"name":"digitalocean",
		"token":"digitalocean_api_token",
		"version": "v2"
	}

##### libvirt

- `name`: libvirt
- `hosts`: array of hosts to query

Example:

	{
		"name": "libvirt",
		"hosts": [
			{
			"name": "libvirt.example.org",
			"user": "libvirt"
			}
		]
	}

###### libvirt hosts

- `name`: fqdn or ip of libvirt host
- `user`: user to connect as

Example:

	{
		"name": "libvirt.example.org",
		"user": "libvirt"
	}

#### Example configuration

	{
		"zones": [
			{
				"idb": {
					"url": "https://idb.example.org/api/v2",
					"token": "idb_api_token",
					"create": true
				},
				"driver": 	{
					"name":"digitalocean",
					"token":"digitalocean_api_token",
					"version": "v2"
				}
			},
			{
				"idb": {
					"url": "https://idb.example.org/api/v2",
					"token": "idb_api_token",
					"create": true
				},
				"driver": {
					"name": "libvirt",
					"hosts": [
						{
						"name": "libvirt.example.org",
						"user": "libvirt"
						}
					]
				}
			}
		]
	}