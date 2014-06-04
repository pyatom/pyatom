/* **********************************************************
 * Copyright (C) 2010-2011 VMware, Inc. All rights reserved.
 * **********************************************************/

/* **************************************************************************
 * This file is part of ATOMac.
 *
 * ATOMac is free software; you can redistribute it and/or modify it under
 * the terms of the GNU General Public License as published by the Free
 * Software Foundation version 2 and no later version.
 *
 * ATOMac is distributed in the hope that it will be useful, but WITHOUT ANY
 * WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
 * FOR A PARTICULAR PURPOSE. See the GNU General Public License version 2
 * for more details.
 *
 * You should have received a copy of the GNU General Public License along with
 * this program; if not, write to the Free Software Foundation, Inc., 51
 * Franklin St, Fifth Floor, Boston, MA 02110-1301 USA.
 * **************************************************************************/

/*
 * a11ymodule.c --
 *
 *      Main module file for ATOMac a11y module
 */

#include <Python.h>
#include <ApplicationServices/ApplicationServices.h>
#include <Carbon/Carbon.h>
#include <sys/types.h>
#include <signal.h>

#include "conversion.h"
#include "axlib.h"

/*
 * Local data
 */

/*
 * AXUIElement typedef
 * This encapsulates an apple AXUIElementRef in a Python object.
 */
typedef struct atomac_AXUIElement{
   PyObject_HEAD       // Python boilerplate macro
   AXUIElementRef ref; // Apple AXUIElementRef encapsulated by the Python obj
   /* For notifications */
   PyObject *observerRes;  // Store return value of the python callback
   PyObject *callbackFn;   // A python callback function if set
   PyObject *callbackArgs;    // Args to the python callback
   PyObject *callbackKwargs;  // Kwargs to the python callback
} atomac_AXUIElement;

/*
 * Python exception objects
 *
 * See initatomaca11y() for initialization
 */

PyObject * atomacError;
PyObject * atomacErrorAPIDisabled;
PyObject * atomacErrorInvalidUIElement;
PyObject * atomacErrorUnsupported;
PyObject * atomacErrorCannotComplete;
PyObject * atomacErrorNotImplemented;

/*
 * Local functions
 */

static void _sigHandler(int sig);
static void _setError(AXError e, char e_str[]);
static CFTypeRef _PyAttributeValueToCFTypeRef(PyObject *value,
                                             CFTypeRef attrValue);
static PyObject *_newAXUIElementWithRef(AXUIElementRef element,
                                         PyTypeObject *type);
static PyObject *_CFAttributeToPyObject(PyObject *self, CFTypeRef attr);
static void AXUIElement_dealloc(atomac_AXUIElement *self);
static PyObject *AXUIElement_new(PyTypeObject *type,
                                 PyObject *args,
                                 PyObject *kwds);
static PyObject *AXUIElement_richcmp(PyObject *a, PyObject *b, int op);
static PyObject *AXUIElement_getPid(atomac_AXUIElement *self);
static PyObject *AXUIElement_getPsnForPid(atomac_AXUIElement *self,
                                              PyObject *args);
static PyObject *AXUIElement_getAttributes(atomac_AXUIElement *self);
static PyObject *AXUIElement_getActions(atomac_AXUIElement *self);
static PyObject *AXUIElement_performAction(atomac_AXUIElement *self,
                                           PyObject *args);
static PyObject *AXUIElement_getAttribute(atomac_AXUIElement *self,
                                          PyObject *args);
static PyObject *AXUIElement_setAttribute(atomac_AXUIElement *self,
                                          PyObject *args);
static PyObject *AXUIElement_setString(atomac_AXUIElement *self,
                                       PyObject *args);
static PyObject *AXUIElement_setNotification(atomac_AXUIElement *self,
                                             PyObject *args,
                                             PyObject *kwargs);
static PyObject *AXUIElement_setTimeout(atomac_AXUIElement *self,
                                        PyObject *args);
static PyMethodDef AXUIElement_methods[];
static PyTypeObject atomac_AXUIElementType;
static PyObject *atomac_axenabled(PyObject *self, PyObject *args);
static PyObject *atomac_getfrontmostpid(PyObject *self, PyObject *args);
static PyObject *atomac_getAppRefByPid(PyObject *self, PyObject *args);
static PyObject *atomac_getSystemObject(PyObject *self, PyObject *args);
static PyObject *atomac_getfrontwindowtitle(PyObject *self, PyObject *args);
static PyMethodDef a11ylibMethods[];
void observerCallback(AXObserverRef observer,
                      AXUIElementRef element,
                      CFStringRef notification,
                      void *contextData);
// PyMODINIT_FUNC initatomaca11y(void)

/*
 *-----------------------------------------------------------------------------
 *
 * _sigHandler --
 *
 *      Function to trap keyboard interrupts; primarily to enable keyboard
 *      interrupts during CFRunLoops (which seem to ignore them)
 *
 * Results:
 *      If a CFRunLoop is running (assumed to be one started by the notification
 *      setter), stop the runloop and raise a Python exception, else ignore.
 *
 * Side effects:
 *      None.
 *
 *-----------------------------------------------------------------------------
 */

static void
_sigHandler(int sig)    // IN: Signal raised
                        // Not used here under the assumptions that
                        // a) our run loop is running and so we can stop it
                        // b) this is the foreground process the SIGINT is
                        // sent to
{
   /* Stop the current loop */
   CFRunLoopStop(CFRunLoopGetCurrent());
   /* Set the Python exception string */
   PyErr_SetString(PyExc_KeyboardInterrupt,
                   "Keyboard interrupted Run Loop");
}

/*
 *-----------------------------------------------------------------------------
 *
 * _setError --
 *
 *      Function to set a Python exception based on an Apple AXError
 *
 * Results:
 *      PyErr_SetString will be called and the supplied error text will
 *      be added to the exception.
 *
 * Side effects:
 *      None.
 *
 *-----------------------------------------------------------------------------
 */

static void
_setError(AXError e,    // IN: Apple AXError
          char e_str[]) // IN: Descriptive error message text
{
   char err_str[1024];  // store final error message text

   snprintf(err_str, sizeof(err_str), "%s (AXError %d)", e_str, (int)e);
   if (kAXErrorAttributeUnsupported == e
       || kAXErrorActionUnsupported == e
       || kAXErrorNotificationUnsupported == e) {
      PyErr_SetString(atomacErrorUnsupported, err_str);
      return;
   }
   if (kAXErrorAPIDisabled == e) {
      PyErr_SetString(atomacErrorAPIDisabled, err_str);
      return;
   }
   if (kAXErrorInvalidUIElement == e) {
      PyErr_SetString(atomacErrorInvalidUIElement, err_str);
      return;
   }
   if (kAXErrorCannotComplete == e) {
      PyErr_SetString(atomacErrorCannotComplete, err_str);
      return;
   }
   if (kAXErrorNotImplemented == e) {
      PyErr_SetString(atomacErrorNotImplemented, err_str);
      return;
   }
   PyErr_SetString(atomacError, err_str);
   return;
}

/*
 *-----------------------------------------------------------------------------
 *
 * _PyAttributeValueToCFTypeRef--
 *
 *      Convert a attribute value from Python object to CFTypeRef
 *
 * Results:
 *      Returns a CFTypeRef value or NULL and Python Exception
 *
 *
 *-----------------------------------------------------------------------------
 */

