from setuptools import setup

setup(
    name="idbiaas",
    version="0.0.1",
    description="IDB IAAS adapter",
    packages=["idbiaas"],
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
