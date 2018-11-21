# Copyright (c) 2010 VMware, Inc. All Rights Reserved.

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

import types
import AppKit
import pprint
import logging
import Foundation


class Clipboard(object):
    """Class to represent clipboard-related operations for text"""

    # String encoding type
    utf8encoding = Foundation.NSUTF8StringEncoding

    # Class attributes to distinguish types of data:
    # Reference:
    # http://developer.apple.com/mac/library/documentation/Cocoa/Reference/
    # ApplicationKit/Classes/NSPasteboard_Class/Reference/Reference.html

    # Text data type
    STRING = AppKit.NSStringPboardType
    # Rich-text format data type (e.g. rtf documents)
    RTF = AppKit.NSRTFPboardType
    # Image datatype (e.g. tiff)
    IMAGE = AppKit.NSTIFFPboardType
    # URL data type (not just web but file locations also)
    URL = AppKit.NSURLPboardType
    # Color datatype - not sure if we'll have to use this one
    # Supposedly replaced in 10.6 but the pyobjc AppKit module doesn't have the
    # new data type as an attribute
    COLOR = AppKit.NSColorPboardType

    # You can extend this list of data types
    # e.g. File copy and paste between host and guest
    # Not sure if text copy and paste between host and guest falls under STRING/
    # RTF or not
    # List of PboardTypes I found in AppKit:
    # NSColorPboardType
    # NSCreateFileContentsPboardType
    # NSCreateFilenamePboardType
    # NSDragPboard
    # NSFileContentsPboardType
    # NSFilenamesPboardType
    # NSFilesPromisePboardType
    # NSFindPanelSearchOptionsPboardType
    # NSFindPboard
    # NSFontPboard
    # NSFontPboardType
    # NSGeneralPboard
    # NSHTMLPboardType
    # NSInkTextPboardType
    # NSMultipleTextSelectionPboardType
    # NSPDFPboardType
    # NSPICTPboardType
    # NSPostScriptPboardType
    # NSRTFDPboardType
    # NSRTFPboardType
    # NSRulerPboard
    # NSRulerPboardType
    # NSSoundPboardType
    # NSStringPboardType
    # NSTIFFPboardType
    # NSTabularTextPboardType
    # NSURLPboardType
    # NSVCardPboardType

    @classmethod
    def paste(cls):
        """Get the clipboard data ('Paste').

        Returns: Data (string) retrieved or None if empty. Exceptions from
        AppKit will be handled by caller.
        """
        pb = AppKit.NSPasteboard.generalPasteboard()

        # If we allow for multiple data types (e.g. a list of data types)
        # we will have to add a condition to check just the first in the
        # list of datatypes)
        data = pb.stringForType_(cls.STRING)
        return data

    @classmethod
    def copy(cls, data):
        """Set the clipboard data ('Copy').

        Parameters: data to set (string)
        Optional: datatype if it's not a string
        Returns: True / False on successful copy, Any exception raised (like
                 passes the NSPasteboardCommunicationError) should be caught
                 by the caller.
        """
        pp = pprint.PrettyPrinter()

        copy_data = 'Data to copy (put in pasteboard): %s'
        logging.debug(copy_data % pp.pformat(data))

        # Clear the pasteboard first:
        cleared = cls.clearAll()
        if not cleared:
            logging.warning('Clipboard could not clear properly')
            return False

        # Prepare to write the data
        # If we just use writeObjects the sequence to write to the clipboard is
        # a) Call clearContents()
        # b) Call writeObjects() with a list of objects to write to the
        #    clipboard
        if not isinstance(data, types.ListType):
            data = [data]

        pb = AppKit.NSPasteboard.generalPasteboard()
        pb_set_ok = pb.writeObjects_(data)

        return bool(pb_set_ok)

    @classmethod
    def clearContents(cls):
        """Clear contents of general pasteboard.

        Future enhancement can include specifying which clipboard to clear
        Returns: True on success; caller should expect to catch exceptions,
                 probably from AppKit (ValueError)
        """
        log_msg = 'Request to clear contents of pasteboard: general'
        logging.debug(log_msg)
        pb = AppKit.NSPasteboard.generalPasteboard()
        pb.clearContents()
        return True

    @classmethod
    def clearProperties(cls):
        """Clear properties of general pasteboard.

        Future enhancement can include specifying which clipboard's properties
        to clear
        Returns: True on success; caller should catch exceptions raised,
                 e.g. from AppKit (ValueError)
        """
        log_msg = 'Request to clear properties of pasteboard: general'
        logging.debug(log_msg)
        pb = AppKit.NSPasteboard.generalPasteboard()
        pb.clearProperties()

        return True

    @classmethod
    def clearAll(cls):
        """Clear contents and properties of general pasteboard.

        Future enhancement can include specifying which clipboard's properties
        to clear
        Returns: Boolean True on success; caller should handle exceptions
        """
        cls.clearContents()
        cls.clearProperties()

        return True

    @classmethod
    def isEmpty(cls, datatype=None):
        """Method to test if the general pasteboard is empty or not with respect
        to the type of object you want.

        Parameters: datatype (defaults to strings)
        Returns: Boolean True (empty) / False (has contents); Raises
                 exception (passes any raised up)
        """
        if not datatype:
            datatype = AppKit.NSString
        if not isinstance(datatype, types.ListType):
            datatype = [datatype]
        pp = pprint.PrettyPrinter()
        logging.debug('Desired datatypes: %s' % pp.pformat(datatype))
        opt_dict = {}
        logging.debug('Results filter is: %s' % pp.pformat(opt_dict))

        try:
            log_msg = 'Request to verify pasteboard is empty'
            logging.debug(log_msg)
            pb = AppKit.NSPasteboard.generalPasteboard()
            # canReadObjectForClasses_options_() seems to return an int (> 0 if
            # True)
            # Need to negate to get the sense we want (True if can not read the
            # data type from the pasteboard)
            its_empty = not bool(pb.canReadObjectForClasses_options_(datatype,
                                                                     opt_dict))
        except ValueError as error:
            logging.exception(error)
            raise

        return bool(its_empty)