static CFTypeRef
_PyAttributeValueToCFTypeRef(PyObject *value,    // IN: The value to set
                             CFTypeRef attrValue)// IN: Value of the UIElement
{
   CFTypeRef val;
   double x,y;
   double doubleVal;

   if (CFBooleanGetTypeID() == CFGetTypeID(attrValue)) {
      val = kCFBooleanFalse;
      if (Py_True == value){
         val = kCFBooleanTrue;
      }
      return val;
   }

   if (CFStringGetTypeID() == CFGetTypeID(attrValue)) {
      val = PyUnicodeToCFStringRef(value);
      if (NULL == val) {
         return NULL;
      }
      return val;
   }

   if (kAXValueCGPointType == AXValueGetType(attrValue)){
      CGPoint point;
      if (!PyArg_ParseTuple(value, "dd", &x, &y)) {
         return NULL;
      }
      point.x = (CGFloat)x;
      point.y = (CGFloat)y;
      val = (CFTypeRef)(AXValueCreate(kAXValueCGPointType,
                                      (const void *)&point));
      return val;

   }

   if (kAXValueCGSizeType == AXValueGetType(attrValue)) {
      CGSize size;
      if (!PyArg_ParseTuple(value, "dd", &x, &y)) {
         return NULL;
      }
      size.width = (CGFloat)x;
      size.height = (CGFloat)y;
      val = (CFTypeRef)(AXValueCreate(kAXValueCGSizeType,
                                      (const void *)&size));
      return val;
   }

   if (kAXValueCFRangeType == AXValueGetType(attrValue)) {
      CFRange range;
      long a, b;
      if (!PyArg_ParseTuple(value, "ll", &a, &b)) {
         return NULL;
      }
      range.location = (CFIndex)a;
      range.length = (CFIndex)b;
      val = (CFTypeRef)(AXValueCreate(kAXValueCFRangeType,
                                      (const void *)&range));
      return val;
   }

   if (CFNumberGetTypeID() == CFGetTypeID(attrValue)) {
      // Maybe this will need to change if we find any writable ints. Right
      // now we pretty much treat all numbers as floats in terms of setting
      // things.
      if (TRUE == CFNumberIsFloatType(attrValue)) {
         if (!PyNumber_Check(value)) {
            PyErr_SetString(atomacErrorUnsupported,
                            "Error writing supplied value to number type");
            return NULL;
         }
         doubleVal = PyFloat_AsDouble(value);
         val = (CFTypeRef)CFNumberCreate(NULL, kCFNumberDoubleType,
                                         &doubleVal);
         return val;
      }
   }

   // Give up
   PyErr_SetString(atomacErrorUnsupported,
                   "Setting this attribute is not supported yet.");
   return NULL;
}

/*
 *-----------------------------------------------------------------------------
 *
 * _newAXUIElementWithRef --
 *
 *      Create a new Python AXUIElement object from a given Apple
 *      AXUIElementRef
 *
 * Results:
 *      Returns a PyObject AXUIElement or NULL and Python Exception
 *
 * Side effects:
 *      The output of this function is undefined if ownership of the Apple
 *      AXUIElement is not asserted. Make sure it was either Created, Copied,
 *      or otherwise CFRetained. If you are lucky, failing to do so will cause
 *      the code to crash. Effects may actually be more harmful than that...
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *
_newAXUIElementWithRef(AXUIElementRef element, // IN: The Apple AXUIElement
                       PyTypeObject *type)     // IN: Requested type of obj
{
   atomac_AXUIElement *item = (atomac_AXUIElement*)type->tp_alloc(type, 0);
   if (NULL == item) {
      return NULL;
   }
   item->ref = element;

   /* Set the notification-related information here too
      except observerRes; that is set in setNotification()
    */
   item->callbackFn = NULL;
   item->callbackArgs = NULL;
   item->callbackKwargs = NULL;
   item->observerRes = NULL;

   return (PyObject *)item;
}

/*
 *-----------------------------------------------------------------------------
 *
 * _CFAttributeToPyObject --
 *
 *      Convert the result of an A11y attribute get to a Python object
 *
 * Results:
 *      Returns a PyObject representing a string, array of elements, or NULL
 *      and a Python exception on failure
 *
 * Side effects:
 *      Ownership of the CFTypeRef is unchanged.
 *      Ownership of the Python object (if any) is given to the caller.
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *
_CFAttributeToPyObject(PyObject *self,      // IN: Python self object
                       CFTypeRef attrValue) // IN: The data to convert
{
   PyObject *res;
   PyObject *temp;

   if (CFStringGetTypeID() == CFGetTypeID(attrValue)) {
      return CFStringRefToPyUnicode(attrValue);
   }

   if (CFBooleanGetTypeID() == CFGetTypeID(attrValue)) {
	  if (CFBooleanGetValue(attrValue)){
	     Py_RETURN_TRUE;
	  }
	  else Py_RETURN_FALSE;
   }

   if (kAXValueCGSizeType == AXValueGetType(attrValue)) {
      return CGValueToPyTuple(attrValue);
   }

   if (kAXValueCGPointType == AXValueGetType(attrValue)) {
      return CGValueToPyTuple(attrValue);
   }

   if (kAXValueCFRangeType == AXValueGetType(attrValue)) {
      return CGValueToPyTuple(attrValue);
   }

   if (CFNumberGetTypeID() == CFGetTypeID(attrValue)) {
      int intValue;
      double doubleValue;

      if (TRUE == CFNumberGetValue(attrValue, kCFNumberIntType, &intValue)) {
         return Py_BuildValue("i", intValue);
      }
      if (TRUE == CFNumberGetValue(attrValue, kCFNumberDoubleType,
          &doubleValue)) {
          // It's possible that we may just need to default to float after
          // trying int - this is because there may be a precision loss (and
          // thus CFNumberGetValue might return False) if the float is just
          // too precise for a C double.
          return Py_BuildValue("d", doubleValue);
      }
      PyErr_SetString(atomacErrorUnsupported,
                      "Error converting numeric attribute");
      return NULL;
   }

   if (AXUIElementGetTypeID() == CFGetTypeID(attrValue)) {
      CFRetain(attrValue);
      return _newAXUIElementWithRef(attrValue, self->ob_type);
      }

   if (CFArrayGetTypeID() == CFGetTypeID(attrValue)) {
      CFIndex count = 0;
      CFIndex i;

      count = CFArrayGetCount(attrValue);
      res = PyList_New(0);
      if (NULL == res) {
         return NULL;
      }
      for (i=0; i<count; i++) {
         CFTypeRef element = CFArrayGetValueAtIndex(attrValue, i);
         if (NULL != element) {
            if (AXUIElementGetTypeID() == CFGetTypeID(element)) {
               CFRetain(element);
               temp = _newAXUIElementWithRef(element, self->ob_type);
               if (NULL == temp) {
                  // This is a potential leak. We build an array and increment
                  // ref counts and simply discard any progress if there is an
                  // error. Ultimately we should unwind the array and clean up.
                  return NULL;
               }
               if (PyList_Append(res, (PyObject *)temp) == -1) {
                  return NULL;
               }
            }  // if AXUIELementGetTypeID() == CFGetTypeID(element)
            else if (CFStringGetTypeID() == CFGetTypeID(element)) {
               temp = CFStringRefToPyUnicode(element);
               if (NULL == temp) {
                  return NULL;
               }
               if (PyList_Append(res, (PyObject *)temp) == -1) {
                  return NULL;
               }
            } // if (CFStringGetTypeID() == CFGetTypeID(element))
         } // if NULL != element
      } // for (i=0; i<count; i++)
      return res;
   } // if CFArrayGetTypeID() == CFGetTypeID(attrValue)

   PyErr_SetString(atomacErrorUnsupported, "Return value not supported yet.");
   return NULL;
}

/*
 *-----------------------------------------------------------------------------
 *
 * AXUIElement_dealloc --
 *
 *      Destructor for AXUIElement objects
 *
 * Results:
 *      None
 *
 * Side effects:
 *      The internal AXUIElementRef is released and the Python object is freed
 *
 *-----------------------------------------------------------------------------
 */

static void
AXUIElement_dealloc(atomac_AXUIElement *self) // IN: Python self object
{
   if (NULL != self->ref) {
      CFRelease(self->ref);
   }
   if (NULL != self->callbackFn) {
      Py_CLEAR(self->callbackFn);
   }
   if (NULL != self->callbackArgs) {
      Py_CLEAR(self->callbackArgs);
   }
   if (NULL != self->callbackKwargs) {
      Py_CLEAR(self->callbackKwargs);
   }
   if (NULL != self->observerRes) {
      Py_CLEAR(self->observerRes);
   }

   self->ob_type->tp_free((PyObject*)self);
}

