#!/bin/bash

python setup.py register
python setup.py sdist upload --sign
python setup.py bdist_egg upload --sign

