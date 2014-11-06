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

module views.MainView
"""
from PyQt4.QtGui import QMainWindow,QWidget,QVBoxLayout,QPixmap,QIcon,\
                        QSplitter,QScrollArea,QSystemTrayIcon,QMenu
from PyQt4.QtCore import Qt
from PyQt4.QtCore import QObject,SIGNAL

import i18n
import utils
import os
from __init__ import View
from UploadManagerView import UploadManagerView
from controllers.ActionManager import ActionManager
from controllers.TrayIconController import TrayIconController

class MainView(QMainWindow, View): #Multiple inheritance rocks, I love you Python
    INSTANCE = None
    ICONS = None #dir, the keys are the file extensions
    
    _trayIcon_ = None
    
    _bloopTree_ = None #The BloopTree
    _uploadManagerView_ = None #Upload manager to show how uploads are doing
    _friendsTree_ = None #Friends Tree
    _groupsTree_ = None #Friends Tree
    
    _treesWidget_ = None #Contains the Tree widgets
    _treesLayout_ = None #Layout for the _treesWidget_
    
    _menuBar_ = None
    _fileMenu_ = None
    _helpMenu_ = None
    
    _uploadManagerScrollArea_ = None
    _uploadManagerContainer_ = None
    vLayout = None
    
    def __init__(self):
        '''
        This constructor just creates the window, loads the icons and menu bar.
        If you want to see the real creation of the window, this class works
        as a singleton, and you should see AppController.createMainWindow()
        '''
        QMainWindow.__init__(self)
        
        View.__init__(self)
        self.setAcceptDrops(True)
        #utils.traceQThread(self)
        self.__mainLayout__ = QVBoxLayout()
        imagePath = os.path.join("i18n","images","us_en") 
        self.setWindowIcon(QIcon(os.path.join(imagePath,"bloop.png")))  
        self.setMouseTracking(True)
        
        self._fileMenu_ = None
        self.vLayout = None     

        #Load the icons for the file types
        self.loadIcons()
        assert(self.ICONS is not None and len(self.ICONS) > 0)
        
        self.showStatusBarDefaultText()
        
    def showStatusBarDefaultText(self):
        self.statusBar().showMessage(i18n.LABEL_BLOOPTREE_STATUS_BAR)
        
    @staticmethod
    def getInstance():
        if MainView.INSTANCE is None:
            MainView.INSTANCE = MainView()
        return MainView.INSTANCE

    def getBloopTree(self):
        return self._bloopTree_
    
    def getUploadManagerViewInsideScrollArea(self):
        '''
        Returns a UploadManagerView widget.
        The upload manager shows the status of the uploads
        '''
        
        if self._uploadManagerScrollArea_ is None:
            self._uploadManagerScrollArea_ = QScrollArea(self)
            self._uploadManagerScrollArea_.setWidget(self._uploadManagerView_)
            self._uploadManagerScrollArea_.setWidgetResizable(True)

        
        return self._uploadManagerScrollArea_
    
    def getUploadManagerView(self):
        return self._uploadManagerView_

    def getFriendsTree(self):
        return self._friendsTree_
    
    def createMenuBar(self):
        #Create File Menu
        self._fileMenu_ = self.menuBar().addMenu(i18n.MENU_FILE)
        self._helpMenu_ = self.menuBar().addMenu(i18n.MENU_HELP)
        
        
        am = ActionManager.getInstance()
        for action in am.getBloopFileMenuActions():
            self._fileMenu_.addAction(action)
            
        for action in am.getBloopHelpMenuActions():
            self._helpMenu_.addAction(action)
            
        
    def createBloopTreeComponent(self):
        from BloopTreeView import BloopTree
        self._bloopTree_ = BloopTree(None)

        ''' Bloop Tree Settings '''
        # Added the line below because if we don't supply it, on Windows there's a weird
        # horizontal scroll bar that stretches so far (for no reason!)
        self._bloopTree_.setColumnCount(2) # The number of columns to show on the My Files BloopTree        
        self._bloopTree_.setColumnWidth(0, 250) # The width (pixels) of the first column (dir / file names)
        self._bloopTree_.setColumnWidth(1, 50) # The width (pixels) of the second column (file size)

        # Apply the Selection Mode for this tree
        self._bloopTree_.setSelectionMode(self._bloopTree_.ExtendedSelection)

    def createUploadManagerComponent(self):
        self._uploadManagerView_ = UploadManagerView(None)
        #print "MainView._uploadManagerView_ @ ", hex(id(self._uploadManagerView_))
        
    def createFriendTreeComponent(self):
        from BloopTreeView import BloopTree        
        self._friendsTree_ = BloopTree(self)

        ''' Friends Tree Settings '''
        self._friendsTree_.setColumnCount(2) # The number of columns to show on the Friends tree
        self._friendsTree_.setColumnWidth(0, 300)
        self._friendsTree_.setColumnWidth(1, 50)
        self._friendsTree_.setHeaderLabels([i18n.LABEL_FRIENDSTREE_TITLE_BAR, i18n.LABEL_STATUS])
        
    def getUploadManagerContainer(self):
        '''
        Returns the UploadManager and a Toolbar all contained on a single widget.
        
        If they have not been instanciated they're prepared here.
        '''
        #The big container, which uses a vertical layout
        if self._uploadManagerContainer_ is None:
            self._uploadManagerContainer_ = QWidget()
            
            layout = QVBoxLayout()
            
            #We add the toolbar with the buttons
            layout.addWidget(self._uploadManagerView_.getToolBar())
            
            #And we add the UploadManagerView inside a scroll area
            layout.addWidget(self.getUploadManagerViewInsideScrollArea())
            
            #apply the layout
            self._uploadManagerContainer_.setLayout(layout)
            
        return self._uploadManagerContainer_

    
    def createComponents(self):
        '''
        Instanciates and loads the main components of the Blooploader.
        Asks the controller of this window to initialize controller objects
        for the trees.
        
         -> Bloop Tree
         -> Upload Manager View
         -> Friend's Tree
        '''
        #Let's hide this for now
        self.createBloopTreeComponent()
        self.createUploadManagerComponent()
        #self.createFriendTreeComponent()
        
        self._treesWidget_ = QSplitter(Qt.Vertical)
        
        if self.getBloopTree() is not None:
            self._treesWidget_.addWidget(self.getBloopTree())
            
        if self.getUploadManagerViewInsideScrollArea() is not None:
            self._treesWidget_.addWidget(self.getUploadManagerContainer())
        
        if self.getFriendsTree() is not None:
           self._treesWidget_.addWidget(self.getFriendsTree())
        
        self._treesWidget_.setStretchFactor(1,10)
        self._treesWidget_.setSizes([200,50,50])

        #connect splitter moved to save it on the settings for next time
        QObject.connect(self._treesWidget_,SIGNAL('splitterMoved(int,int)'), self.getController().onSplitterMoved)
        self.setCentralWidget(self._treesWidget_)
        self.getBloopTree().setFocus()
        self.getController().restoreSizes()
    
    def loadIcons(self):
        #TODO: Have an icon for unknown file extension.
        imagePath = os.path.join("i18n","images","us_en") #TODO: this has to change for a QSetting 
        fileList = os.listdir(imagePath)

        if self.ICONS is None:
            self.ICONS = {}

            for name in fileList:
                if name.startswith('.'):
                    continue
                key = name[:name.find('.')]
                
                bufferQPixmap = QPixmap(os.path.join(imagePath,name))
                self.ICONS[key] = bufferQPixmap
                bufferQPixmap = None
                del(bufferQPixmap)
                
    def getIcons(self):
        return self.ICONS
    
    def getSplitterWidget(self):
        return self._treesWidget_
    
    def resizeEvent(self, resizeEvent):
        if self.getController() is None:
            return
        
        self.getController().saveSizes()
        
    def moveEvent(self, moveEvent):
        if self.getController() is None:
            return

        self.getController().saveSizes()
    
    ############ DRAG AND DROP EVENTS ON MAIN VIEW #######################
    def dragEnterEvent(self, dragEnterEvent):
        utils.trace('MainView','dragEnterEvent',dragEnterEvent)
  
    def mouseMoveEvent(self,mouseEvent):
        #Attempts to update hovered items on the trees, since the trees don't seem to be having
        #focus when popup menues are shown.
        self.getBloopTree().updateHoveredItemAt(mouseEvent.x(), mouseEvent.y()) #maybe QCursor.pos() can help aswell
        self.getFriendsTree().updateHoveredItemAt(mouseEvent.x(),mouseEvent.y())
        del(mouseEvent)

    def initIconTray(self,appController=None):
        if QSystemTrayIcon.isSystemTrayAvailable():
            trayController = TrayIconController.getInstance()
            trayController.getView().initContextMenu()
            trayController.getView().show()
            
            if appController is not None:
                trayController.setAppController(appController)
                trayController.getView().showMessage("Blooploader Notice","A MyBloop.com session has been initiated for " + appController.getRemoteSession().getUsername())
                
            return trayController
        return None