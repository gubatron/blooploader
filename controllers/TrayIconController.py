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

module controllers.TrayIconController
"""
#from AppController import AppController
from ActionManager import ActionManager
from __init__ import Controller

class TrayIconController(Controller):
    '''
    Use this class to manipulate the TrayIcon.
    If you need to get a hold of the actual Qt object
    use .getView()
    
    TODO: Add SIGNAL/SLOTS to bring MainWindow back to action if IconTray is clicked
          Make the application hide when MainWindow is closed, not shutdown
    '''
    INSTANCE = None
    _remoteSession = None
    _appController = None
    
    '''
    Controls all the logic and states of the TrayIcon.
    '''
    def __init__(self, view):
        Controller.__init__(self, view)
        self.updateRemoteSession()
        
    @staticmethod
    def getInstance():
        if TrayIconController.INSTANCE is None:
            from views.TrayIconView import TrayIconView
            TrayIconController.INSTANCE = TrayIconController(TrayIconView())
        return TrayIconController.INSTANCE
    
    def getRemoteSession(self):
        return self._remoteSession
    
    def setRemoteSession(self,remoteSession):
        self._remoteSession = remoteSession
        
    def updateRemoteSession(self):
        if self.getAppController() is not None:
            self.setRemoteSession(self.getAppController().getRemoteSession())
        
    def logout(self):
        self.setRemoteSession(None)
        self.getView().hide()
        
    def setAppController(self,appController):
        self._appController = appController
        
    def getAppController(self):
        return self._appController