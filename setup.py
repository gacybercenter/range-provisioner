from setuptools import setup

setup(
    name='provisioner',
    version='1.0',
    entry_points={
        'console_scripts': [
            'provisioner=provisioner:main',
        ],
    },
)