from setuptools import setup, find_packages

VERSION = '0.5.0'
DESCRIPTION = 'Get satellite images time series'
LONG_DESCRIPTION = 'Create satellite time-series patches from STAC catalogs'

setup(
    name='SITS',
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    url='https://github.com/kenoz/SITS_utils',
    author='Kenji Ose',
    author_email='kenji.ose@ec.europa.eu',
    install_requires=[],
    keywords=['python', 'sits', 'satellite', 'time series', 'STAC'],
    packages=find_packages(),
    classifiers=[
            "Development Status :: 3 - Alpha",
            "Intended Audience :: Education",
            "Programming Language :: Python :: 2",
            "Programming Language :: Python :: 3",
            "Operating System :: MacOS :: MacOS X",
            "Operating System :: Microsoft :: Windows",
        ]
)
