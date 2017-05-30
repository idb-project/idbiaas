from setuptools import setup

setup(
    name="idbiaas",
    version="0.0.3",
    description="IDB IAAS adapter",
    packages=["idbiaas"],
    author="bytemine GmbH",
    author_email="schuller@bytemine.net",
    url="https://github.com/idb-project/idbiaas",
    install_requires=[
        "requests",
        "apache-libcloud",
        "appdirs",
        "argparse",
        "asn1crypto",
        "backports.ssl-match-hostname",
        "cffi",
        "cryptography",
        "enum34",
        "idna",
        "ipaddress",
        "libvirt-python",
        "packaging",
        "pyOpenSSL",
        "pycparser",
        "pyparsing",
        "six",
        "wsgiref"
        ],
    entry_points={'console_scripts':['idbiaas=idbiaas.idbiaas:main']}
)
