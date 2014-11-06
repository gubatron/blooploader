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

module controller.LoginController
'''
from PyQt4.QtCore import SIGNAL,QObject,QUrl,QVariant,QThread,QMutex,QMutexLocker
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QDesktopServices,QMessageBox
import utils
from utils.Employer import Employer
import sys
from models.RemoteSession import RemoteSession
from __init__ import Controller
from AppController import AppController
import threading
import md5

class LoginController(Controller,Employer):

    settings = None
    _ON_SESSION_SETTING_LOCK_ = QMutex()
    SIGNAL_FINISHED = SIGNAL("finishedAttempt()")
    SIGNAL_UPDATE_MESSAGE_AVAILABLE = SIGNAL("updateMessageAvailable()")
    SIGNAL_LOGIN_ERROR = SIGNAL("connError()")
    
    _attemptLoginResult = None
    
    def __init__(self, view):
        Controller.__init__(self,view)
        Employer.__init__(self)
        
        self.getViewInputReferences()
        self.connectSignals()
        self.checkIfCanRemember()

        QObject.connect(self,LoginController.SIGNAL_FINISHED,self.onConnect,Qt.QueuedConnection)
        QObject.connect(self,LoginController.SIGNAL_UPDATE_MESSAGE_AVAILABLE,self.onUpdateMessageAvailable,Qt.QueuedConnection)
        QObject.connect(self,LoginController.SIGNAL_LOGIN_ERROR, self.onLoginError,Qt.QueuedConnection)
        
    def initSettings(self):
        if self.settings is None:
            self.settings = AppController.getInstance().getSettings()
    
    def getViewInputReferences(self):    
        self._usernameLabel_ = self.getView().getUsernameLabel()
        self._passwordLabel_ = self.getView().getPasswordLabel()
        self._buttonLogin_ = self.getView().getButtonLogin()
        self._buttonRegister_ = self.getView().getButtonRegister()
        self._usernameLineEdit_ = self.getView().getLineEditUsername()
        self._passwordLineEdit_ = self.getView().getLineEditPassword()
        self._links_ = self.getView().getLabelMyBloopSiteLink()
        self._remember_ = self.getView().getRememberCheckbox()

    def connectSignals(self):
        QObject.connect(self._buttonLogin_,SIGNAL('clicked()'),self.onLogin)
        QObject.connect(self._links_,SIGNAL('linkActivated(QString)'),self.onLinkActivated)
        QObject.connect(self._usernameLabel_,SIGNAL('linkActivated(QString)'),self.onLinkActivated)
        QObject.connect(self._passwordLabel_,SIGNAL('linkActivated(QString)'),self.onLinkActivated)
    
    def checkIfCanRemember(self):
        self.initSettings()
        
        '''Checks with QSettings if they were remembering'''
        if self.settings.contains('username') and self.settings.contains('password'):
            self.populateDialog()
        else:
            self.clearDialog()
            
    def rememberCurrentCredentials(self):
        self.initSettings()
        self.settings.setValue('username',QVariant(self._usernameLineEdit_.text()))
        self.settings.setValue('password',QVariant(self._passwordLineEdit_.text()))

    def forgetCurrentCredentials(self):
        self.initSettings()
        self.settings.remove('username')
        self.settings.remove('password')
        
    def populateDialog(self):
        self.initSettings()
        savedPass = self.settings.value('password').toString()

        #make pass an md5 hash in case it's not been saved as one
        if len(self.settings.value('password').toString())<32:
            savedPass = md5.md5(savedPass).hexdigest()
            self.settings.setValue('password',QVariant(savedPass))
        
        self._usernameLineEdit_.setText(self.settings.value('username').toString())
        self._passwordLineEdit_.setText(savedPass)
        
        self._remember_.setCheckState(Qt.Checked)
        
    def clearDialog(self):
        '''Clears all the fields and controls'''
        self._usernameLineEdit_.clear()
        self._passwordLineEdit_.clear()
        self._remember_.setCheckState(Qt.Unchecked)

    def onLogin(self):
        '''Signal callback for the login button'''
        username = str(self._usernameLineEdit_.text())
        password = str(self._passwordLineEdit_.text())
        
        if username is "":
            self._usernameLineEdit_.setCursorPosition(0)
            return

        if password is "":
            self._passwordLineEdit_.setCursorPosition(0)
            return

        if len(password) < 32:
            #plain password given.
            #calculate md5 hash
            password = md5.md5(password).hexdigest()
            self._passwordLineEdit_.setText(password)
        
        if self.getView().wantsToBeRemembered():
            self.rememberCurrentCredentials()
        else:
            self.forgetCurrentCredentials()
            
        #now do the actual jsonrpc call to login
        #use AppController for convenience (AppController might use another controller class
        #if it starts getting super big)
        self.disableControls()
        self.hireWorker(self.attemptOpenSession)

    def onConnect(self):
        #When the thread ends it checks if we could create a session, if so, it opens a window
        #THE LESSON LEARNED: Do not attempt to create windows on another thread.
        #It will try to look for a QApp or a painter on THAT thread, and not the original thread.
        self.enableControls()
        
        if AppController.getInstance().getRemoteSession() is not None:
            AppController.getInstance().createMainWindow()
            self.getView().close()
        else:
            print "LoginController.onConnect() - There's no RemoteSession, nothing happens"
            
    def onLoginError(self):
        result = self.getAttemptResult()
        self.enableControls()
    
        if result == False:
            QMessageBox.critical(None, 
                                 'Login failed',
                                 "Login Error.\nPlease try again\n\n(If the problem persists come back later)",
                                 QMessageBox.Ok,
                                 QMessageBox.Ok)

            
        if type(result) == dict and\
           result.has_key('responseType') and\
           result['responseType'] == u"LOGIN_ERROR":
            if result.has_key(u'message') is not None:
                result['message'] = "Invalid username or password. Press the 'Forgot Password' link to recover your password."
                QMessageBox.critical(None, 
                                     'Login failed',
                                     result['message'],
                                     QMessageBox.Ok,
                                     QMessageBox.Ok)
            
        AppController.getInstance().setRemoteSession(None)
            
    def onUpdateMessageAvailable(self):
        '''An update message has been detected while creating a remote session
        the worker thread sends us the information from the RPC response
        This 'result' dictionary should have information about the update message
        
        Depending on the type of UPGRADE_XXXX message we show different QMessageBox dialogs
        
        For some reason it seems several threads are trying to send the message available signal,
        so I'll protect this method with a non-blocking QMutex
        '''
        # Let's show the dialog to prompt an upgrade if the result doesn't even have a message for us.
        import i18n
        result = self.getAttemptResult()
        if not result.has_key('message'):
            result['message'] = i18n.UPDATE_MESSAGE_MANDATORY
            
            upgradeResponse = QMessageBox.warning(None, 
                                                i18n.UPDATE_MESSAGE_WARNING_TITLE,
                                                result['message'],
                                                QMessageBox.Yes | QMessageBox.No,
                                                QMessageBox.Yes);
                      
            # If the user presses yes, open a window to the URL provided                          
            if upgradeResponse == QMessageBox.Yes:
                if not result.has_key(u'url'):
                    from models.mbu_config import meta
                    result[u'url'] = 'http://' + meta['SERVER']
                                            
                QDesktopServices.openUrl(QUrl(result[u'url']))
                sys.exit(0)

        elif result.has_key(u'responseType') and result[u'responseType'] == 'UPGRADE_OPTIONAL':
            # Let's show the dialog to prompt an upgrade                 
            if not result.has_key(u'message'):
                result[u'message'] = i18n.UPDATE_MESSAGE_RECOMMENDED
                
            upgradeResponse = QMessageBox.information(None, 
                                                i18n.UPDATE_MESSAGE_NEW_VERSION_TITLE,
                                                result[u'message'],
                                                QMessageBox.Yes | QMessageBox.No,
                                                QMessageBox.Yes);
                      
            # If the user presses yes, open a window to the URL provided                          
            if upgradeResponse == QMessageBox.Yes:
                if not result.has_key(u'url'):
                    result[u'url'] = 'http://' + meta['SERVER']
                                            
                QDesktopServices.openUrl(QUrl(result[u'url']))
                sys.exit(0)

        elif result.has_key(u'responseType') and result[u'responseType'] == 'UPGRADE_MANDATORY':
            QMessageBox.critical(None, 
                                 i18n.UPDATE_MESSAGE_WARNING_TITLE,
                                 result['message'],
                                 QMessageBox.Ok,
                                 QMessageBox.Ok);
                                 
            if not result.has_key(u'url'):
                result[u'url'] = 'http://' + meta['SERVER']
                                            
            QDesktopServices.openUrl(QUrl(result[u'url']))
            sys.exit(0)
                
        #self.emit(self.SIGNAL_FINISHED)
        
    def setAttemptResult(self,result):
        self._attemptLoginResult = result
        
    def getAttemptResult(self):
        return self._attemptLoginResult
        
    def attemptOpenSession(self):
        '''
        This method attempts to open the session on a thread
        to not lock the UI while its waiting for an answer.
        
        On Sucess it passes the AppController a new Session Object.
        And tells the App Controller to create/refresh the main window.
        
        Since this method is created on a Thread, it should not try to invoke
        the creation of another window, or try to post any signals.
        
        It should just let us know that its done.
        '''
        result = False
        self.setAttemptResult(result)
        uname = str(self._usernameLineEdit_.text())
        passwd = str(self._passwordLineEdit_.text())
        #print "LoginController.attemptOpenSession() -> pass sent: ["+passwd+"]"
        remoteSession = None

        try:
            remoteSession = RemoteSession()
            result = remoteSession.create(uname,passwd)
            self.setAttemptResult(result)
        except Exception,e:
            remoteSession = None
            self.setAttemptResult(False)
            utils.trace("LoginController","attemptOpenSession - caught exception from create()",e.args)
            if len(e.args)>0 and type(e.args[0]) == dict:
                #FITIM: We might want to pass status=1 when there's a UPGRADE_MANDATORY
                result = e.args[0] #there might be some results, even though status was 0 on the raw response
                self.setAttemptResult(result)

        #On Login sucess
        if result and remoteSession:
            AppController.getInstance().setRemoteSession(None)
            AppController.getInstance().setRemoteSession(remoteSession)
            AppController.getInstance().setUserProfile(remoteSession.getRemoteUserProfile())
            self._buttonLogin_.setDisabled(False)
        else:
            AppController.getInstance().setRemoteSession(None)

        if (type(result)==bool and result==False) or\
           (type(result)==dict and result.has_key(u'responseType') and\
            result[u'responseType']=="LOGIN_ERROR"):
            self.emit(LoginController.SIGNAL_LOGIN_ERROR)
            return
        
        #If there's an update message end this thread and send a signal to the parent thread with the 
        #response from remoteSession.create, which should have the update message
        if result.has_key(u'responseType') and result[u'responseType'].startswith("UPGRADE_"):
            self.emit(LoginController.SIGNAL_UPDATE_MESSAGE_AVAILABLE)
            return

        self.emit(LoginController.SIGNAL_FINISHED)
            
    def onLinkActivated(self,url):
        QDesktopServices.openUrl(QUrl(url))

    def enableControls(self):
        self.getView().showForm()
        
    def disableControls(self):
        self.getView().showWaiting()