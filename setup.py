# Copyright (c) 2010 VMware, Inc. All Rights Reserved.

# This file is part of PyATOM.

# PyATOM is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the Free
# Software Foundation version 2 and no later version.

# PyATOM is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License version 2
# for more details.

# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# St, Fifth Floor, Boston, MA 02110-1301 USA.

from distutils.core import setup, Extension
import os

def read(fname):
   '''Returns the contents of the specified file located in the same dir as
      the script
   '''
   return open(os.path.join(os.path.dirname(__file__), fname)).read()

source_files = [
   'pyatom/_a11y/a11ymodule.c',
   'pyatom/_a11y/conversion.c',
   'pyatom/_a11y/axlib.c',
]

_a11y = Extension(
   'pyatom._a11y',
   sources = source_files,
   extra_link_args = [
      '-framework', 'ApplicationServices',
      '-framework', 'Carbon',
   ],
)

setup (
   name = 'atom',
   version = '0.9',
   author = 'The PyATOM Team',
   author_email = 'pyatom-dev@lists.pyatom.com',
   url = 'http://pyatom.com',
   description = ("Automated Testing on Mac - test GUI applications "
                  "written in Cocoa by using Apple's Accessibility API"),
   license = 'GPLv2',
   long_description = read('README.rst'),
   ext_modules = [_a11y],
   packages = ['pyatom'],
   classifiers = [
      'Development Status :: 5 - Production/Stable',
      'Environment :: MacOS X :: Cocoa',
      'License :: OSI Approved :: GNU General Public License (GPL)',
      'Topic :: Software Development :: Quality Assurance',
      'Topic :: Software Development :: Testing',
   ],
)
