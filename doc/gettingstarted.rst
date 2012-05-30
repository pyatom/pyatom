===============
Getting Started
===============

------------------
Basic Requirements
------------------

* *Host*
  
  ATOMac requires an Intel-based system running OS X and Xcode installed.

  Tested OS versions:

  * 10.6
  * 10.7

  It may work on 10.5.
  If you experience issues with ATOMac on a particular version of OS X,
  please open a ticket in the issue tracker.
 
* *System Preferences*
  
  System-wide accessibility must be enabled. 
  
  To enable access for assistive devices,
  check the checkbox: 
 
  | *System Preferences >*
  |    *Universal Access >*
  |       *Enable access for assistive devices.*
  
  Failure to enable this will result in ErrorAPIDisabled exceptions or invalid references.
  
  To facilitate programmatic control via keyboard shortcuts,
  select the radio button for *All Controls* under
  
  | *System Preferences >*
  |    *Keyboard >*
  |       *Keyboard Shortcuts >*
  |          *Full Keyboard Access*
 
* *Installation*
  
  Installation should be as simple as running the following command line,
  which will download, build and install ATOMac::

  $ sudo easy_install atomac
  
  Alternatively, you can use `pip <http://pypi.python.org/pypi/pip>`_ 
  for easier module management.
