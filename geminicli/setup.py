from setuptools import setup, find_packages

setup(
    name="geminicli",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click",
        "httpx",
        "pyyaml",
    ],
    entry_points={
        "console_scripts": [
            "geminicli = geminicli.main:cli",
        ],
    },
)
