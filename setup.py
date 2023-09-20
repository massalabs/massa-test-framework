from setuptools import setup, find_packages

VERSION = '0.0.1'
DESCRIPTION = 'Massa test framework'
LONG_DESCRIPTION = 'A framework for Massa core dev to develop functional tests'

# Setting up
setup(
    name="massa_test_framework",
    version=VERSION,
    author="sd",
    author_email="<sd@massa.net>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[
        "paramiko==3.2",
        "requests==2.31",
        "tomlkit==0.11",
        "base58==2.1",
        "blake3==0.3",
        "varint==1.0.2",
        "ed25519==1.5",
        "patch-ng==1.17.4",
        # "betterproto==2.0.0b5",
        "massa-proto-python==0.0.1"
    ],  # add any additional packages that
    # needs to be installed along with your package. Eg: 'caer'
    keywords=['python'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
    ]
)
