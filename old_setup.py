from setuptools import setup, find_packages

# Function to parse requirements.txt
def parse_requirements(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip() and not line.startswith('#')]

VERSION = '0.6.3'
DESCRIPTION = 'Get satellite images time series'
LONG_DESCRIPTION = 'Create satellite time-series patches from STAC catalogs'
REQUIREMENTS = parse_requirements('requirements.txt')

setup(
    name='sits',
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    url='https://github.com/kenoz/SITS_utils',
    author='Kenji Ose',
    author_email='kenji.ose@ec.europa.eu',
    install_requires=REQUIREMENTS,
    extras_require={'dev': parse_requirements('requirements-dev.txt')},
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
