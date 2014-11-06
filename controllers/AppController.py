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

module controller.AppController
'''
from PyQt4.QtCore import QObject, QSettings
from PyQt4.QtGui import QSystemTrayIcon
import utils
from utils.Employer import Employer
from views.MainView import MainView
from MainViewController import MainViewController


class AppController(Employer):
    '''
    Singleton main Application Controller

    This guy here should have refereces to all controllers.
    It can also implement general functionality expected to be reachable from a
    centric place.
    
    Its also responsible for bootstrapping application level settings
    using QSettings
    '''
    INSTANCE = None
    _settings_ = None
    
    _remoteSession_ = None #json rpc bridge object
    _userProfile_ = None
    _loginView_ = None
    _mainView_ = None
    
    #Controllers
    _loginController_ = None
    _mainViewController_ = None
    _trayIconController_ = None
    
    def __init__(self):
        """
        Returns an instance of AppController.
        You're not supposed to use this constructor, use AppController.getInstance() instead.
        
        Here Application Settings handler is initialized.
        """
        Employer.__init__(self)
        self.initSettings()


    @staticmethod
    def getInstance():
        if AppController.INSTANCE is None:
            AppController.INSTANCE = AppController()
        return AppController.INSTANCE
    
    def showLoginView(self):
        if self._loginView_ is None:
            #Do this imports here to avoid circular references
            from views.LoginView import LoginView
            from controllers.LoginController import LoginController
            
            #Create the login view object, and get the references for it and its controller
            self.setLoginView(LoginView())
            self.setLoginController(LoginController(self.getLoginView())) 
            #The Controller() constructor tells the view about its new controller

        self.getLoginView().show()
        
    
    def initSettings(self,reset=False):

        if reset:
            self._settings_ = None
            
        if self._settings_ is None:
            self._settings_ = QSettings('mybloop.com','blooploader',self)
    
    def getSettings(self,reset=False):
        self.initSettings(reset)
        return self._settings_
    
    def setLoginView(self, view):
        self._loginView_ = view
        
    def getLoginView(self):
        return self._loginView_
    
    def setLoginController(self,controller):
        self._loginController_ = controller
        
    def getLoginController(self):
        return self._loginController_
    
    def setMainView(self, view):
        self._mainView_ = view
        
    def getMainView(self):
        return self._mainView_
    
    def getMainViewController(self):
        return self._mainViewController_
    
    def setRemoteSession(self,session):
        self._remoteSession_ = session
        
    def getRemoteSession(self):
        return self._remoteSession_
    
    def setUserProfile(self, up):
        self._userProfile_ = up
        #utils.trace('AppController','setUserProfile',self._userProfile_)

    def getUserProfile(self):
        return self._userProfile_

    def createMainWindow(self):
        '''
        Creates the Main Window and bootstraps the Bloop Tree.
        '''
        self._mainView_ = MainView.getInstance()
        self._mainViewController_ = MainViewController(self._mainView_)
        self._mainView_.createComponents()
        
        # Expand the data on the Friend Tree by default
        if self.getMainViewController().getFriendsTreeController() is not None:
            self.getMainViewController().getFriendsTreeController().buildTree()

        self.getMainViewController().bootstrapComponents()
        
        #We do all this at this point (and not on the MainView Controller)
        #since we'd like to make sure we have a controller before invoking
        #these methods.
        self._mainView_.show()
        self._mainView_.createMenuBar()
        
        #IconTray
        possibleTrayController = self._mainView_.initIconTray(self)
        
        if possibleTrayController:
            self.setTrayIconController(possibleTrayController)
        
        self.getMainViewController().restoreSizes()
        
        #Try to recover from unfinished uploads if any
        #self.hireWorker(self.getMainViewController().getUploadManagerViewController().tryRestoringUploads)
        #cant put this on a thread, windows claims the upload manager timer will be started from another thread
        self.getMainViewController().getUploadManagerViewController().tryRestoringUploads()

    def saveMainWindowSizes(self):
        self.getMainViewController().saveSizes()
        
    def logout(self):
         '''
         Destroys the Main Window and shows back the login view.
         
         TODO: Make the TrayIcon dissapear once a session ends.
         '''
         self.saveMainWindowSizes()
         self.getMainView().hide()
         self.getMainView().deleteLater()
         
         if self.getTrayIconController():
             self.getTrayIconController().logout()
         
         MainView.INSTANCE = None
         
         self.showLoginView()
         self.getRemoteSession().destroy()
         self.setRemoteSession(None)

         from models.upload_manager import UploadManager
         UploadManager.getInstance().shutdown()
         
    def setTrayIconController(self,trayIconController):
        self._trayIconController_ = trayIconController
        
    def getTrayIconController(self):
        return self._trayIconController_