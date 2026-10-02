from setuptools import setup, find_packages

setup(
    name="range-provisioner",
    version="2.0.0",
    description="Cyber Range Orchestration Platform for OpenStack Heat, Swift, and Apache Guacamole",
    author="Marcus Corulli",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.html", "*.sh"],
        "src.web": ["templates/*.html"],
    },
    install_requires=[
        "openstacksdk>=4.0.0",
        "guacamole-api-wrapper>=0.1.0",
        "requests>=2.28.0",
        "pyyaml>=6.0",
        "jinja2>=3.1.0",
        "colorama>=0.4.6",
        "click>=8.0.0",
        "rich>=13.0.0",
        "fastapi>=0.110.0",
        "uvicorn[standard]>=0.28.0",
        "pydantic>=2.5.0",
        "python-multipart>=0.0.9",
        "aiofiles>=23.0.0",
        "sqlalchemy>=2.0.0",
        "pyjwt>=2.8.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-cov>=4.0.0",
            "httpx>=0.27.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "range-provisioner=src.cli:cli",
            "provisioner=src.cli:cli",
        ],
    },
)