import objc
import re
import signal
import Cocoa
from CoreFoundation import *
from ApplicationServices import *
from PyObjCTools import AppHelper, MachSignals

"""
Library of Apple A11y functions
"""
def _CFAttributeToPyObject(self, attrValue):
    def list_helper(list_value):
        list_builder = []
        for item in list_value:
            list_builder.append(_CFAttributeToPyObject(self, item))
        return list_builder

    def number_helper(number_value):
        success, int_value = CFNumberGetValue(number_value, kCFNumberIntType, None)
        if success:
            return int(int_value)

        success, float_value = CFNumberGetValue(number_value, kCFNumberDoubleType, None)
        if success:
            return float(float_value)

        raise ErrorUnsupported('Error converting numeric attribute: {}'.format(number_value))

    def axuielement_helper(element_value):
        return self.with_ref(element_value)

    cf_attr_type = CFGetTypeID(attrValue)
    cf_type_mapping = {
        CFStringGetTypeID(): str,
        CFBooleanGetTypeID(): bool,
        CFArrayGetTypeID(): list_helper,
        CFNumberGetTypeID(): number_helper,
        AXUIElementGetTypeID(): axuielement_helper,
    }
    try:
        return cf_type_mapping[cf_attr_type](attrValue)
    except KeyError:
        # did not get a supported CF type. Move on to AX type
        pass

    ax_attr_type = AXValueGetType(attrValue)
    ax_type_map = {
        kAXValueCGSizeType: NSSizeFromString,
        kAXValueCGPointType: NSPointFromString,
        kAXValueCFRangeType: NSRangeFromString,
    }
    try:
        extracted_str = re.search('{.*}', attrValue.description()).group()
        return tuple(ax_type_map[ax_attr_type](extracted_str))
    except KeyError:
        raise ErrorUnsupported('Return value not supported yet: {}'.format(ax_attr_type))

def _sigHandler(sig):
    AppHelper.stopEventLoop()
    raise KeyboardInterrupt('Keyboard interrupted Run Loop')

def _setError(error_code, error_message):
    error_mapping = {
        kAXErrorAttributeUnsupported: ErrorUnsupported, # -25205
        kAXErrorActionUnsupported: ErrorUnsupported, # -25206
        kAXErrorNotificationUnsupported: ErrorUnsupported, # -25207
        kAXErrorAPIDisabled: ErrorAPIDisabled, # -25211
        kAXErrorInvalidUIElement: ErrorInvalidUIElement, # -25202
        kAXErrorCannotComplete: ErrorCannotComplete, # -25204
        kAXErrorNotImplemented: ErrorNotImplemented, # -25208
    }
    msg = '{} (AX Error {})'.format(error_message, error_code)

    raise error_mapping[error_code](msg)

class Error(Exception):
    pass

class ErrorAPIDisabled(Error):
    pass

class ErrorInvalidUIElement(Error):
    pass

class ErrorCannotComplete(Error):
    pass

class ErrorUnsupported(Error):
    pass

class ErrorNotImplemented(Error):
    pass

