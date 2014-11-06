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

module controller.MainViewController
'''
from PyQt4.QtCore import SIGNAL,QObject,QVariant,QSize,QPoint
import utils
from __init__ import Controller

class MainViewController(Controller):
    _userProfile = None
    _remoteSession = None

    #The Tree's Views
    _bloopTree = None
    _friendsTree = None
    _groupsTree = None

    _uploadManagerView = None

    #The Tree's Controllers
    _appController = None
    _bloopTreeController = None
    _friendsTreeController = None
    _groupsTreeController = None

    _uploadManagerViewController = None

    _currentTree = None
    _currentItem = None
    _previousItem = None
    
    def __init__(self, view):
        Controller.__init__(self, view)

    SIGNAL_ITEM_CHANGED = SIGNAL('currentItemChanged (QTreeWidgetItem *,QTreeWidgetItem *)')
    SIGNAL_DOUBLE_CLICKED = SIGNAL('itemDoubleClicked(QTreeWidgetItem *,int)')
    SIGNAL_ITEM_CLICKED = SIGNAL('itemClicked (QTreeWidgetItem *,int)')
    SIGNAL_ITEM_ENTERED = SIGNAL('itemEntered (QTreeWidgetItem *,int)')

    def getBloopTree(self):
        #Get a reference to the user's Bloop Tree, all of his files
        if self._bloopTree == None and self.getView() is not None:
            self._bloopTree = self.getView().getBloopTree()
        return self._bloopTree

    def getUploadManagerView(self):
        if self._uploadManagerView == None and self.getView() is not None:
            self._uploadManagerView = self.getView().getUploadManagerView()
        return self._uploadManagerView

    def getFriendsTree(self):
        #Get a reference to the user's Friend's Tree
        if self._friendsTree == None and self.getView() is not None:
            self._friendsTree = self.getView().getFriendsTree()
        return self._friendsTree

    def getGroupsTree(self):
        #Get a reference to the user's Group's Tree
        if self._groupsTree == None and self.getView() is not None:
            self._groupsTree = self.getView().getGroupsTree()
        return self._groupsTree

    def getBloopTreeRoot(self):
        #Gets a reference to the Bloop Tree's root element
        if self.getBloopTree() is not None:
            return self.getBloopTree().topLevelItem(0)
        return None

    def getFriendsTreeRoot(self):
        #Gets a reference to the Friend's Tree's root element
        if self.getFriendsTree() is not None:
            return self.getFriendsTree().topLevelItem(0)
        return None

    def getGroupsTreeRoot(self):
        #Gets a reference to the Group's Tree's root element
        if self.getGroupsTree() is not None:
            return self.getGroupsTree().topLevelItem(0)
        return None

    def getAppController(self):
        if self._appController is not None:
            return self._appController
        
        if not 'AppController' in dir():
            from controllers.AppController import AppController
            
        self._appController = AppController.getInstance()        
        return self._appController

    def getBloopTreeController(self):
        return self._bloopTreeController

    def getFriendsTreeController(self):
        return self._friendsTreeController

    def getGroupsTreeController(self):
        return self._groupsTreeController

    def getUploadManagerViewController(self):
        return self._uploadManagerViewController

    def initializeTreeControllers(self):
        '''
        The Trees for Bloop, Friends and Groups will be controlled
        by TreeController classes.
        
        Here's where we bind the Tree view objects to its controllers.
        '''
        if self.getBloopTree() is not None:
            from TreeControllers import BloopTreeController
            self._bloopTreeController = BloopTreeController(self.getBloopTree(),self)
            
            #Catch when they move the mouse over the items inside the bloop tree, so we know who's currently
            #being pointed by the mouse, useful when drop happens
            bloopTree = self.getBloopTree()
            itemEnteredSlot = bloopTree.setCurrentHoveredItem
            bloopTree.connect(bloopTree,MainViewController.SIGNAL_ITEM_ENTERED,itemEnteredSlot)

        if self.getFriendsTree() is not None:
            from TreeControllers import FriendsTreeController
            self._friendsTreeController = FriendsTreeController(self.getFriendsTree(), self)
            utils.trace('MainViewController','initializeTreeControllers',self._friendsTreeController)

    
 
    def initializeUploadManagerViewController(self):
        '''
        The Upload Manager View will be controlled by a
        UploadManagerViewController object
        '''
        from UploadManagerViewController import UploadManagerViewController
        self._uploadManagerView = self.getView().getUploadManagerView()
        print "MainViewController._uploadManagerView @ ",hex(id(self._uploadManagerView))
        self._uploadManagerViewController = UploadManagerViewController(self._uploadManagerView, self)
    
    def bootstrapComponents(self):
        '''
        Sets the references to the trees, wipes them out, and fills them up
        with its first level elements.
        
        Makes the trees have controllers
        
        Makes the upload manager view have controllers

        It will make a call to initializeTreeControllers()
        '''
        #Makes the 3 Trees have controller objects attached to them
        #They will be responsible for everything that happens to those trees
        self.initializeUploadManagerViewController()
        self.initializeTreeControllers()
                
        #disconnect any signals connected in the past
        #self.disconnectTreeEvents()
        
        # Clear all the trees initially
        if self.getBloopTree() is not None:
            self.getBloopTree().clear()
        
        if self.getFriendsTree() is not None:
            self.getFriendsTree().clear()
        
        #we ask the remote session for the root element.
        if self.getRemoteSession() is None:
            #the session died
            self.getAppController().showLogin()
            return
        
        #add first level elements, the root elements of each tree (3 trees)
        self.addFirstLevelItems()
        
        #connect tree events
        if self.getBloopTree() is not None:
            self.connectTreeEvents(self.getBloopTree())
        
        if self.getFriendsTree() is not None:
            self.connectTreeEvents(self.getFriendsTree())

        
    def connectTreeEvents(self,tree):
        from views.BloopTreeView import BloopTree
        QObject.connect(tree,MainViewController.SIGNAL_ITEM_CHANGED,self.onItemChanged)
        QObject.connect(tree,MainViewController.SIGNAL_ITEM_CLICKED,self.onItemClicked)
        QObject.connect(tree,MainViewController.SIGNAL_DOUBLE_CLICKED,self.onItemDoubleClicked)
        QObject.connect(tree,BloopTree.SIGNAL_RIGHT_CLICK, self.onTreeRightClick)
        QObject.connect(tree,BloopTree.SIGNAL_LEFT_CLICK, self.onTreeLeftClick)
        QObject.connect(tree,BloopTree.SIGNAL_KEY_PRESS, self.onTreeKeyPress)
        
    def getUserProfile(self):
        from AppController import AppController
        if self._userProfile is None:
            self._userProfile = AppController.getInstance().getUserProfile()            
        return self._userProfile
    
    def getRemoteSession(self):
        from AppController import AppController        
        if self._remoteSession is None:
            self._remoteSession = AppController.getInstance().getRemoteSession()
        return self._remoteSession
    
    def onTreeRightClick(self,tree):
        '''
        This comes from a custom event sent by the tree.

        Since a tree is supposed to have a controller to handle
        its events, we invoke the controller's abstract method
        onRightClick. Same goes for onTreeLeftClick
        '''
        self.setCurrentTree(tree)
        tree.getController().onRightClick()
        
    def onTreeLeftClick(self,tree):
        '''This comes from a custom event sent by the tree'''
        self.setCurrentTree(tree)
        self.getCurrentTree().getController().onLeftClick()
        print "MainViewController, treeLeftC"
    
    def onTreeKeyPress(self,tree,keyEvent):
        tree.getController().onKeyPress(keyEvent)
    
    def addFirstLevelItems(self):
        #Loads the first level elements on the tree
        from views.BloopTreeView import BloopItem
        
        if self.getBloopTree() is not None:
            self.getBloopTree().insertTopLevelItem(0,BloopItem(['My Bloop'],'bloop'))
        
        if self.getFriendsTree() is not None:
            self.getFriendsTree().insertTopLevelItem(0,BloopItem(['My Friends'],'friends'))
        
        #Add Elements on the Root.
        self.getBloopTreeController().addItems(self.getBloopTree().topLevelItem(0))
        self.getBloopTree().topLevelItem(0).setExpanded(True)
        

    def setCurrentTree(self,tree):
        self._currentTree = tree

    def getCurrentTree(self):
        return self._currentTree
    
    def setCurrentItem(self,current):
        self._currentItem = current
        
    def getCurrentItem(self):
        return self._currentItem

    def setPreviousItem(self,previous):
        self._previousItem = previous
        
    def getPreviousItem(self):
        return self._previousItem
    
    def onItemChanged(self,current,previous):
        self.setCurrentItem(current)
        self.setPreviousItem(previous)
    
    def onItemClicked(self,item,column):
        self.setCurrentTree(item.treeWidget())

    def onItemDoubleClicked(self,item,column):
        '''Whatever happens when you double click on an item,
        gets forwarded to that item's Tree Controller onDoubleClick method'''
        self.setCurrentTree(item.treeWidget())
        if item.treeWidget().getController() is not None:
            item.treeWidget().getController().onDoubleClick()
            
    def saveSizes(self):
        '''Invoke this method if you need to save the sizes of:
        -> MainView
        -> Sizes of the splitters
        -> Position of the window
        '''
        #save splitter sizes
        from AppController import AppController
        sizes = self.getView().getSplitterWidget().sizes()
        settings = AppController.getInstance().getSettings()
        sizes_str = str(sizes).replace('[','').replace(']','')
        settings.setValue('splitter_sizes',QVariant(sizes_str))

        #save window size
        window_size = self.getView().size() #returns a QSize
        window_size_str = str(window_size.width()) + ',' + str(window_size.height())
        settings.setValue('window_size',QVariant(window_size_str))
        
        #save the position of the window
        window_pos = self.getView().pos()
        window_pos_str = str(window_pos.x())+','+str(window_pos.y())
        settings.setValue('window_position',QVariant(window_pos_str))
        #utils.trace('MainViewController','saveSizes','Sizes Saved.\n\tWindow Pos (' + window_pos_str + ')\n\tWindow Size (' + window_size_str + ')\n\tSplitters ('+sizes_str+')\n\n')
        
    def restoreSizes(self):
        '''
        Recovers and applies the size of the Blooploader window (not the login)
        , the sizes of the components, and the windows position.
        
        '''
        from AppController import AppController
        settings = AppController.getInstance().getSettings()
        
        #Fetch the settings on their string from
        #PyQt4 Developer Note:
        #  QSettings.value() returns a QVariant, I must convert to QString to do str(QString)
        sizes_str = str(settings.value('splitter_sizes',QVariant('480,80,80')).toString())
        window_size_str = str(settings.value('window_size',QVariant('300,500')).toString())
        window_pos_str = str(settings.value('window_position',QVariant('250,250')).toString())

        #Split the strings, and make each element an int through list comprehension
        sizes = [int(x) for x in sizes_str.split(',')]
        window_size = [int(x) for x in window_size_str.split(',')]
        window_pos = [int(x) for x in window_pos_str.split(',')]

        #Apply Settings
        self.getView().getSplitterWidget().setSizes(sizes) #Splitter Size
        self.getView().resize(QSize(window_size[0],window_size[1])) #Window Size
        self.getView().move(QPoint(window_pos[0],window_pos[1])) #Window Position

        #utils.trace('MainViewController','restoreSizes','Sizes Saved.\n\tWindow Pos (' + window_pos_str + ')\n\tWindow Size (' + window_size_str + ')\n\tSplitters ('+sizes_str+')\n\n')

        
    def onSplitterMoved(self, index, pos):
        self.saveSizes()