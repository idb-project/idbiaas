from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="idbiaas",
    version="0.0.1",
    description="IDB IAAS adapter",
    long_description=read('README.md'),
    packages=["idbiaas"],
    install_requires=["requests","apache-libcloud"],
    entry_points = { 'console_scripts': ['idbiaas=idbiaas.idbiaas:main'] }
)
