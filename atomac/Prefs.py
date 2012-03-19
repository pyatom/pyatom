# -*- coding: utf-8 -*-

# Copyright (c) 2011 Julián Romero.

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

from AppKit import NSWorkspace, NSUserDefaults, NSDictionary, NSMutableDictionary
from UserDict import UserDict
from os import path

__all__ = ["Prefs"]

class Prefs(UserDict):
    ''' NSUserDefaults proxy to read/write application preferences.
        It has been conceived to prepare the preferences before a test launch the app.
        Once a Prefs instance is created, it doesn't detect prefs changed elsewhere,
        so for now you need to create the instance right before reading/writing a pref.
        Defaults.plist with default values is expected to exist on the app bundle.

        p = Prefs('com.example.App')
        coolStuff = p['CoolStuff']
        p['CoolStuff'] = newCoolStuff

    '''
    def __init__(self, bundleID, bundlePath=None, defaultsPlistName='Defaults'):
        ''' bundleId: the application bundle identifier
            bundlePath: the full bundle path (useful to test a Debug build)
            defaultsPlistName: the name of the plist that contains default values
        '''
        self.__bundleID = bundleID
        self.__bundlePath = bundlePath
        UserDict.__init__(self)
        self.__setup(defaultsPlistName)

    def __setup(self, defaultsPlistName=None):
        NSUserDefaults.resetStandardUserDefaults()
        prefs = NSUserDefaults.standardUserDefaults()
        self.defaults = self.__defaults(defaultsPlistName)
        domainData = prefs.persistentDomainForName_(self.__bundleID)
        if domainData:
            self.data = domainData
        else:
            self.data = NSDictionary.dictionary()

    def __defaults(self, plistName='Defaults'):
        if self.__bundlePath is None:
            self.__bundlePath = NSWorkspace.sharedWorkspace().absolutePathForAppBundleWithIdentifier_(self.__bundleID)
        if self.__bundlePath:
            plistPath = path.join(self.__bundlePath, "Contents/Resources/%s.plist" % plistName)
            plist = NSDictionary.dictionaryWithContentsOfFile_(plistPath)
            if plist:
                return plist
        return NSDictionary.dictionary()

    def get(self, key):
        return self.__getitem__(key)

    def __getitem__(self, key):
        result = self.data.get(key, None)
        if result is None or result == '':
            if self.defaults:
                result = self.defaults.get(key, None)
        return result

    def set(self, key, value):
        self.__setitem__(key, value)

    def __setitem__(self, key, value):
        mutableData = self.data.mutableCopy()
        mutableData[key] = value
        self.data = mutableData
        prefs = NSUserDefaults.standardUserDefaults()
        prefs.setPersistentDomain_forName_(self.data, self.__bundleID)

