# Copyright (c) 2012 VMware, Inc. All Rights Reserved.

# This file is part of ATOMac.

#@author: Eitan Isaacson <eitan@ascender.com>
#@author: Nagappan Alagappan <nagappan@gmail.com>
#@copyright: Copyright (c) 2009 Eitan Isaacson
#@copyright: Copyright (c) 2009-12 Nagappan Alagappan

#http://ldtp.freedesktop.org

# ATOMac is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by the Free
# Software Foundation version 2 and no later version.

# ATOMac is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License version 2
# for more details.

# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# St, Fifth Floor, Boston, MA 02110-1301 USA.
"""Log routines for LDTP"""

from os import environ as env
import logging

AREA = 'ldtp.client'
ENV_LOG_LEVEL = 'LDTP_LOG_LEVEL'
ENV_LOG_OUT = 'LDTP_LOG_OUT'

log_level = getattr(logging, env.get(ENV_LOG_LEVEL, 'NOTSET'), logging.NOTSET)

logger = logging.getLogger(AREA)

if ENV_LOG_OUT not in env:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter('%(name)-11s %(levelname)-8s %(message)s'))
else:
    handler = logging.FileHandler(env[ENV_LOG_OUT])
    handler.setFormatter(
        logging.Formatter('%(asctime)s %(levelname)-8s %(message)s'))

logger.addHandler(handler)

logger.setLevel(log_level)
