from setuptools import find_packages, setup

setup(
    name='prismasyncjmfjdf',
    packages=find_packages(include=['prismasyncjmfjdf']),
    version='0.1.2',
    description='Python library for PRISMAsync jmfjdf queries and commands',
    author='Dries Dokter',
    package_data={"prismasyncjmfjdf": ["*.jmf", "*.jdf", "*.pdf"]},
    include_package_data=True,
    install_requires=['requests', 'base64io', 'pathlib'],
)