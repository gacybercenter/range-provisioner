from setuptools import find_packages, setup

setup(
    name='provisioner',
    version='1.0',
    python_requires='>=3.10',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    py_modules=['provisioner'],
    install_requires=[
        'guacamole-api-wrapper',
        'openstacksdk',
        'requests',
        'pyyaml',
        'jinja2',
        'colorama',
    ],
    entry_points={
        'console_scripts': [
            'provisioner=provisioner:main',
            'range-provisioner=provisioner:main',
        ],
    },
)