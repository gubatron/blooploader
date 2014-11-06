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

module views.LoginView
"""
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QWidget,QDialog,QVBoxLayout,QHBoxLayout,QPalette
from PyQt4.QtGui import QLabel,QLineEdit,QCheckBox,QPushButton,QPixmap
from PyQt4.QtGui import QMenuBar,QMenu,QIcon,QColor,QStackedLayout
from controllers.ActionManager import ActionManager

import i18n
import os

from __init__ import View

class PairedWidget(QWidget):
	_a_ = None
	_b_ = None
	_layout_ = None

	
	def __init__(self,a,b,orientation='V'):
		'''Builds a widget made of two other widgets.
		a - Widget
		b - Widget
		orientation - 'V' for Vertical, 'H' for Horizontal'''
		QWidget.__init__(self)

		self._a_=a
		self._b_=b
		
		if orientation.upper()=='V':
			self._layout_ = QVBoxLayout()
		elif orientation.upper()=='H':
			self._layout_ = QHBoxLayout()
			
		self._layout_.addWidget(a)
		self._layout_.addWidget(b)
		self.setLayout(self._layout_)
		#utils.traceQThread(self)

class LoginView(QDialog,View):
	_mainLayout_ = None

	#We put all widgets in container widgets,
	#If we add all of them to layouts by themselves we get Bus error
	#when doing mainLayout.addLayout()
	_usernameWidget_ = None
	_passWidget_ = None
	_rememberWidget_ = None
	_buttonsWidget_ = None
	
	_logoLabel_ = None
	_usernameLabel_ = None
	_passwordLabel_ = None
	_usernameLineEdit_ = None
	_passwordLineEdit_ = None
	_rememberCheckbox_ = None
	_registerButton_ = None
	_loginButton_ = None
	_myBloopSiteLink_ = None #QLabel
	_movieWaiting_ = None #Gotta keep a refernce to the .GIF, otherwise it won't send signals to the QLabel
	
	_controller_ = None
	_menuBar_ = None
		
	def __init__(self, parent=None):
		'''
		Initializes all components in the dialog.
		Whoever uses this view, and its controller,
		must letter bind the controller and the view
		using view.setController(c)
		
		The controller then will be able to access
		all the view elements with the getters
		defined in this dummy view class.
		
		The controller can also connect to events
		triggered by this dialog.
		'''
		QDialog.__init__(self)
		View.__init__(self)
		#self.createMenubar()
		#set up the fields
		
		self.setWindowTitle(i18n.LABEL_WINDOW_LOGIN_TITLE)
		imagePath = os.path.join("i18n","images","us_en") 
		self.setWindowIcon(QIcon(os.path.join(imagePath,"bloop.png")))		
		
		#Blooploader Logo
		pixmap = QPixmap(os.path.join('i18n','images','us_en','login_logo.png'))
		assert(not pixmap.isNull())
		self._logoLabel_ = QLabel()
		self._logoLabel_.setPixmap(pixmap)
		
		#login row
		self._usernameLabel_ = QLabel(i18n.LABEL_USERNAME)
		self._usernameLineEdit_ = QLineEdit()
		self._usernameWidget_ = PairedWidget(self._usernameLabel_, self._usernameLineEdit_)

		#password row
		self._passwordLabel_ = QLabel(i18n.LABEL_PASSWORD)
		self._passwordLineEdit_ = QLineEdit()
		self._passwordLineEdit_.setEchoMode(QLineEdit.Password)
		self._passWidget_ = PairedWidget(self._passwordLabel_, self._passwordLineEdit_)
		
		#remember me row
		self._rememberCheckbox_ = QCheckBox(i18n.LABEL_REMEMBER_ME)
		self._rememberWidget_= QWidget() 
		rememberLayout = QHBoxLayout()
		rememberLayout.addStretch()
		rememberLayout.addWidget(self._rememberCheckbox_)
		self._rememberWidget_.setLayout(rememberLayout)
		
		#buttons
		self._loginButton_ = QPushButton(i18n.LABEL_LOGIN)
		self._buttonsWidget_ = QHBoxLayout()
		self._buttonsWidget_.addStretch()
		self._buttonsWidget_.addWidget(self._loginButton_)

		#MyBloop.com Link at the end
		self._myBloopSiteLink_ = QLabel('<a href="http://www.mybloop.com">www.mybloop.com</a>')
		myBloopSiteLinkLayout = QHBoxLayout()
		myBloopSiteLinkLayout.addStretch()
		myBloopSiteLinkLayout.addWidget(self._myBloopSiteLink_)
		myBloopSiteLinkLayout.addStretch()
		
		#Stack em up vertically
		self._mainLayout_ = QVBoxLayout()
		self._mainLayout_.addStretch()
		self._mainLayout_.addWidget(self._logoLabel_,0,Qt.AlignCenter)
		self._mainLayout_.addWidget(self._usernameWidget_)
		self._mainLayout_.addWidget(self._passWidget_)
		self._mainLayout_.addWidget(self._rememberWidget_)
		self._mainLayout_.addLayout(self._buttonsWidget_)
		self._mainLayout_.addLayout(myBloopSiteLinkLayout)
		self._mainLayout_.addStretch()
		
		#Add another layout to show while we wait
		#put all this on a QStackedLayout
		self._passwordLineEdit_.setStyleSheet("border-style: outset; border-width: 1px; border-radius: 3px; border-color: gray; padding: 3px;")
		self._usernameLineEdit_.setStyleSheet("border-style: outset; border-width: 1px; border-radius: 3px; border-color: gray; padding: 3px;")
		self._waitLayout_ = QVBoxLayout()
		self._waitLayout_.setAlignment(Qt.AlignHCenter)

		self._waitLabel_ = QLabel()
		pixmap = QPixmap(os.path.join('i18n','images','us_en','loading.png'))
		self._waitLabel_.setPixmap(pixmap)
		self._waitLayout_.addWidget(self._waitLabel_)
		self._waitLayout_.addStretch()

		self._stackedLayout_ = QStackedLayout()

		waitWidget = QWidget()
		waitWidget.setLayout(self._waitLayout_)

		mainWidget = QWidget()
		mainWidget.setLayout(self._mainLayout_)

		self._stackedLayout_.addWidget(mainWidget)
		self._stackedLayout_.addWidget(waitWidget)

		self._stackedLayout_.setCurrentIndex(0) #main layout

		self.fillBackground()
		loginLayout = QVBoxLayout()
		loginLayout.addLayout(self._stackedLayout_)
		self.setLayout(loginLayout)

	def getLineEditUsername(self):
		return self._usernameLineEdit_
	
	def getLineEditPassword(self):
		return self._passwordLineEdit_

	def getUsernameLabel(self):
		return self._usernameLabel_

	def getPasswordLabel(self):
		return self._passwordLabel_
	
	def getButtonLogin(self):
		return self._loginButton_
	
	def getButtonRegister(self):
		return self._registerButton_
	
	def getLabelMyBloopSiteLink(self):
		'''Returns a QLabel object. 
		This QLabel contains one or more links to MyBloop.com pages.
		It's the responsability of the controller to catch the linkActivated(QString)
		signal to open a browser for the user. The String passed contains the URL'''
		return self._myBloopSiteLink_
	
	def getRememberCheckbox(self):
		return self._rememberCheckbox_
	
	def wantsToBeRemembered(self):
		return self._rememberCheckbox_.checkState() == Qt.Checked
	
	def fillBackground(self):
		"""Fills the background with a solid white"""
		self.palette().setColor(QPalette.Background, QColor(255,255,255))
		self.setAutoFillBackground(True)
		
	def showForm(self):
		self._stackedLayout_.setCurrentIndex(0)
		
	def showWaiting(self):
		self._stackedLayout_.setCurrentIndex(1)

	def createMenubar(self):
		self._menuBar_ = QMenuBar(None)
		
		#Create File Menu
		self._fileMenu_ = QMenu(self)
		am = ActionManager.getInstance()
        #todo add actions from ActionManager
		for action in am.getBloopFileMenuActions():
		    print "MainView.createMenuBar() adding action to file menu", action
		    print self._fileMenu_.addAction(action)
        
		#Create Help Menu
		self._menuBar_.addMenu(self._fileMenu_)
		
		#self.setMenuWidget(self._menuBar_)
		#self._menuBar_.setVisible(True)