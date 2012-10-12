=================================
ATOMac - Automated Testing on Mac
=================================
Introduction
============
We are pleased to introduce the first Python library to fully enable GUI testing of Mac applications via the Apple Accessibility API. This library was created out of desperation. Existing tools such as using appscript to send messages to accessibility objects are painful to write and slow to use. ATOMac has direct access to the API. It's fast and easy to use to write tests.

Getting started
===============
ATOMac requires a system running OS X and Xcode installed. It has been tested extensively on 10.6, 10.7, and 10.8. 10.5 may work. If you experience issues with ATOMac on a particular version of OS X, please open a ticket in the issue tracker.

Systemwide accessibility must be enabled. Check the checkbox: System Preferences > Universal Access > Enable access for assistive devices. Failure to enable this will result in ErrorAPIDisabled exceptions during some module usage.

Installation should be as simple as running the following command line, which will download, build and install ATOMac::

 $ sudo easy_install atomac

Usage
=====
Once the atomac module is installed, you should be able to use it to launch an application::

 >>> import atomac
 >>> atomac.launchAppByBundleId('com.apple.Automator')

This should launch Automator. Next, get a reference to the UI Element for the application itself::

 >>> automator = atomac.getAppRefByBundleId('com.apple.Automator')
 >>> automator
 <pyatom.AXClasses.NativeUIElement AXApplication u'Automator'>

Now, we can find objects in the accessibility hierarchy::

 >>> window = automator.windows()[0]
 >>> window.AXTitle
 u'Untitled'
 >>> sheet = window.sheets()[0]

Note that we retrieved an accessibility attribute from the Window object - AXTitle. ATOMac supports reading and writing of most attributes. Using Xcode's included accessibility inspector can provide a quick way to find these attributes.

There is a shortcut for getting the sheet object which bypasses accessing it through the Window object - ATOMac can search all objects in the hierarchy::

 >>> sheet = automator.sheetsR()[0]

There are search methods for most types of accessibility objects. Each search method, such as ``windows``, has a corresponding recursive search function, such as ``windowsR``. The recursive search finds items that aren't just direct children, but children of children. These search methods can be given terms to identify specific elements. Note that * and ? can be used as wildcard match characters in all ATOMac search methods::

 >>> close = sheet.buttons('Close')[0]

ATOMac has a method to search for UI Elements that match any number of criteria. The criteria are accessibility attributes::

 >>> close = sheet.findFirst(AXRole='AXButton', AXTitle='Close')

``FindFirst`` and ``FindFirstR`` return the first item found to match the criteria or None. ``FindAll`` and ``FindAllR`` return a list of all items that match the criteria or an empty list.

Objects are fairly versatile. You can get a list of supported attributes and actions on an object::

 >>> close.getAttributes()
 [u'AXRole', u'AXRoleDescription', u'AXHelp', u'AXEnabled', u'AXFocused',
 u'AXParent', u'AXWindow', u'AXTopLevelUIElement', u'AXPosition', u'AXSize',
 u'AXTitle']
 >>> close.AXTitle
 u'Close'
 >>> close.getActions()
 [u'Press']

Performing an action is as natural as::

 >>> close.Press()

Any action can be triggered this way.

LDTP
====
Starting with version 1.0.0, ATOMac now includes compatibility with LDTP, a cross platform automation library. This allows testers to write a single script that will automate test cases on Linux, Windows, and now Mac OS X. Information and documentation on LDTP can be found at the `LDTP home page`_.

.. _`LDTP home page`: http://ldtp.freedesktop.org/

LDTP operation is virtually identical to the operation on Linux. The import mechanism is slightly different, since it is shipped with ATOMac. Cross platform scripts executing on the System Under Test should import the LDTP client as follows::

 try:
     import ldtp
 except ImportError:
     import atomac.ldtp as ldtp

In the future, the LDTP client may be broken out into a separate platform independent module to ameliorate this issue.

Like the Linux platform, the LDTP daemon may be run on the SUT, enabling client/server testing by executing 'ldtp' at a shell prompt. See the LDTP documentation for more details on client/server operation.

Todo and contributing
=====================
Although ATOMac is fully functional and drives hundreds of automated test cases at VMware, we have a to-do list to make the project even better.

* Formatting - this code is not currently PEP-8 compliant.
* Better mouse handling - for example, a method to smoothly drag from one UI Element to another.
* Cleanup the search methods - We could use currying to define all the search methods in AXClasses in a cleaner way.

Feel free to submit pull requests against the project on Github. If you're interested in developing ATOMac itself, sign up to the pyatom-dev mailing list.

See also
========
* The ATOMac `home page`_
* `Changelog`_
* `Mailing lists`_
* `Source code`_ on Github
* `Issue tracker`_

.. _`home page`: http://pyatom.com
.. _`changelog` : https://raw.github.com/pyatom/pyatom/master/CHANGELOG.txt
.. _`mailing lists`: http://lists.pyatom.com
.. _`source code`: https://github.com/pyatom/pyatom
.. _`issue tracker`: https://github.com/pyatom/pyatom/issues

License
=======

ATOMac is released under the GNU General Public License. See COPYING.txt for more details.

Authors
=======

James Tatum <jtatum@gmail.com>,
Andrew Wu,
Jesse Mendonca,
Ken Song,
Nagappan Alagappan,
Yingjun Li,

And other contributors listed in the CHANGELOG file. Thank you so much!
