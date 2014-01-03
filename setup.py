try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'Convert MAPS HDF5 files to Scientific Data Exchange format',
    'author': 'David J. Vine',
    'url': 'github.com/djvine/maps_data_exchange.',
    'download_url': 'Where to download it.',
    'author_email': 'djvine@gmail.com',
    'version': '0.1',
    'install_requires': ['nose, data_exchange'],
    'packages': ['maps_data_exchange'],
    'scripts': [],
    'name': 'maps_data_exchange'
}

setup(**config)
