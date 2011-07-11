#!/bin/bash

# If you did a sudo python setup.py install, you may need to remove some
# directories first - dist, build, and atomac.egg-info
python setup.py register
python setup.py sdist upload --sign
python setup.py bdist_egg upload --sign