/*
 *-----------------------------------------------------------------------------
 *
 * AXUIElement_new --
 *
 *      Constructor for AXUIElement objects.
 *
 * Results:
 *      Returns the new object on success or NULL on failure.
 *      NULL result will also throw an exception in Python thanks to tp_alloc
 *
 * Side effects:
 *      On success, memory is allocated for a new Python object
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *
AXUIElement_new(PyTypeObject *type, // IN: Python type object
                PyObject *args,     // IN: Arguments
                PyObject *kwargs)   // IN: Keyword arguments
{
   atomac_AXUIElement *self;

   self = (atomac_AXUIElement *)type->tp_alloc(type, 0);
   if (self != NULL) {
      self->ref = NULL;
   }
   return (PyObject *)self;
}

/*
 *-----------------------------------------------------------------------------
 *
 * AXUIElement_richcmp --
 *
 *      Implements comparison of AXUIElements.
 *
 * Results:
 *      Returns Py_True or Py_False based on result of CFEqual. Returns
 *      TypeError exception if the comparison is unsupported.
 *
 * Side effects:
 *      None
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *
AXUIElement_richcmp(PyObject *a, PyObject *b, int op)
{
   int result = 0;

   if (Py_EQ != op && Py_NE != op) {
      PyErr_SetString(PyExc_TypeError,
                      "Object does not support specified comparison");
      return NULL;
   }

   if (!PyObject_TypeCheck(b, &atomac_AXUIElementType)) {
      // The right hand side of the comparison isn't even one of us.
      Py_RETURN_FALSE;
   }

   // This typecast is safe because we know both sides are AXUIElements
   atomac_AXUIElement *obj1, *obj2;
   obj1 = (atomac_AXUIElement *) a;
   obj2 = (atomac_AXUIElement *) b;

   if ((NULL == obj1->ref) && (NULL == obj2->ref)) {
      Py_RETURN_TRUE;
   }

   if ((NULL == obj1->ref) || (NULL == obj2->ref)) {
      Py_RETURN_FALSE;
   }

   result = CFEqual(obj1->ref, obj2->ref);

   if (Py_EQ == op) {
      if (result) {
         Py_RETURN_TRUE;
      } else {
         Py_RETURN_FALSE;
      }
   } else if (Py_NE == op) {
      if (result) {
         Py_RETURN_FALSE;
      } else {
         Py_RETURN_TRUE;
      }
   }

   PyErr_SetString(PyExc_RuntimeError,
                   "Comparison function failure");
   return NULL;
}

PyDoc_STRVAR(getpid_doc,
             "_getPid() -> int\n\n"
             "Get the PID of the current a11y element.");

/*
 *-----------------------------------------------------------------------------
 *
 * AXUIElement_getPid --
 *
 *      Get the PID of the AXUIElement
 *
 * Result:
 *      A PyObject list of the attributes or NULL and an exception
 *
 * Side effects:
 *      None
 *
 *-----------------------------------------------------------------------------
 */
static PyObject *AXUIElement_getPid(atomac_AXUIElement *self)
{
   AXError err = kAXErrorSuccess;
   pid_t pid = 0;
   PyObject *res;

   err = AXUIElementGetPid(self->ref, &pid);
   if (kAXErrorSuccess != err) {
      _setError(err, "Error retrieving PID");
      return NULL;
   }

   res = Py_BuildValue("i", pid);

   return res;
}

PyDoc_STRVAR(getpsnforpid_doc,
             "_getPsnForPid(pid (int)) -> tuple\n\n"
             "Return the PSN of the given PID as a 2-item tuple:\n"
             "(High part (int), Low part (int))");

/*
 *-----------------------------------------------------------------------------
 *
 * AXUIElement_getPsnForPid --
 *
 *      Get the PSN for the PID of the AXUIElement
 *
 * Result:
 *      A PyTuple representing the PSN or NULL and an exception (The PyTuple
 *      can be used to represent the PSN struct when used with PyObjC calls
 *      e.g. Quartz.CGEventPostToPSN.
 *
 * Side effects:
 *      None
 *
 *-----------------------------------------------------------------------------
 */
static PyObject *
AXUIElement_getPsnForPid(atomac_AXUIElement *self, // IN: Python self object
                         PyObject *args)         // IN: Python args tuple
{
   OSStatus err = noErr;
   pid_t pid = 0;
   ProcessSerialNumber psn;
   // Python object to return:
   PyObject *psnTuple = NULL;

   if (!PyArg_ParseTuple(args, "i", &pid)) {
      return NULL;
   }

   err = GetProcessForPID(pid, &psn);
   if (noErr != err) {
      _setError(err, "Failed to get PSN for PID");
      return NULL;
   }

   psnTuple = Py_BuildValue("(ii)", psn.highLongOfPSN, psn.lowLongOfPSN);
   /* Returning the tuple so no decrement here */

   return psnTuple;
}

PyDoc_STRVAR(getattributes_doc,
             "_getAttributes() -> list\n\n"
             "Get a list of the attributes supported by the object.");

