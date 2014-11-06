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

module views

Here we'll define a generic interface for all classes that are supposed to be views
"""
from PyQt4.QtCore import QObject

class View(QObject):
    
    _controller_ = None
    
    def __init__(self):
        QObject.__init__(self)
    
    def setController(self, controller):
        self._controller_ = controller
        
    def getController(self):
        return self._controller_