# Copyright (c) 2012 VMware, Inc. All Rights Reserved.

# This file is part of ATOMac.

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
"""Utils class."""

import re
import atomac
import fnmatch

from constants import abbreviated_roles

class Utils:
    def __init__(self):
        # FIXME: Currently this is not updated at run-time
        # Current opened applications list will be returned
        self._running_apps = atomac.NativeUIElement._getApps()

    def _ldtpize_accessible(self, acc):
        """
        Get LDTP format accessibile name

        @param acc: Accessible handle
        @type acc: object

        @return: object type, stripped object name (associated / direct),
                        associated label
        @rtype: tuple
        """
        role = self._get_role(acc)
        if re.match("AXWindow", role, re.M | re.U | re.L):
            label = self._get_window_title(acc)
            # Strip space and new line from window title
            strip = r'( |\n)'
        else:
            label = self._get_value(acc)
            # Strip space, colon, dot, underscore and new line from
            # all other object types
            strip = r'( |:|\.|_|\n)'
        if label:
            # Return the role type (if, not in the know list of roles,
            # return ukn - unknown), strip the above characters from name
            # also return labely_by string
            if not isinstance(label, unicode):
                label = u'%s' % label
            print label, role, strip, isinstance(label, unicode)
            label = re.sub(strip, '', label)
        return abbreviated_roles.get(role, 'ukn'), label

    def _insert_obj(self, obj_dict, obj):
        ldtpized_name = self._ldtpize_accessible(obj)
        try:
            key = u"%s%s" % (ldtpized_name[0], ldtpized_name[1])
        except UnicodeEncodeError:
            key = u"%s%s" % (ldtpized_name[0],
                             ldtpized_name[1].decode('utf-8'))
        count = 1
        while obj_dict.has_key(key):
            key = u'%s%s%d' % (ldtpized_name[0], ldtpized_name[1], count)
            try:
                key = u"%s%s%d" % (ldtpized_name[0],
                                   ldtpized_name[1], count)
            except UnicodeEncodeError:
                key = u"%s%s%d" % (ldtpized_name[0],
                                   ldtpized_name[1].decode('utf-8'), count)
            count += 1
        obj_dict[key] = obj

    def _get_windows(self):
        windows = {}
        for gui in set(self._running_apps):
            # Get process id
            pid = gui.processIdentifier()
            # Get app id
            app = atomac.getAppRefByPid(pid)
            # Navigate all the windows
            for window in app.windows():
                if not window:
                    continue
                self._insert_obj(windows, window)
        return windows

    def _get_value(self, obj):
        value = None
        try:
            value=obj.AXValue
        except (atomac._a11y.ErrorUnsupported, atomac._a11y.Error):
            try:
                value=obj.AXRoleDescription
            except (atomac._a11y.ErrorUnsupported, atomac._a11y.Error):
                pass
        return value

    def _get_window_title(self, window):
        title = ''
        try:
            title=window.AXTitle
        except (atomac._a11y.ErrorUnsupported, atomac._a11y.Error):
            try:
                title=window.AXValue
            except (atomac._a11y.ErrorUnsupported, atomac._a11y.Error):
                try:
                    title=window.AXRoleDescription
                except (atomac._a11y.ErrorUnsupported, atomac._a11y.Error):
                    pass
        return title

    def _get_role(self, obj):
        role = ''
        try:
            role=obj.AXRole
        except (atomac._a11y.ErrorUnsupported, atomac._a11y.Error):
            pass
        return role

    def _get_window_handle(self, window_name):
        if not window_name:
            return None
        window_name = fnmatch.translate(window_name)
        windows = self._get_windows()
        for window in windows:
            if re.match(window_name, window):
                return windows[window]
        return None

    def _populate_appmap(self, window_handle):
        if not window_handle:
            return {}
        obj_dict = {}
        for obj in window_handle.findAllR():
            self._insert_obj(obj_dict, obj)
        return obj_dict