/*
 *-----------------------------------------------------------------------------
 *
 * AXUIElement_getAttributes --
 *
 *      Get a list of attributes on the AXUIElement object
 *
 * Result:
 *      A PyObject list of the attributes or NULL and an exception
 *
 * Side effects:
 *      None
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *
AXUIElement_getAttributes(atomac_AXUIElement *self)  // IN: Python self object
{
   AXError err = kAXErrorSuccess;
   CFArrayRef attrs;
   PyObject *res;

   err = AXUIElementCopyAttributeNames(self->ref, &attrs);
   if (kAXErrorSuccess != err) {
      _setError(err, "Error retrieving attribute list");
      CFRelease(attrs);
      return NULL;
   }

   res = _CFAttributeToPyObject((PyObject*)self, attrs);

   CFRelease(attrs);
   return res;
}

PyDoc_STRVAR(getactions_doc,
             "_getActions() -> list\n\n"
             "Get a list of the actions available on the AXUIElement.");

/*
 *-----------------------------------------------------------------------------
 *
 * AXUIElement_getActions --
 *
 *      Get a list of actions available on the AXUIElement object
 *
 * Result:
 *      A PyObject list of the actions or NULL and an exception
 *
 * Side effects:
 *      None
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *
AXUIElement_getActions(atomac_AXUIElement *self)  // IN: Python self object
{
   AXError err = kAXErrorSuccess;
   CFArrayRef actions;
   PyObject *res;

   if (NULL == self->ref) {
      PyErr_SetString(atomacError, "Not a valid accessibility object");
      return NULL;
   }

   err = AXUIElementCopyActionNames(self->ref, &actions);
   if (kAXErrorSuccess != err) {
      _setError(err, "Error retrieving action names");
      if (NULL != actions) {
         CFRelease(actions);
      }
      return NULL;
   }

   res = _CFAttributeToPyObject((PyObject*)self, actions);

   CFRelease(actions);
   return res;
}

PyDoc_STRVAR(performaction_doc,
             "_performAction(action (str))\n\n"
             "Perform the specified action on the AXUIElement.");

/*
 *-----------------------------------------------------------------------------
 *
 * AXUIElement_performAction --
 *
 *      Perform the specified action on the AXUIElement object
 *
 * Result:
 *      Python None or NULL and an exception
 *
 * Side effects:
 *      None
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *
AXUIElement_performAction(atomac_AXUIElement *self,  // IN: Python self object
                          PyObject *args)          // IN: Python argument tuple
{
   AXError err = kAXErrorSuccess;
   PyObject *requested;
   CFStringRef action;

   // You would think we could use S or U here, but S rejects Unicode strings
   // and U rejects regular strings. So yeah, that doesn't work.
   // Thankfully PyUnicodeToCFStringRef will reject objects that aren't
   // string or unicode.
   if (!PyArg_ParseTuple(args, "O", &requested)) {
      return NULL;
   }

   action = PyUnicodeToCFStringRef(requested);
   if (NULL == action) {
      return NULL;
   }

   err = AXUIElementPerformAction(self->ref, action);
   if (kAXErrorSuccess != err) {
      _setError(err, "Error performing requested action");
      CFRelease(action);
      return NULL;
   }

   CFRelease(action);
   Py_RETURN_NONE;
}

PyDoc_STRVAR(getattribute_doc,
             "_getAttribute(attribute (str)) -> object (any python type)\n\n"
             "Retrieve the specified attribute of the AXUIElement.");

/*
 *-----------------------------------------------------------------------------
 *
 * AXUIElement_getAttribute --
 *
 *      Get the value of the the specified attribute
 *
 * Result:
 *      Python None or NULL and an exception
 *
 * Side effects:
 *      None
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *
AXUIElement_getAttribute(atomac_AXUIElement *self,  // IN: Python self object
                         PyObject *args)          // IN: Python argument tuple
{
   AXError err = kAXErrorSuccess;
   CFTypeRef attrValue;
   PyObject *res;
   PyObject *pattr;
   CFTypeRef attr;

   if (!PyArg_ParseTuple(args, "O", &pattr)) {
      return NULL;
   }

   // Let's ask the A11y interface for attributes
   attr = PyUnicodeToCFStringRef(pattr);
   if (NULL == attr) {
      return NULL;
   }

   err = AXUIElementCopyAttributeValue(
                                       self->ref,
                                       attr,
                                       (CFTypeRef *)&attrValue
                                       );

   if (kAXErrorNoValue == err) {
      CFRelease(attr);
      Py_RETURN_NONE;
   }

   if (kAXErrorSuccess != err) {
      if (kAXErrorNotImplemented == err) {
         _setError(err, "Attribute not implemented");   
      } else {
        _setError(err, "Error retrieving attribute");
      }
      CFRelease(attr);
      return NULL;
   }

   res = _CFAttributeToPyObject((PyObject*)self, attrValue);

   CFRelease(attr);
   CFRelease(attrValue);
   return res;
}

PyDoc_STRVAR(setattribute_doc,
             "_setAttribute(attribute (str), value)\n\n"
             "Set the specified attribute of the AXUIElement to the specified "
             "value.");

/*
 *-----------------------------------------------------------------------------
 *
 * AXUIElement_setAttribute --
 *
 *      Set the specified attribute to the specified value
 *
 * Result:
 *      Python None or NULL and an exception
 *
 * Side effects:
 *      None
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *
AXUIElement_setAttribute(atomac_AXUIElement *self,  // IN: Python self object
                         PyObject *args)          // IN: Python argument tuple
{
   AXError err = kAXErrorSuccess;
   int res = -1;
   PyObject *pattr;
   PyObject *pval;
   CFStringRef attr = NULL;
   CFStringRef val = NULL;
   CFTypeRef attrValue = NULL;
   Boolean settable = FALSE;

   // Parse out arguments for the attr to set and the requested value
   if (!PyArg_ParseTuple(args, "OO", &pattr, &pval)) {
      return NULL;
   }

   // Unlike the getter, the setter doesn't handle traditional sets first.
   // This prevents items from adding to the object dict when subclassed.
   attr = PyUnicodeToCFStringRef(pattr);
   if (NULL == attr) {
      return NULL;
   }

   // Let's see if the element has this attribute
   err = AXUIElementCopyAttributeValue(self->ref,
                                       attr,
                                       (CFTypeRef *)&attrValue
                                       );
   if (kAXErrorSuccess != err) {
      _setError(err, "Error retrieving attribute to set");
      goto end;
   }

   // Attribute is settable or not
   err = AXUIElementIsAttributeSettable(self->ref, attr, &settable);
   if (kAXErrorSuccess != err) {
      _setError(err, "Error querying attribute");
      goto end;
   }
   if (!settable) {
      PyErr_SetString(atomacErrorUnsupported, "Attribute is not settable");
      goto end;
   }

   val = _PyAttributeValueToCFTypeRef(pval, attrValue);
   if (val == NULL) {
      goto end;
   }

   // Set the attribute value
   err = AXUIElementSetAttributeValue(self->ref, attr, val);
   if (kAXErrorSuccess != err) {
      if (kAXErrorIllegalArgument == err) {
         _setError(err, "Invalid value for element attribute");
         goto end;
      }
      _setError(err, "Error setting attribute value");
      goto end;
   }

   // We ran the gauntlet with no errors so...
   res = 0;

end:
   if (attr != NULL) {
      CFRelease(attr);
   }
   if (val != NULL) {
      CFRelease(val);
   }
   if (attrValue != NULL) {
      CFRelease(attrValue);
   }
   if (0 == res) {
      Py_RETURN_NONE;
   }
   return NULL;
}

PyDoc_STRVAR(setstring_doc,
             "_setString(attribute (str), str)\n\n"
             "Set the specified attribute of the AXUIElement to the specified "
             "string.  Useful for password fields when the normal setter "
             "fails.");

/*
 *-----------------------------------------------------------------------------
 *
 * AXUIElement_setString --
 *
 *      Set the specified attribute to the specified string
 *
 *      Useful for password fields when the normal setter fails
 *
 * Result:
 *      Python None or NULL and an exception
 *
 * Side effects:
 *      None
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *
AXUIElement_setString(atomac_AXUIElement *self,  // IN: Python self object
                      PyObject *args)          // IN: Python argument tuple
{
   AXError err = kAXErrorSuccess;
   PyObject *requested;
   PyObject *string;
   CFStringRef attribute;
   CFStringRef value;

   // Parse out objects for the requested attribute and the value
   if (!PyArg_ParseTuple(args, "OO", &requested, &string)) {
      return NULL;
   }

   attribute = PyUnicodeToCFStringRef(requested);
   if (NULL == attribute) {
      return NULL;
   }

   value = PyUnicodeToCFStringRef(string);
   if (NULL == value) {
      return NULL;
   }

   err = AXUIElementSetAttributeValue(self->ref, attribute, value);
   if (kAXErrorSuccess != err) {
      _setError(err, "Error setting attribute to string");
      CFRelease(attribute);
      CFRelease(value);
      return NULL;
   }

   CFRelease(attribute);
   CFRelease(value);
   Py_RETURN_NONE;
}

PyDoc_STRVAR(setnotification_doc,
             "_setNotification(timeout (int), notification (str), ...) -> bool"
             "\n\n"
             "Set a notification for some UI event to occur on the given "
             "AXUIElement in the given timeout.\n\n"
             "Additional optional parameters include in order:\n"
             "- Python callback function (whose return value evaluates to "
             "bool\n"
             "-- Callback args (tuple)\n"
             "-- Callback keyword args (dictionary)\n\n"
             "If Callback args are non-null, the element returned by the "
             "python callback is returned in the first argument in the args "
             "tuple. If only keyword args are provided, this element is not "
             "returned. The callback should not attempt to use any element "
             "returned if the notification is to fire on the destruction of "
             "the element; use of said element in the callback will cause a "
             "hang.");

/*
 *-----------------------------------------------------------------------------
 *
 * AXUIElement_setNotification --
 *
 *      Set a notification on a given element to fire when a specified event
 *      occurs.
 *
 * Parameters:
 *      timeout value (int), notification to observe (string constant)
 *
 * Optional:
 *      Python callback function (must return value that can be evaluated to
 *      True or False
 *      If callback is provided, will also have to provide the callback
 *      arguments.  If callback arguments are provided, they MUST be provided as
 *      - Args: required / positional args provided as a tuple
 *      - Kwargs: Keyword args provided as a dictionary (whose values match the
 *        keyword args in the python function declaration).
 *      - NOTE: If args is non-NULL, the element returned by the python callback
 *        is always returned in the first argument to the callback.
 *        If the callback doesn't need to use the returned element, it can be
 *        ignored by the callback.  If keyword args only are provided, the
 *        element is NOT returned.
 *        Note also that the callback should not attempt to use any element
 *        returned if the notification to watch is the removal / destruction of
 *        the element; use of said element in the callback will cause a hang.
 *
 * Results:
 *      Python Boolean True (non-zero int) or False (0);
 *      or NULL and an exception on failure.
 *
 * Side effects:
 *      Sets an attribute on the ATOMac object.
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *
AXUIElement_setNotification(atomac_AXUIElement *self, // IN: Python self object
                            PyObject *args,     // IN: Python arguments tuple
                            PyObject *kwargs)   // IN: Python keyword args dict
{
   pid_t pid;

   /* Arguments to be passed in from caller */
   int timeout = 0;
   PyObject *notificationStr;
   PyObject *callbackFn = NULL;
   PyObject *callbackArgs = NULL;
   PyObject *callbackKwargs = NULL;

   /* List of expected keyword arguments; includes the required args too */
   static char *kwList[] = {"timeout", "notification",
                            "callback", "callbackArgs", "callbackKwargs", NULL};

   /* AXUIElement provided by the python object itself (have to extract) */
   AXUIElementRef element;

   /* The Core Foundation string type version */
   CFStringRef cfNotification;
   AXObserverRef observer = NULL;

   /* Signal handler variables */
   PyOS_sighandler_t oldSigIntHandler;

   /* Store whether keyboard interrupted or not */
   Boolean interrupted = FALSE;

   /* Arguments that must be present: timeout value, notification to watch;
      If a callback function is specified, any callback args should
      be provided as a tuple; any kwargs as a dictionary
      (to be used with PyObject_Call()).
      In the format string:
      i -> int; S -> Python String Object; O -> Python Object
    */
   if (!PyArg_ParseTupleAndKeywords(args, kwargs, "iO|OOO", kwList,
                                    &timeout, &notificationStr,
                                    &callbackFn, &callbackArgs,
                                    &callbackKwargs)) {
      return NULL;
   }

   /* Set the callback function only if callback function is provided */
   if ((NULL != callbackFn) && (Py_None != callbackFn)) {
      /* Set here */
      if (!PyCallable_Check(callbackFn)) {
         return NULL;
      }
      /* Python docs say that XINCREF and XDECREF increment and decrement the
         reference count of an object and are safe with NULL pointers
       */
      /* Need to add reference for new callback */
      /* Use a temp variable for the assignments */
      PyObject *temp;
      temp = self->callbackFn;;
      Py_INCREF(callbackFn);
      /* Replace old (or NULL) with new */
      self->callbackFn = callbackFn;
      /* Need to subtract reference for previous callback; use CLEAR in case
       it is NULL and to set it to NULL if refcount -> 0 */
      Py_CLEAR(temp);

      /* Check if have to set / provide the args if they're non-NULL */
      if ((NULL != callbackArgs) && (Py_None != callbackArgs )) {
         /* Require that the callbackArgs be provided as a tuple */
         if (!PyTuple_Check(callbackArgs)) {
            PyErr_SetString(PyExc_ValueError,
                            "Callback args not given as a tuple.");
            Py_CLEAR(self->callbackFn);

            return NULL;
         }

         /* Take ownership of callbackArgs */
         /* Use a temp variable in the exchange */
         temp = self->callbackArgs;
         Py_INCREF(callbackArgs);
         self->callbackArgs = callbackArgs;
         /* This may be NULL so use CLEAR */
         Py_CLEAR(temp);
      } else {
         /* Still have to build an empty tuple for args */
         callbackArgs = Py_BuildValue("()");
         if (NULL == callbackArgs) {
            return NULL;
         }
      }

      self->callbackArgs = callbackArgs;

      /* Check if have to set / provide the kwargs if they're non-NULL;
         kwargs can be NULL, unlike args */
      if ((NULL != callbackKwargs) && (Py_None != callbackKwargs)) {
         /* Require that the callbackKwargs be provided as a dict */
         if (!PyDict_Check(callbackKwargs)) {
            PyErr_SetString(PyExc_ValueError,
                            "Callback kwargs not given as a dict.");
            Py_CLEAR(self->callbackArgs);
            return NULL;
         }

         /* Take ownership of callbackKwargs */
         temp = self->callbackKwargs;
         Py_INCREF(callbackKwargs);
         self->callbackKwargs = callbackKwargs;
         Py_CLEAR(temp);
      }
   }

   /* Extract the AXUIElementRef to use */
   element = self->ref;

   /* Set the callback result first */
   Py_INCREF(Py_None);
   self->observerRes = Py_None;

   /* Convert the C string notification to the CFStringRef type */
   cfNotification = PyUnicodeToCFStringRef(notificationStr);

   if (NULL == cfNotification) {
      /* Need to clear Python objects if conversion failed */
      Py_CLEAR(self->callbackFn);
      Py_CLEAR(self->callbackArgs);
      Py_CLEAR(self->callbackKwargs);
      Py_CLEAR(self->observerRes);

      return NULL;
   }

   /* Create observer */
   AXError err = AXUIElementGetPid(element, &pid);
   if (kAXErrorSuccess != err) {
      _setError(err, "Could not get Pid for UI element");

      /* Release previously created objects */
      if (NULL != cfNotification) {
         CFRelease(cfNotification);
      }

      /* Need to clear Python objects too */
      Py_CLEAR(self->callbackFn);
      Py_CLEAR(self->callbackArgs);
      Py_CLEAR(self->callbackKwargs);
      Py_CLEAR(self->observerRes);

      return NULL;
   }
   err = AXObserverCreate(pid, observerCallback, &observer);
   if (kAXErrorSuccess != err) {
      _setError(err, "Could not create observer for notification");

      /* Release previously created objects */
      if (NULL != cfNotification) {
         CFRelease(cfNotification);
      }

      /* Need to clear Python objects too */
      Py_CLEAR(self->callbackFn);
      Py_CLEAR(self->callbackArgs);
      Py_CLEAR(self->callbackKwargs);
      Py_CLEAR(self->observerRes);

      return NULL;
   }

   /* Add notification to observer */
   err = AXObserverAddNotification(observer,
                                   element,
                                   cfNotification,
                                   self);
   if (kAXErrorSuccess != err) {
      _setError(err, "Could not add notification to observer");

      /* Release previously created objects */
      if (NULL != observer) {
         CFRelease(observer);
      }
      if (NULL != cfNotification) {
         CFRelease(cfNotification);
      }

      /* Need to clear Python objects too */
      Py_CLEAR(self->callbackFn);
      Py_CLEAR(self->callbackArgs);
      Py_CLEAR(self->callbackKwargs);
      Py_CLEAR(self->observerRes);

      return NULL;
   }

   /* Add observer source to run loop */
   CFRunLoopAddSource(CFRunLoopGetCurrent(),
                      AXObserverGetRunLoopSource(observer),
                      kCFRunLoopDefaultMode);

   /* Set the signal handlers prior to running the run loop */
   oldSigIntHandler = signal(SIGINT, _sigHandler);
   /* If an error occurs (return value is SIG_ERR), continue as it's not
      fatal */

   /* Run the run loop now */
   int runResult;
   /* Because running the run loop is a blocking action, allow other Python
      threads to run while the run loop is running. */
   Py_BEGIN_ALLOW_THREADS
   runResult = CFRunLoopRunInMode(kCFRunLoopDefaultMode,
                                  timeout,
                                  FALSE); // Do not abort the run loop after one
                                          // source is handled; allow for
                                          // multiple attempts until timeout
                                          // or loop is stopped
   Py_END_ALLOW_THREADS

   /* Restore the original signal handler only if it wasn't an error before*/
   if (SIG_ERR != oldSigIntHandler) {
      signal(SIGINT, oldSigIntHandler);
   }

   /* Set the Boolean for keyboard interrupt */
   if (PyExc_KeyboardInterrupt == PyErr_Occurred()) {
      interrupted = TRUE;
      /* Normally would exit here; however, rather than copying the clean-up
         calls here, fall through and check at end */
   }

   /* When the run loop has completed, remove the sources from the run loop */
   if (CFRunLoopContainsSource(CFRunLoopGetCurrent(),
                               AXObserverGetRunLoopSource(observer),
                               kCFRunLoopDefaultMode)) {
      CFRunLoopRemoveSource(CFRunLoopGetCurrent(),
                            AXObserverGetRunLoopSource(observer),
                            kCFRunLoopDefaultMode);
   }

   /* Remove the notification from the observer */
   err = AXObserverRemoveNotification(observer,
                                      element,
                                      cfNotification);
   if (kAXErrorSuccess != err) {
      /* Make a note of the problem */
      _setError(err, "Could not remove notification from observer");

      /* Then clean up created objects */
      if (NULL != cfNotification) {
         CFRelease(cfNotification);
      }
      if (NULL != observer) {
         CFRelease(observer);
      }

      Py_CLEAR(self->callbackFn);
      Py_CLEAR(self->callbackArgs);
      Py_CLEAR(self->callbackKwargs);
      Py_CLEAR(self->observerRes);

      return NULL;
   }

   /* Then clean up created objects */
   if (NULL != cfNotification) {
      CFRelease(cfNotification);
   }
   if (NULL != observer) {
      CFRelease(observer);
   }

   /* Clear Python references created for the callback info and reset to NULL */
   /* Py_CLEAR is safe for objects that are set to NULL; otherwise will
      decrement the count.  If count reaches 0, will set reference to NULL
    */
   Py_CLEAR(self->callbackFn);
   Py_CLEAR(self->callbackArgs);
   Py_CLEAR(self->callbackKwargs);

   /* If earlier we were interrupted then bail since we've cleaned up by now */
   if (interrupted) {
      return NULL;
   }

   /* Return Python object returned from callback
      Currently assuming the value of observerRes to represent desired return
      object of the function
    */
   if (kCFRunLoopRunStopped == runResult) {
      if (PyErr_Occurred()) {
         /* Raise the exception the observer callback set */
         Py_CLEAR(self->observerRes);
         return NULL;
      }

      /* Else assume that the python callback returned ok and return the
         return value from the callback */
      return self->observerRes;
   } else {
      /* Assume that the run loop timed out => False result */
      Py_RETURN_FALSE;
   }
}

