#! /usr/bin/env python3

import os

try:
    from setuptools import find_packages, setup
except AttributeError:
    from setuptools import find_packages, setup

NAME = 'OASYS2-XOPPY'
VERSION = '1.0.4'
ISRELEASED = False

DESCRIPTION = 'XOPPY: XOP (X-ray oriented programs) in Python'
README_FILE = os.path.join(os.path.dirname(__file__), 'README.txt')
LONG_DESCRIPTION = open(README_FILE).read()
AUTHOR = 'Manuel Sanchez del Rio, Luca Rebuffi, and Bioinformatics Laboratory, FRI UL'
AUTHOR_EMAIL = 'srio@esrf.eu, lrebuffi@anl.gov'
URL = 'https://github.com/oasys-kit/XOPPY'
DOWNLOAD_URL = 'https://github.com/oasys-kit/XOPPY'
LICENSE = 'GPLv3'

KEYWORDS = [
    'X-ray optics',
    'simulator',
    'oasys2',
]

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: X11 Applications :: Qt',
    'Environment :: Console',
    'Environment :: Plugins',
    'Programming Language :: Python :: 3',
    'Intended Audience :: Science/Research',
]

SETUP_REQUIRES = (
    'setuptools',
)

INSTALL_REQUIRES = (
    'oasys2>=0.0.7',
    'xoppylib>=1.0.43',
)

PACKAGES = find_packages(exclude=('*.tests', '*.tests.*', 'tests.*', 'tests'))

PACKAGE_DATA = {
    "orangecontrib.xoppy.widgets.source":["icons/*.png", "icons/*.jpg"],
    "orangecontrib.xoppy.widgets.optics":["icons/*.png", "icons/*.jpg", "misc/*.*"],
}

ENTRY_POINTS = {
    'oasys2.addons' : ("xoppy = orangecontrib.xoppy", ),
    'oasys2.widgets' : (
        "XOPPY Sources = orangecontrib.xoppy.widgets.source",
        "XOPPY Optics = orangecontrib.xoppy.widgets.optics",
    ),
}

if __name__ == '__main__':
    setup(
          name = NAME,
          version = VERSION,
          description = DESCRIPTION,
          long_description = LONG_DESCRIPTION,
          author = AUTHOR,
          author_email = AUTHOR_EMAIL,
          url = URL,
          download_url = DOWNLOAD_URL,
          license = LICENSE,
          keywords = KEYWORDS,
          classifiers = CLASSIFIERS,
          packages = PACKAGES,
          package_data = PACKAGE_DATA,
          setup_requires = SETUP_REQUIRES,
          install_requires = INSTALL_REQUIRES,
          entry_points = ENTRY_POINTS,
          include_package_data = True,
          zip_safe = False,
          )

