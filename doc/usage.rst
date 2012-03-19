Usage
=====


Working with Applications
-------------------------

Once the atomac module is installed,
we should be able to use it to launch an application::

    >>> import atomac
    >>> atomac.launchAppByBundleId('com.apple.Automator')

This should launch Automator.
Next, we can get a reference to the UI element 
for the application itself::

    >>> automator = atomac.getAppRefByBundleId('com.apple.Automator')
    >>> automator
    <atomac.AXClasses.NativeUIElement AXApplication u'Automator'>

Other means of obtaining references to a running application include::

    >>> automator = atomac.getAppRefByLocalizedName('Automator')
    >>> automator = atomac.getAppRefByPid(12345)

Finally, to terminate a running application, 
we can use the method ``terminateAppByBundleId``::

    >>> atomac.terminateAppByBundleId('com.apple.Automator')


Finding Objects in the Hierarchy
--------------------------------

Assuming we have an atomac reference 
to the running Automator application,
we can find objects in the accessibility hierarchy::

    >>> window = automator.windows()[0]
    >>> window.AXTitle
    u'Untitled'
    >>> sheet = window.sheets()[0]

Note that we retrieved an accessibility attribute 
from the Window object - AXTitle.
ATOMac supports reading and writing of most attributes.
Using Xcode's included *Accessibility Inspector* utility can provide
a quick way to find these attributes.

There is a shortcut for getting the sheet object
which bypasses accessing it through the Window object.
ATOMac can search all objects in the hierarchy 
by appending 'R' to the end of the method call::

    >>> sheet = automator.sheetsR()[0]

There are search methods for most types of accessibility objects.
Each search method, such as ``windows``,
has a corresponding recursive search function, such as ``windowsR``. 
The recursive search finds items 
that aren't just direct children of the associated object,
but children of its children. 
These search methods can be given terms to identify specific elements.
Note that "*" and "?" can be used as wildcard match characters 
in all ATOMac search methods::

    >>> close = sheet.buttons('Close*')[0]

ATOMac has a method to search for UI elements 
that match any number of criteria. 
The criteria are accessibility attributes 
(as outlined in Accessibility Inspector)::

    >>> close = sheet.findFirst(AXRole='AXButton', AXTitle='Close')

``FindFirst`` and ``FindFirstR`` return 
the first item found to match the criteria or ``None``. 
``FindAll`` and ``FindAllR`` return a list of all items 
that match the criteria or an empty list.


Attributes and Actions
----------------------

Objects are fairly versatile. 
You can get a list of supported attributes and actions on an object::

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

Note that in Accessibility Inspector the action name begins with "AX-". 
To distinguish actions more easily from attributes, 
atomac drops the initial "AX" for names of actions.  
As a result, "AXPress" in Accessibility Inspector simply becomes 
"Press" in atomac and can be invoked on the object as ``Press()``. 
Any appropriate action can be triggered this way.

