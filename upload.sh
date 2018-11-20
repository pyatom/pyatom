#!/bin/bash

# If you did a sudo python setup.py install, you may need to remove some
# directories first - dist, build, and atomac.egg-info
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
sudo rm -rf $DIR/dist
sudo rm -rf $DIR/build
sudo rm -rf $DIR/atomac.egg-info

python setup.py register
python setup.py sdist upload --sign
python setup.py bdist_wheel upload --sign

