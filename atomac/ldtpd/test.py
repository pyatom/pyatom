# Copyright (c) 2012 VMware, Inc. All Rights Reserved.

# This file is part of ATOMac.

#@author: Nagappan Alagappan <nagappan@gmail.com>
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
"""Core class to be exposed via XMLRPC in LDTP daemon."""

import core

test=core.Core()
#test.launchapp('Calculator')
#print test.launchapp('Chicken of the VNC')
#print test.launchapp('app does not exist')
#test.wait(5)
#test.generatekeyevent('d<return>')
#test.generatekeyevent('d')
#test.generatekeyevent('d<tab><tab>')
#test.generatekeyevent('<command>t')
#test.generatekeyevent('<command>n')
#test.generatekeyevent('<command_l><tab>') # Not working
#test.keypress('<shift_l>') # Not working
#test.generatekeyevent('<shift>abc')
#test.generatekeyevent('xyz')
#test.generatekeyevent('<capslock>abc') # Caps lock not working
#test.keyrelease('<shift_l>') # Not working
#test.imagecapture('Untitled')
#apps=test.getapplist()
#windows=test.getwindowlist()
#test.generatemouseevent(10, 10)
#test.wait(3)
#size=test.getobjectsize("Jay")
#test.generatemouseevent(size[0] + 100, size[1] + 5, "b3c")
#test.generatemouseevent(size[0]-100, size[1], "b1d")
#print test.guiexist("gedit")
#print test.guiexist("gedit", "txt0")
#print test.guiexist("Open")
#print test.guiexist("Open", "btnCancel")
#print test.guiexist("Open", "C0ncel")
#print "waittillguiexist"
#print test.waittillguiexist("Open")
#print test.waittillguiexist("Open", "btnCancel")
#print test.waittillguiexist("Open", "C0ncel", 10)
#print "waittillguinotexist"
#print test.waittillguinotexist("Open", guiTimeOut=5)
#print test.waittillguinotexist("Open", "btnCancel", 5)
#print test.waittillguinotexist("Open", "C0ncel")
#print windows
#objList = test.getobjectlist("frmTryitEditorv1.5")
#for obj in objList:
    #if re.search("^tbl\d", obj):
        #print obj, test.getrowcount("frmTryitEditorv1.5", obj)
#print test.selectrow("Accounts", "tbl0", "VMware")
#print test.selectrowpartialmatch("Accounts", "tbl0", "Zim")
#print test.selectrowindex("Accounts", "tbl0", 0)
#print test.selectlastrow("Accounts", "tbl0")
#print test.getcellvalue("Accounts", "tbl0", 1)
#print test.scrollup("Downloads", "scbr0")
#print test.oneright("Downloads", "scbr1", 3)
#print len(apps), len(windows)
#print apps, windows
#print test.getobjectlist("Contacts")
#print test.click("Open", "Cancel")
#print test.comboselect("frmInstruments", "cboAdd", "UiAutomation.js")
#print test.comboselect("frmInstruments", "Choose Target", "Choose Target;Octopus")
#print test.getobjectlist("frmInstruments")
#print test.check("frmInstruments", "chkRecordOnce")
#print test.wait(1)
#print test.uncheck("frmInstruments", "chkRepeatRecording")
#print test.uncheck("frmInstruments", "chkPause")
#print test.verifyuncheck("frmInstruments", "chkPause")
#print test.verifycheck("frmInstruments", "chkRepeatRecording")
#print test.doesmenuitemexist("Instru*", "File;Open...")
#print test.doesmenuitemexist("Instruments*", "File;Open...")
#print test.doesmenuitemexist("Instruments*", "File;Open*")
#print test.selectmenuitem("Instruments*", "File;Open*")
#print test.checkmenu("Instruments*", "View;Instruments")
#test.wait(1)
#print test.checkmenu("Instruments*", "View;Instruments")
#print test.uncheckmenu("Instruments*", "View;Instruments")
#test.wait(1)
#print test.verifymenucheck("Instruments*", "View;Instruments")
#print test.verifymenuuncheck("Instruments*", "View;Instruments")
#print test.checkmenu("Instruments*", "View;Instruments")
#test.wait(1)
#print test.verifymenucheck("Instruments*", "View;Instruments")
#print test.verifymenuuncheck("Instruments*", "View;Instruments")
#print test.mouseleftclick("Open", "Cancel")
#a=test.getobjectlist("Open")
#for i in a:
#    if i.find("txt") != -1:
#        print i
#print test.settextvalue("Open", "txttextfield", "pyatom ldtp")
#print test.gettextvalue("Open", "txttextfield")
#print test.getcharcount("Open", "txttextfield")
#print test.menuitemenabled("Instruments*", "File;Record Trace")
#print test.menuitemenabled("Instruments*", "File;Pause Trace")
#print test.listsubmenus("Instruments*", "Fi*")
#print test.listsubmenus("Instruments*", "File;OpenRecent")
#print test.listsubmenus("Instruments*", "File;mnuOpenRecent")
#print test.listsubmenus("Instruments*", "File;GetInfo")
#try:
#    print test.listsubmenus("Instruments*", "File;ding")
#except LdtpServerException:
#    pass
#try:
#    print test.listsubmenus("Instruments*", "ding")
#except LdtpServerException:
#    pass
#try:
#    print test.listsubmenus("ding", "dong")
#except LdtpServerException:
#    pass
#print test.getcursorposition("Open", "txttextfield")
#print test.setcursorposition("Open", "txttextfield", 10)
#print test.cuttext("Open", "txttextfield", 2)
#print test.cuttext("Open", "txttextfield", 2, 20)
#print test.pastetext("Open", "txttextfield", 2)
#print test.gettabname("*ldtpd*python*", "ptl0", 2)
#print test.gettabcount("*ldtpd*python*", "ptl0")
#print test.selecttabindex("*ldtpd*python*", "ptl0", 2)
#print test.selecttab("*ldtpd*python*", "ptl0", "*bash*")
#print test.verifytabname("*ldtpd*python*", "ptl0", "*gabe*")
#print test.selectindex("frmInstruments", "cboAdd", 1)
#print test.getallitem("frmInstruments", "cboAdd")
#print test.selectindex("frmInstruments", "cboAdd", 10)
#print test.showlist("frmInstruments", "cboAdd")
#test.wait(1)
#print test.verifydropdown("frmInstruments", "cboAdd")
#print test.hidelist("frmInstruments", "cboAdd")
#test.wait(1)
#print test.verifydropdown("frmInstruments", "cboAdd")
#print test.showlist("frmInstruments", "cboAdd")
#test.wait(1)
#print test.verifyshowlist("frmInstruments", "cboAdd")
#print test.hidelist("frmInstruments", "cboAdd")
#test.wait(1)
#print test.verifyhidelist("frmInstruments", "cboAdd")
# Terminal settings window
#print test.comboselect("frmInstruments", "lst0", "Trace Log")
#print test.getallstates("Settings", "chkUseboldfonts")
#print test.getallstates("Settings", "chkAntialiastext")
#print test.getallstates("Settings", "rbtn*Block")
#print test.getallstates("Settings", "rbtn*Underline")
