"""
* ***** BEGIN LICENSE BLOCK *****
* Version: GNU GPL 2.0
*
* The contents of this file are subject to the
* GNU General Public License Version 2.0; you may not use this file except
* in compliance with the License. You may obtain a copy of the License at
* http://www.gnu.org/licenses/gpl.html
*
* Software distributed under the License is distributed on an "AS IS" basis,
* WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
* for the specific language governing rights and limitations under the
* License.
* ***** END LICENSE BLOCK ***** 

module utils

Place all common util functions here.
"""
import time
import os
import sys
import traceback

def checkKeysNotEmpty(dict, keys, context=""):
    """
    Description: 
      Given a dictionary, and a list of keys.
      It will check that all the given keys exist on the dictionary.
      If one of the keys doesn't exist, it raises a ValueError exception
    
    Parameters:
      dict - The dictionary to be checked
      keys - The list of keys that are supposed to be in the dictionary
      context - Usually the name of the Class and method on which you're testing for keys
      
    Output:
      Returns True if everything is ok.
      Raises a ValueError exception for the first key it cannot find.
    
    Example:
      utils.checkKeysNotEmpty(myDict,['id','date'],'MyClass.methodBlah')
    """
    for k in keys:
        if dict.has_key(k) == False:
            raise ValueError("%s Error: Missing key '%s'" % (context,k))
    
    return True

def neutralPath(path):
    path = path.replace('/',os.path.sep)
    path = path.replace('\\',os.path.sep)
    return path

def pythonPathAppend(folderName):
    """Use this function to append project folders paths (relative to src/)
       to the PythonPath.  You can use '/' as a path separator, this
       function will take care of it."""
    folderName = neutralPath(folderName)
    sys.path.append(sys.path[0]+os.path.sep+folderName)
    
def isFileEmpty(filePath):
    fp = open(filePath,"r")
    fp.seek(0,2)
    fileSize = fp.tell()
    fp.close()
    del(fp)
    
    return fileSize == 0

def getUserHomeDirectory():
    '''Returns the full path to the user directory for any OS'''
    env_home_variable = {'linux':'HOME',
                         'darwin':'HOME',
                         'windows':'USERPROFILE'}
    
    home_directory = os.getcwd()
    try:
        home_directory = os.environ[env_home_variable[os.uname()[0].lower()]]
    except:
        #Windows has no uname() function available in python
        home_directory = os.environ[env_home_variable['windows']]
    return home_directory

def _t():
    return "%d:%d:%d" % (time.gmtime()[3],time.gmtime()[4],time.gmtime()[5])

DISTINCT_THREADS = {}
def traceQThread(qobj):
    '''Prints a report with all the QThreads and the classes hosted in them.
    Note: One of the smokedest weird tracking-reflection code i've done. Gubs.'''
    global DISTINCT_THREADS
    
    memory_address = id(qobj.thread())
    if not DISTINCT_THREADS.has_key(memory_address):
        DISTINCT_THREADS[memory_address]={qobj.__class__.__name__:1}
    else:
        className = qobj.__class__.__name__
        if not DISTINCT_THREADS[memory_address].has_key(className):
            DISTINCT_THREADS[memory_address][className] = 1
        else:
            current_count = DISTINCT_THREADS[memory_address][qobj.__class__.__name__]
            DISTINCT_THREADS[memory_address][qobj.__class__.__name__]=current_count+1
    
    thread_count = len(DISTINCT_THREADS)
    trace(qobj.__class__.__name__,qobj.thread(),"priority="+str(qobj.thread().priority())+" total_threads=" + str(thread_count))

def dumpQThreads():
    '''Prints the status of a QThread'''
    global DISTINCT_THREADS
    
    for memory_address in DISTINCT_THREADS:
        print "At " + hex(memory_address) + ":"
        for className in DISTINCT_THREADS[memory_address]:
            print "\t"+className+" (" + str(DISTINCT_THREADS[memory_address][className]) + ")"
        print

def trace(className, methodName, msg):
    print "%s -> %s.%s : %s" % (_t(),className,methodName,msg)
    
def getFileName(fullFilePath):
    '''Given a full file path returns the name'''
    #if path ends with "/"
    if fullFilePath.endswith("/") or fullFilePath.endswith("\\"):
        fullFilePath = fullFilePath[:-1]

    fileName = fullFilePath[fullFilePath.rfind(os.path.sep)+1:] #just the name
    
    if fileName == fullFilePath:
        #means we didn't find os.path.sep, and the mime data given has / as separator
        fileName = fullFilePath[fullFilePath.rfind('/')+1:]
        #trace("utils","getFileName","Used / for path separator")
    #trace("utils","getFileName ->", fileName)
    return fileName

def getFileNameNoExt(filename):
    return filename[:filename.rfind('.')]

def getExtFromFileName(filename):
    return filename[filename.rfind('.')+1:]

def isWindows():
    return os.name == 'nt'

def printList(l):
    if l is None:
        print "List is None"
        print
        return
    for x in l:
        print x
    print

def printDict(d):
    if d is None:
        print "Dict is None"
        print
        return
    for x in d:
        print x,"=",d[x]
    print
    
def isWindowContainedInAnyOfAvailableDesktops(window_position):
    from PyQt4.QtGui import QDesktopWidget
    from PyQt4.QtCore import QRect,QPoint
    window_x, window_y = window_position
    
    desktopWidget = QDesktopWidget()
    #nScreens = desktopWidget.numScreens()
    
    closestScreenIndex = desktopWidget.screenNumber(QPoint(window_x,window_y))
    
    closestScreenDimensions = desktopWidget.availableGeometry(closestScreenIndex)
    x_in_screen = window_x <= (closestScreenDimensions.x() + closestScreenDimensions.width()) and window_x >= closestScreenDimensions.x()
    y_in_screen = window_y <= (closestScreenDimensions.y() + closestScreenDimensions.height()) and window_y >= closestScreenDimensions.y()
    return  x_in_screen and y_in_screen

def printSupportedImageFormats():
    from PyQt4.QtGui import QImageReader
    
    formats = QImageReader.supportedImageFormats()
    print "\nSupported Image Formats:"
    for f in formats:
        print "\t" + str(f)
    print "\n"
    
def showTraceback(context=None):
    print
    print "**"
    if context is not None:
        print "\nContext:\n",context,"\n"
    traceback.print_exc(10, file=sys.stdout)
    print "**"
    print

print "Loading paths"
pythonPathAppend('models')
pythonPathAppend('views')
pythonPathAppend('controllers')
pythonPathAppend('lib')
pythonPathAppend('lib/jsonrpc')
pythonPathAppend('lib/simplejson')
pythonPathAppend('tests')
pythonPathAppend('utils')
pythonPathAppend('i18n')
pythonPathAppend('i18n/images')
pythonPathAppend('i18n/images/us_en')