PyDoc_STRVAR(settimeout_doc,
             "_setTimeout(timeout (int))\n\n"
             "Set the accessibility timeout for the AXUIElement.");

/*
 *-----------------------------------------------------------------------------
 *
 * AXUIElement_setTimeout --
 *
 *      Set the accessibility API timeout value for a given element or globally.
 *
 * Parameters:
 *      Non-negative float value for accessibility API timeout in seconds
 *
 * Result:
 *      Python None or NULL and an exception
 *
 * Side effects:
 *      Timeout for the accessibility API for the given accessibility object is
 *      changed.
 *
 *      To change the timeout for a particular accessibility object:
 *
 *      From Apple: "Setting the timeout on another accessibility object sets it
 *      only for that object, not for other accessibility objects that are equal
 *      to it.
 *
 *      Setting timeoutInSeconds to 0 for any other accessibility object makes
 *      that element use the current global timeout value."
 *
 *      To change the timeout globally for the existing process:
 *
 *      "Pass the system-wide accessibility object ... if you want to
 *      set the timeout globally for this process.
 *
 *      Setting timeoutInSeconds to 0 for the system-wide accessibility object
 *      resets the global timeout to its default value."
 *      (Currently (at least on Snow Leopard) approximately 6 seconds.)
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *AXUIElement_setTimeout(atomac_AXUIElement *self, // IN: Python
                                                                // self object
                                        PyObject *args)         // IN: Python
                                                                // arguments
                                                                // tuple
{
   AXError err = kAXErrorSuccess;
   AXUIElementRef element = NULL;
   float newTimeout = 0;

   // Conversion of floating numbers offers f (C float) or d (C double)
   // Using f (C float) for now; if C floats are too small then use d (C double)
   // for the conversion.
   if (!PyArg_ParseTuple(args, "f", &newTimeout)) {
      return NULL;
   }

   /* Extract the AXUIElementRef to use */
   element = self->ref;

   if (NULL == element) {
      PyErr_SetString(atomacErrorUnsupported,
                      "Operation not supported on null element references");
      return NULL;
   }


   err = AXUIElementSetMessagingTimeout(element, newTimeout);

   if (kAXErrorIllegalArgument == err) {
      PyErr_SetString(PyExc_ValueError,
                      "Accessibility timeout values must be non-negative");
      return NULL;
   }
   if (kAXErrorInvalidUIElement == err) {
      _setError(err, "The element reference is invalid");
      return NULL;
   }

   Py_RETURN_NONE;
}