class AXUIElement(object):
    """
    Apple AXUIElement object
    """
    """
    1. Factory class methods for getAppRefByPid and getSystemObject which
       properly instantiate the class.
    2. Generators and methods for finding objects for use in child classes.
    3. __getattribute__ call for invoking actions.
    4. waitFor utility based upon AX notifications.
    """
    def __init__(self, ref=None, callback_fn=None, callback_args=None, callback_kwargs=None, observer_res=None):
        super(AXUIElement, self).__init__()
        self.ref = ref
        self.callbackFn = callback_fn
        self.callbackArgs = callback_args
        self.callbackKwargs = callback_kwargs
        self.observerRes = observer_res

    def _setNotification(self, timeout=0, notificationStr=None, callbackFn=None, callbackArgs=None, callbackKwargs=None):
        if callable(callbackFn):
            self.callbackFn = callbackFn

        if isinstance(callbackArgs, tuple):
            self.callbackArgs = callbackArgs
        else:
            self.callbackArgs = tuple()

        if isinstance(callbackKwargs, dict):
            self.callbackKwargs = callbackKwargs

        self.observerRes = None

        pid = self._getPid()
        err, observer = AXObserverCreate(pid, observerCallback, None)
        if err != kAXErrorSuccess:
            _setError(err, 'Could not create observer for notification')

        err = AXObserverAddNotification(
            observer, self.ref,
            notificationStr,
            self
        )

        if err != kAXErrorSuccess:
            _setError(err, 'Could not add notification to observer')

        #Add observer source to run loop
        CFRunLoopAddSource(
            CFRunLoopGetCurrent(),
            AXObserverGetRunLoopSource(observer),
            kCFRunLoopDefaultMode
        )

        # Set the signal handlers prior to running the run loop
        oldSigIntHandler = MachSignals.signal(signal.SIGINT, _sigHandler)
        # If an error occurs (return value is SIG_ERR), continue as it's not fatal
        AppHelper.runConsoleEventLoop(
            mode=kCFRunLoopDefaultMode,
            installInterrupt=False,
            maxTimeout=timeout,
        )
        MachSignals.signal(signal.SIGINT, oldSigIntHandler)
        err = AXObserverRemoveNotification(observer, self.ref, notificationStr)
        if err != kAXErrorSuccess:
            _setError(err, 'Could not remove notification from observer')

        return self.observerRes
        # if timeout
        # return False

    def _getAttributes(self):
        """
        Get a list of the actions available on the AXUIElement
        :return:
        """
        err, attr = AXUIElementCopyAttributeNames(self.ref, None)

        if err != kAXErrorSuccess:
            _setError(err, 'Error retrieving attribute list')
        else:
            return list(attr)

    def _getActions(self):
        """
        Get a list of the actions available on the AXUIElement
        :return:
        """
        if self.ref is None:
            raise Error('Not a valid accessibility object')

        err, actions = AXUIElementCopyActionNames(self.ref, None)
        if err != kAXErrorSuccess:
            _setError(err, 'Error retrieving action names')
        else:
            return list(actions)

    def _performAction(self, action):
        """
        Perform the specified action on the AXUIElement object
        :param action:
        :return:
        """
        err = AXUIElementPerformAction(self.ref, action)

        if err != kAXErrorSuccess:
            _setError(err, 'Error performing requested action')

    def _getAttribute(self, attr):
        """
        Get the value of the the specified attribute
        :param args:
        :return:
        """
        err, attrValue = AXUIElementCopyAttributeValue(self.ref, attr, None)
        if err == kAXErrorNoValue:
            return

        if err != kAXErrorSuccess:
            if err == kAXErrorNotImplemented:
                _setError(err, 'Attribute not implemented')
            else:
                _setError(err, 'Error retrieving attribute')

        return _CFAttributeToPyObject(self, attrValue)

    def _setAttribute(self, attr, val):
        """
        Set the specified attribute to the specified value
        :param args:
        :return:
        """
        self._getAttribute(attr)
        err, to_set = AXUIElementCopyAttributeValue(self.ref, attr, None)
        if err != kAXErrorSuccess:
            _setError(err, 'Error retrieving attribute to set')

        err, settable = AXUIElementIsAttributeSettable(self.ref, attr, None)
        if err != kAXErrorSuccess:
            _setError(err, 'Error querying attribute')

        if not settable:
            raise ErrorUnsupported('Attribute is not settable')

        err = AXUIElementSetAttributeValue(self.ref, attr, val)
        if err != kAXErrorSuccess:
            if err == kAXErrorIllegalArgument:
                _setError(err, 'Invalid value for element attribute')
            _setError(err, 'Error setting attribute value')

    # def __setattr__(self, name, value):
    #     pass

    def _setString(self, attribute, value):
        err = AXUIElementSetAttributeValue(self.ref, attribute, str(value))
        if err != kAXErrorSuccess:
            _setError(err, 'Error setting attribute to string')

    def _getPid(self):
        """
        Get the PID of the AXUIElement
        """
        error_code, pid = AXUIElementGetPid(self.ref, None)
        if error_code != kAXErrorSuccess:
            _setError(error_code, 'Error retrieving PID')
        return pid

    def _setTimeout(self, newTimeout):
        if self.ref is None:
            raise ErrorUnsupported('Operation not supported on null element references')

        err = AXUIElementSetMessagingTimeout(self.ref, newTimeout)
        if err == kAXErrorIllegalArgument:
            raise ValueError('Accessibility timeout values must be non-negative')
        if err == kAXErrorInvalidUIElement:
            _setError(err, 'The element reference is invalid')

    def _getElementAtPosition(self, x, y):
        if self.ref is None:
            raise ErrorUnsupported('Operation not supported on null element references')

        err, res = AXUIElementCopyElementAtPosition(self.ref, x, y, None)
        if err == kAXErrorIllegalArgument:
            raise ValueError('Arguments must be two floats.')

        return self.with_ref(res)

    @classmethod
    def with_ref(cls, ref):
        """
        Create a new Python AXUIElement object from a given Apple AXUIElementRef
        :param ref:
        :return:
        """
        if isinstance(ref, cls):
            return cls(ref.ref)
        return cls(ref=ref)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        selr = self.ref
        othr = other.ref
        if self.ref is None and other.ref is None:
            return True

        if self.ref is None or other.ref is None:
            return False

        return CFEqual(self.ref, other.ref)

    def __ne__(self, other):
        return not self.__eq__(other)


"""
module functions
"""
def axenabled():
    """
    Return the status of accessibility on the system.
    :return: bool
    """
    return AXIsProcessTrusted()


def getfrontmostpid():
    """
    Return the PID of the application in the foreground.
    :return: int
    """
    frontmost_app = NSWorkspace.sharedWorkspace().frontmostApplication()
    pid = frontmost_app.processIdentifier()
    return pid


def getAppRefByPid(cls, pid):
    """
        Get an AXUIElement reference to the application specified by the given PID.
    """
    app_ref = AXUIElementCreateApplication(pid)

    if app_ref is None:
        raise ErrorUnsupported('Error getting app ref')

    return cls.with_ref(app_ref)


def getSystemObject(cls):
    """
        Get an AXUIElement reference for the system accessibility object.
    """
    app_ref = AXUIElementCreateSystemWide()

    if app_ref is None:
        raise ErrorUnsupported('Error getting a11y object')

    return cls.with_ref(app_ref)


# callbacks
# Callback methods for notifications
def observerCallback(cls, element, contextData):
    axObj = contextData
    cb_fn = contextData.callbackFn
    cb_args = contextData.callbackArgs
    cb_kwargs = contextData.callbackKwargs
    if cb_fn is not None:
        retElem = cls.with_ref(element)
        if retElem is None:
            raise RuntimeError('Could not create new AX UI Element.')

        cb_args = (retElem,) + cb_args
        callbackRes = cb_fn(cb_args, cb_kwargs)

        if callbackRes is None:
            raise RuntimeError('Python callback failed.')

        if callbackRes in (-1, 1):
            AppHelper.stopEventLoop()

        temp = axObj.observerRes
        axObj.observerRes = callbackRes
    else:
        AppHelper.stopEventLoop()
        temp = axObj.observerRes
        axObj.observerRes = True
