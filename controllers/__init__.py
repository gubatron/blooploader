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

module controllers

A module for the controllers of the GUI.
We'll define a generic Controller class here.
'''

from PyQt4.QtCore import QObject

class Controller(QObject):
    _view_ = None
    
    def __init__(self,view):
        QObject.__init__(self)
        self.setView(view)
        view.setController(self)
    
    def getView(self):
        return self._view_
    
    def setView(self,v):
        self._view_ = v