/*
 *-----------------------------------------------------------------------------
 *
 * AXUIElement_methods --
 *
 *      Constant defining the available methods in the AXUIElement type
 *
 *-----------------------------------------------------------------------------
 */
static PyMethodDef
AXUIElement_methods[] = {
   {"_setNotification", (PyCFunction)AXUIElement_setNotification,
    METH_VARARGS | METH_KEYWORDS, setnotification_doc},
   {"_getAttributes", (PyCFunction)AXUIElement_getAttributes, METH_NOARGS,
      getattributes_doc},
   {"_getActions", (PyCFunction)AXUIElement_getActions, METH_NOARGS,
      getactions_doc},
   {"_performAction", (PyCFunction)AXUIElement_performAction, METH_VARARGS,
      performaction_doc},
   {"_getAttribute", (PyCFunction)AXUIElement_getAttribute, METH_VARARGS,
      getattribute_doc},
   {"_setAttribute", (PyCFunction)AXUIElement_setAttribute, METH_VARARGS,
      setattribute_doc},
   {"_setString", (PyCFunction)AXUIElement_setString, METH_VARARGS,
      setstring_doc},
   {"_getPid", (PyCFunction)AXUIElement_getPid, METH_NOARGS,
      getpid_doc},
   {"_getPsnForPid", (PyCFunction)AXUIElement_getPsnForPid, METH_VARARGS,
      getpsnforpid_doc},
   {"_setTimeout", (PyCFunction)AXUIElement_setTimeout, METH_VARARGS,
      settimeout_doc},
   {NULL} // Sentinel
};

/*
 *-----------------------------------------------------------------------------
 *
 * atomac_AXUIElementType --
 *
 *      Constant defining the configuration of the AXUIElement type
 *
 *-----------------------------------------------------------------------------
 */

static PyTypeObject
atomac_AXUIElementType = {
   PyObject_HEAD_INIT(NULL)
   0,                                     // ob_size
   "atomac._a11y.AXUIElement",           // tp_name
   sizeof(atomac_AXUIElement),              // tp_basicsize
   0,                                     // tp_itemsize
   (destructor)AXUIElement_dealloc,       // tp_dealloc
   0,                                     // tp_print
   0,                                     // tp_getattr
   0,                                     // tp_setattr
   0,                                     // tp_compare
   0,                                     // tp_repr
   0,                                     // tp_as_number
   0,                                     // tp_as_sequence
   0,                                     // tp_as_mapping
   0,                                     // tp_hash
   0,                                     // tp_call
   0,                                     // tp_str
   PyObject_GenericGetAttr,               // tp_getattro
   PyObject_GenericSetAttr,               // tp_setattro
   0,                                     // tp_as_buffer
   Py_TPFLAGS_DEFAULT|Py_TPFLAGS_BASETYPE,// tp_flags
   "Apple AXUIElement object",            // tp_doc
   0,                                     // tp_traverse
   0,                                     // tp_clear
   (richcmpfunc)AXUIElement_richcmp,      // tp_richcompare
   0,                                     // tp_weaklistoffset
   0,                                     // tp_iter
   0,                                     // tp_iternext
   AXUIElement_methods,                   // tp_methods
   0,                                     // tp_members
   0,                                     // tp_getset
   0,                                     // tp_base
   0,                                     // tp_dict
   0,                                     // tp_descr_get
   0,                                     // tp_descr_set
   0,                                     // tp_dictoffset
   0,                                     // tp_init
   0,                                     // tp_alloc
   AXUIElement_new,                       // tp_new
};

/*
 * Python module functions
 * These functions are available in atomac._a11y itself, rather than methods
 * of objects.
 */

PyDoc_STRVAR(axenabled_doc,
             "axenabled() -> bool\n\n"
             "Return the status of accessibility on the system.");

