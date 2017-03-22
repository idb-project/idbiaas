from setuptools import setup, find_packages

setup(
    name="idbiaas",
    version="0.0.1",
    description="IDB IAAS adapter",
    packages=["idbiaas"],
    install_requires=["requests","apache-libcloud"],
    entry_points = { 'console_scripts': ['idbiaas=idbiaas.idbiaas:main'] }
)
