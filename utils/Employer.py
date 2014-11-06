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

module utils.Employer

Any class who needs to 'employ' several GenericWorker threads during its
life time should extend Employer.

This way it can add new worker references and not worry about leaving
dirty references behind.
'''
from PyQt4.QtCore import QObject,SIGNAL
from GenericWorker import GenericWorker
import utils

class Employer(QObject):
    THE_BOSS = None #There will be only one employer now.
    _workers = None
    
    def __init__(self):
        QObject.__init__(self)

    def getInstance(self):
        if Employer.THE_BOSS is None:
            Employer.THE_BOSS = Employer()
        return Employer.THE_BOSS
        
    def hireWorker(self,callbackMethod,*args):
        '''
        Use this method to start a GenericWorker thread which will run the callbackMethod and its arguments
        
        callbackMethod: a reference to the method you want the worker to execute
        args: an optional number of parameters to pass to the callback method
        
        returns a reference to the GenericWorker in case you need to wait for it.
        '''
        debug = str(callbackMethod)
        #utils.trace("Employer","hireWorker","Hired for " + debug + " (" + str(self.getInstance()) + ")")
        worker = GenericWorker(callbackMethod, *args)
        self.getInstance()._addNewWorker(worker)
        worker.start()
        return worker
    
    def resetWorkers(self):
        self._workers= []
        
    def getWorkers(self):
        return self._workers
        
    def acceptResignation(self):
        if self.getWorkers() is None or len(self.getWorkers()) == 0:
            #utils.trace("Employer","acceptResignation","Received a resignation but I've no workers")
            return
        
        #utils.trace("Employer", "acceptResignation:", "Will Fire someone yay!. Total Workers: " + str(len(self.getInstance().getWorkers())))
        for t in self.getWorkers():
            if t.isFinished():
                self.getInstance().getWorkers().remove(t)
                #utils.trace("Employer", "acceptResignation:", "I quit! ("+str(self)+"). Total Workers: " + str(len(self.getInstance().getWorkers())))

    def _addNewWorker(self,w):
        if self.getInstance().getWorkers() is None:
            self.getInstance().resetWorkers()

        #utils.trace("Employer","_addNewWorker","adding worker, I am " + str(self.getInstance()))
        self.getInstance().getWorkers().append(w)
        #utils.trace("Employer", "_addNewWorker:", "Added worker ("+str(w)+"). Total Workers: " + str(len(self.getInstance().getWorkers())))
        self.connect(w,SIGNAL('finishedWork()'),self.getInstance().acceptResignation)