/*
 *-----------------------------------------------------------------------------
 *
 * atomac_axenabled --
 *
 *      Function to determine whether A11y is enabled in system preferences or
 *      not.
 *
 * Results:
 *      Python TRUE or FALSE object reflecting the current status.
 *
 * Side effects:
 *      None.
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *
atomac_axenabled(PyObject *self, // IN: Python self object
               PyObject *args) // IN: Python arguments tuple
{
   Boolean result = FALSE;
   result = AXEnabled();
   if (result == TRUE) {
      Py_RETURN_TRUE;
   } else {
      Py_RETURN_FALSE;
   }
}

PyDoc_STRVAR(getfrontmostpid_doc,
             "getfrontmostpid() -> int\n\n"
             "Return the PID of the application in the foreground.");

/*
 *-----------------------------------------------------------------------------
 *
 * atomac_getfrontmostpid --
 *
 *      Function to get the PID of the frontmost application.
 *
 * Results:
 *      Python Integer object with the PID of the frontmost application.
 *
 * Side effects:
 *      None.
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *
atomac_getfrontmostpid(PyObject *self, // IN: Python self object
                     PyObject *args) // IN: Python arguments tuple
{
   pid_t pid;

   pid = getFrontmostPID();
   return Py_BuildValue("i", pid);
}

PyDoc_STRVAR(getapprefbypid_doc,
             "getAppRefByPid(pid (int)) -> AXUIElement reference\n\n"
             "Get an AXUIElement reference to the application specified by "
             "the given PID.");

/*
 *-----------------------------------------------------------------------------
 *
 * atomac_getAppRefByPid --
 *
 *      Get a Python AXUIElement object for the application with the given PID.
 *
 * Results:
 *      AXUIElement Python object or NULL and an exception on failure.
 *
 * Side effects:
 *      On success, a Python object is allocated (and returned to the caller).
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *
atomac_getAppRefByPid(PyObject *self, // IN: Python self object
                    PyObject *args) // IN: Python arguments tuple
{
   pid_t pid;
   AXUIElementRef app;
   PyObject *ret;
   PyObject *type = NULL;

   if (!PyArg_ParseTuple(args, "Oi", &type, &pid)) {
      return NULL;
   }

   if (!(PyType_CheckExact(type) &&
         PyType_IsSubtype((PyTypeObject *)type, &atomac_AXUIElementType))) {
      PyErr_SetString(PyExc_AttributeError, "Unsupported type supplied");
      return NULL;
   }

   app = AXUIElementCreateApplication(pid);
   if (NULL == app) {
      PyErr_SetString(atomacErrorUnsupported, "Error getting app ref");
      return NULL;
   }
   Py_INCREF(type);
   ret = _newAXUIElementWithRef(app, (PyTypeObject *)type);
   return ret;
}

PyDoc_STRVAR(getsystemobject_doc,
             "getSystemObject() -> AXUIElement reference\n\n"
             "Get an AXUIElement reference for the system accessibility "
             "object.");

/*
 *-----------------------------------------------------------------------------
 *
 * atomac_getSystemObject --
 *
 *      Get a Python AXUIElement for the system accessibility object.
 *      The system accessbility object lets you see the focused application and
 *      focused UI element. Other than that, it isn't much fun at all.
 *
 * Results:
 *      AXUIElement Python object or NULL and an exception on failure.
 *
 * Side effects:
 *      On success, a Python object is allocated (and returned to the caller).
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *
atomac_getSystemObject(PyObject *self, // IN: Python self object
                     PyObject *args) // IN: Python arguments tuple
{
   AXUIElementRef app;
   PyObject *ret;
   PyObject *type = NULL;

   if (!PyArg_ParseTuple(args, "O", &type)) {
      return NULL;
   }

   if (!(PyType_CheckExact(type) &&
         PyType_IsSubtype((PyTypeObject *)type, &atomac_AXUIElementType))) {
      PyErr_SetString(PyExc_AttributeError, "Unsupported type supplied");
      return NULL;
   }

   app = AXUIElementCreateSystemWide();
   if (NULL == app) {
      PyErr_SetString(atomacErrorUnsupported, "Error getting a11y object");
      return NULL;
   }
   Py_INCREF(type);
   ret = _newAXUIElementWithRef(app, (PyTypeObject *)type);
   return ret;
}

PyDoc_STRVAR(getfrontwindowtitle_doc,
             "getfrontwindowtitle(pid (int)) -> str\n\n"
             "Return the title of the foreground window of the given PID.");

/*
 *-----------------------------------------------------------------------------
 *
 * atomac_getfrontwindowtitle --
 *
 *      Get the title of the frontmost window from A11y.
 *      This function was a demo and should be removed when the module is
 *      finished.
 *
 * Results:
 *      Python string object or NULL and an exception on failure.
 *
 * Side effects:
 *      None.
 *
 *-----------------------------------------------------------------------------
 */

static PyObject *
atomac_getfrontwindowtitle(PyObject *self, // IN: Python self object
                         PyObject *args) // IN: Python arguments tuple
{
   pid_t pid;
   CFTypeRef windowTitle;
   PyObject *ret;

   if (!PyArg_ParseTuple(args, "i", &pid)) {
      return NULL;
   }
   windowTitle = getFrontMostWindowTitle(pid);
   // must check for null
   ret = CFStringRefToPyUnicode(windowTitle);
   // must check for null
   CFRelease(windowTitle);
   return ret;
}

/*
 *-----------------------------------------------------------------------------
 *
 * a11ylibMethods --
 *
 *      Constant defining all module functions.
 *
 *-----------------------------------------------------------------------------
 */

static PyMethodDef
a11ylibMethods[] = {
   {"axenabled", atomac_axenabled, METH_VARARGS, axenabled_doc},
   {"getfrontmostpid", atomac_getfrontmostpid, METH_VARARGS, getfrontmostpid_doc},
   {"getfrontwindowtitle", atomac_getfrontwindowtitle, METH_VARARGS,
      getfrontwindowtitle_doc},
   {"getAppRefByPid", atomac_getAppRefByPid, METH_VARARGS,
      getapprefbypid_doc},
   {"getSystemObject", atomac_getSystemObject, METH_VARARGS, getsystemobject_doc},
   {NULL, NULL, 0, NULL}        /* Sentinel */
};

/*
 *-----------------------------------------------------------------------------
 *
 * Callbacks --
 *
 *      Callback methods for notifications
 *
 *-----------------------------------------------------------------------------
 */

/*
 *-----------------------------------------------------------------------------
 *
 * observerCallback --
 *
 *      Callback function to fire when an AX Observer sees a specified event
 *
 * Results:
 *      None
 *
 * Side effects:
 *      Observer hit flag is set (0 -> False, 1 -> True, -1 -> Error).
 *
 *-----------------------------------------------------------------------------
 */

