from setuptools import setup

setup(
    name="idbiaas",
    version="0.0.7",
    description="IDB IAAS adapter",
    packages=["idbiaas"],
    author="bytemine GmbH",
    author_email="schuller@bytemine.net",
    url="https://github.com/idb-project/idbiaas",
    install_requires=[
        "apache-libcloud",
        "appdirs",
        "asn1crypto",
        "backports.ssl-match-hostname",
        "certifi",
        "cffi",
        "chardet",
        "cryptography",
        "enum34",
        "idbiaas",
        "idna",
        "ipaddress",
        "libvirt-python",
        "packaging",
        "pycparser",
        "pyOpenSSL",
        "pyparsing",
        "requests",
        "six",
        "urllib3"
    ],
    entry_points={'console_scripts':['idbiaas=idbiaas.idbiaas:main']}
)
