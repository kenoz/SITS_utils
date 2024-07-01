from setuptools import setup, find_packages

setup(
    name='SITS',
    version='0.1',
    url='https://github.com/kenoz/SITS_utils',
    author='Kenji Ose',
    author_email='kenji.ose@ec.europa.eu',
    description='Create satellite time-series patches from STAC catalogs',
    packages=find_packages(),    
    install_requires=[],
)