void
observerCallback(AXObserverRef observer,     // IN: Observer
                 AXUIElementRef element,     // IN: AXUIElement
                 CFStringRef notification,   // IN: Notification (from
                                             // AXNotificationConstants.h)
                 void *contextData)          // IN: context data
{
   CFIndex buf_size = 0;
   char *newstr;

   /* In case caller provided a callback */
   PyObject *callbackFn = NULL;
   PyObject *callbackArgs = NULL;
   PyObject *callbackKwargs = NULL;
   PyObject *retElem = NULL;     // Store the element returned from callback
   PyObject *callbackRes = NULL; // Store the result of the callback

   PyObject *newCallbackArgs = NULL;
   PyObject *tupleItem = NULL;

   int callbackEval = 0;   // Store the evaluated result of the callback return
                           // value
   Py_ssize_t argSize;     // Store the size of the incoming callbackArgs tuple

   /* Need to cast the contextData to the atomac_AXUIElement type to access
    relevant members (callbacks, etc.)
    */
   atomac_AXUIElement *axObj;
   axObj = (atomac_AXUIElement *)contextData;

   buf_size = CFStringGetMaximumSizeForEncoding(CFStringGetLength(notification),
                                                CFENCODING) + 1;
   newstr = (char *) malloc(buf_size);
   Boolean cfError = CFStringGetCString(notification,
                                        newstr,
                                        buf_size,
                                        CFENCODING);
   if (FALSE == cfError) {
      /* Failed to allocate memory! */
      return;
   }
   free(newstr);

   /* If callback is provided then run it; use callback result to set observer
      result */
   if (NULL != axObj->callbackFn) {
      /* Run the callback here and grab the result; convert to 1 or 0 for
         True or False */

      /* Take ownership of these PyObjects */
      Py_XINCREF(axObj->callbackFn);
      Py_CLEAR(callbackFn);
      callbackFn = axObj->callbackFn;

      Py_XINCREF(axObj->callbackArgs);
      Py_CLEAR(callbackArgs);
      callbackArgs = axObj->callbackArgs;

      Py_XINCREF(axObj->callbackKwargs);
      Py_CLEAR(callbackKwargs);
      callbackKwargs = axObj->callbackKwargs;

      if (0 != PyTuple_Size(callbackArgs)) {
         /* Callback args is non-NULL */
         CFRetain(element);
         retElem = _newAXUIElementWithRef(element, axObj->ob_type);
         if (NULL == retElem) {
            /* Problem creating new object, so set error value and return */
            CFRunLoopStop(CFRunLoopGetCurrent());
            PyErr_SetString(PyExc_RuntimeError,
                            "Could not create new AX UI Element.");
            CFRelease(element);

            /* Cannot really return a value since observerCallback is void */
            return;
         }
         /* Should not CFRelease(element) here as we've assigned it to an
            AXUIElement; should be released when the AXUIElement is
            deallocated */

         argSize = PyTuple_Size(callbackArgs);

         /* Set the first element in the args tuple as the element ref */
         /* PyTuple_SetItem steals the reference to the item being set in the
            tuple so it will manage its reference count henceforth (e.g. for
            retElem; need not decrement its ref count) */
         /* Use PyTuple_New() to create a new tuple since PyTuple_SetItem()
            does not work on existing tuples */
         newCallbackArgs = PyTuple_New((int) argSize);
         if (NULL == newCallbackArgs) {
            PyErr_SetString(PyExc_RuntimeError,
                            "Could not create a new tuple");
            CFRunLoopStop(CFRunLoopGetCurrent());
            return;
         }

         PyTuple_SetItem(newCallbackArgs, 0, retElem);

         int i;
         for (i=1; i < argSize; i++) {
            tupleItem = PyTuple_GetItem(callbackArgs, i);
            /* PyTuple_GetItem() returns a borrowed reference;
               when callbackArgs refcount is decremented to 0, these may
               disappear too unless we take ownership */
            Py_XINCREF(tupleItem);
            PyTuple_SetItem(newCallbackArgs, i, tupleItem);
         }
      } else {
         /* Assign callbackArgs to newCallbackArgs to consolidate the args
            passed to PyObject_Call() */
         /* Use a temp variable to make sure objects don't get accidentally
            destroyed */
         PyObject *temp;
         temp = newCallbackArgs;
         Py_INCREF(callbackArgs);
         newCallbackArgs = callbackArgs;
         Py_CLEAR(temp);
      }

      /* Need to Py_CLEAR callbackRes later */
      /* See http://docs.python.org/c-api/init.html#non-python-created-threads
         Allow C extension modules to call back into a Python function from
         themselves in a threaded context.
       */
      PyGILState_STATE gilState;

      gilState = PyGILState_Ensure();

      callbackRes = PyObject_Call(callbackFn,
                                  newCallbackArgs,
                                  callbackKwargs);

      PyGILState_Release(gilState);

      /* Clear the built newCallbackArgs right after usage,
         as well as the other argument objects */
      Py_CLEAR(newCallbackArgs);
      Py_CLEAR(callbackKwargs);
      Py_CLEAR(callbackArgs);

      if (NULL == callbackRes) {
         /* Observer callback return is void so set PyErr_SetString instead */
         PyErr_SetString(PyExc_RuntimeError,
                         "Python callback failed.");
      } else {
         /* Pass the return value of the python callback to the atomac object */
         PyObject *temp;
         temp = axObj->observerRes;
         Py_INCREF(callbackRes);
         axObj->observerRes = callbackRes;
         Py_XDECREF(temp);

         /* Still stop the runloop based on the Boolean evaluated value of the
            Python callback.
            PyObject_IsTrue() Returns -1 on failure (meaning object cannot be
            evaluated to a Boolean True or False */
         callbackEval = PyObject_IsTrue(callbackRes);
         if (-1 == callbackEval) {
            /* Stop the run loop anyway because the python callback failed */
            CFRunLoopStop(CFRunLoopGetCurrent());
         } else {
            /* Change so that the run loop stops only if the Python callback
               returns True (or equivalent) */
            if (1 == callbackEval) {
               CFRunLoopStop(CFRunLoopGetCurrent());
            }
         }
      }
      /* No need to Py_CLEAR callbackRes as it will be returned to caller */
   } else {
      /* Default: Set the return value in the contextData object cast as
         atomac_AXUIElement */
      /* If no python callback is provided then simply set the return val to
         True and stop the run loop */
      CFRunLoopStop(CFRunLoopGetCurrent());
      PyObject *temp;
      /* Py_True's ref count should be subsequently decremented in the caller */
      temp = axObj->observerRes;
      Py_INCREF(Py_True);
      axObj->observerRes = Py_True;
      Py_XDECREF(temp);
   }

   return;
}

/*
 *-----------------------------------------------------------------------------
 *
 * init_a11y --
 *
 *      Module initialization for atomac._a11y module.
 *
 * Results:
 *      N/A
 *
 * Side effects:
 *      None
 *
 *-----------------------------------------------------------------------------
 */

PyMODINIT_FUNC
init_a11y(void)
{
   PyObject * m;

   if (PyType_Ready(&atomac_AXUIElementType) < 0) {
      return;
   }

   m = Py_InitModule3("atomac._a11y", a11ylibMethods,
                      "Library of Apple A11y functions");

   Py_INCREF(&atomac_AXUIElementType);
   PyModule_AddObject(m, "AXUIElement", (PyObject *)&atomac_AXUIElementType);

   /*
    * Exceptions are initialized here. atomacError subclasses Python's "error"
    * exception. Eventually, these will likely have to be defined in Python
    * and retrieved here.
    */

   atomacError = PyErr_NewException("atomac._a11y.Error", PyExc_StandardError,
                                  NULL);
   Py_INCREF(atomacError);
   PyModule_AddObject(m, "Error", atomacError);

   // Subclasses of atomacError
   atomacErrorAPIDisabled = PyErr_NewException("atomac._a11y.ErrorAPIDisabled",
                                             atomacError, NULL);
   Py_INCREF(atomacErrorAPIDisabled);
   PyModule_AddObject(m, "ErrorAPIDisabled", atomacErrorAPIDisabled);

   atomacErrorInvalidUIElement = PyErr_NewException("atomac._a11y."
                                                  "ErrorInvalidUIElement",
                                                  atomacError, NULL);
   Py_INCREF(atomacErrorInvalidUIElement);
   PyModule_AddObject(m, "ErrorInvalidUIElement", atomacErrorInvalidUIElement);

   atomacErrorUnsupported = PyErr_NewException("atomac._a11y.ErrorUnsupported",
                                             atomacError, NULL);
   Py_INCREF(atomacErrorUnsupported);
   PyModule_AddObject(m, "ErrorUnsupported", atomacErrorUnsupported);

   atomacErrorCannotComplete = PyErr_NewException("atomac._a11y."
                                                "ErrorCannotComplete",
                                                atomacError, NULL);
   Py_INCREF(atomacErrorCannotComplete);
   PyModule_AddObject(m, "ErrorCannotComplete", atomacErrorCannotComplete);

   atomacErrorNotImplemented = PyErr_NewException("atomac._a11y."
                                                "ErrorNotImplemented",
                                                atomacError, NULL);
   Py_INCREF(atomacErrorNotImplemented);
   PyModule_AddObject(m, "ErrorNotImplemented", atomacErrorNotImplemented);
}
