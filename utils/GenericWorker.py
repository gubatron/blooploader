'''
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

module utils.GenericWorker


Use this QThread derived class to execute a 
callable on a worker thread
'''
from PyQt4.QtCore import QThread,SIGNAL

class GenericWorker(QThread):
    def __init__(self, callable, *args):
        QThread.__init__(self)
        self.callable = callable
        self.args = args
    
    def run(self):
        #print "GenericWorker.run() -> executing callable",self.callable
        #print "GenericWorker.run() -> arguments:", self.args
        self.callable(*self.args)
        QThread.emit(self,SIGNAL("finishedWork()"))
        #print "GenericWorker, emit finished() (" + str(self) + ":" + str(self.callable) + ")" 
        return