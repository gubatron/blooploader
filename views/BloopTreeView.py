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

module views.BloopTrees

In this module we'll have the classes that describe the visual behaviour
of the different Tree's in the blooploader main interface.

The BloopTree is a somewhat generic QTreeWidget tailored to the purposes
of the Blooploader. It talks to a generic TreeController.

The difference between the trees are the nature of its Items.

Therefor we'll have BloopItems, FriendItems and so on.

BloopItems represent usually files and folders on a bloop account.

Frienditems represent friends/family of a bloop user.
'''
from PyQt4.QtGui import QTreeWidget,QTreeWidgetItem,QTreeView,QIcon,QColor,QItemSelectionModel
from PyQt4.QtGui import QDrag
from PyQt4.QtCore import QObject, QRect, QMimeData, QByteArray, SIGNAL
from PyQt4.QtCore import Qt
import utils
import os
from MainView import MainView
from __init__ import View

class BloopTree(QTreeWidget, View):
    SIGNAL_RIGHT_CLICK = SIGNAL('rightClick(PyQt_PyObject)') 
    SIGNAL_LEFT_CLICK = SIGNAL('leftClick(PyQt_PyObject)')
    SIGNAL_KEY_PRESS = SIGNAL('keyPress(PyQt_PyObject,PyQt_PyObject)') #forwards (self,QKeyEvent) object

    _currentHoveredItem_ = None #Item on the tree which has the mouse on top
    
    _currentDrag_ = None
    _currentDrop_ = None
    _currentMimeData_ = None

    def __init__(self, parentWidget):
        QObject.__init__(self)
        QTreeWidget.__init__(self,parentWidget)
        View.__init__(self)
        self.setAcceptDrops(True)
        self.setMinimumWidth(300)
        self.setMouseTracking(True) #mouse doesn't have to be pressed to detect mouseMoves, or itemEntered
        #self.adjustSize()        

    def mimeData(self, items):
        self._currentMimeData_ = QMimeData()
        
        selectedData = []
        
        for item in items:
            data = item.getItemData() #python dict
            selectedData.append(data)
            
        self._currentMimeData_.setData("mybloop/files",
                     QByteArray.fromRawData(str(selectedData)))
        
        return self._currentMimeData_

    def updateHoveredItemAt(self,x,y):
        '''
        Given a pair of x,y coordinates, it updates the currentHoveredItem
        property. :)
        '''
        item = self.itemAt(x,y)
        if item is not None:
            self.setCurrentHoveredItem(item)
            #if item.getItemData() is not None:
            #    if item.getItemData().has_key('fileName'):
            #        utils.trace('BloopTree','mouseMoveEvent',item.getItemData()['fileName'])

    def mouseMoveEvent(self, mouseEvent):
        if mouseEvent:
            self.updateHoveredItemAt(mouseEvent.x(),mouseEvent.y())
            mouseEvent = None
            
            if self._currentDrag_ is not None and self._currentDrag_.source() != self._currentDrag_.target():
                self._currentDrop_ = self._currentDrag_.start(Qt.MoveAction)

        
    def mousePressEvent(self, mouseEvent):
        self.updateHoveredItemAt(mouseEvent.x(),mouseEvent.y())
        if mouseEvent.button() == Qt.LeftButton:
            self.emit(BloopTree.SIGNAL_LEFT_CLICK,self)
            
            #Possibly create a Drag event
            self._currentDrag_ = QDrag(self)
            self._currentDrag_.setMimeData(self.mimeData(self.selectedItems()))
            
            
        elif mouseEvent.button() == Qt.RightButton:
            self.emit(BloopTree.SIGNAL_RIGHT_CLICK,self)

        QTreeView.mousePressEvent(self,mouseEvent)
        mouseEvent = None

    def dragEnterEvent(self, dragEnterEvent):
        #utils.trace('BloopTree','dragEnterEvent',dragEnterEvent)
        #utils.trace('BloopTree','dragEnterEvent',self.getController())
        self.getController().onDragEnter(dragEnterEvent)

    def dragLeaveEvent(self, dragLeaveEvent):
        #utils.trace('BloopTree','dragLeaveEvent',dragLeaveEvent)
        self.getController().onDragLeave(dragLeaveEvent)

    def dragMoveEvent(self, dragMoveEvent):
        '''
        When objects are about to be dropped, and the user is
        hovering over tree elements, this method will update
        the _currentHoveredItem_ of this tree.
        
        It will invoke its controller method, onDragMove()
        so that it will know what to do.
        
        We expect that onDragMove, might make use of getCurrentHoveredItem()
        in case it needs it right before they drop the files
        '''
        #utils.trace('BloopTree','dragMoveEvent',dragMoveEvent)
        self.updateHoveredItemAt(dragMoveEvent.pos().x(),dragMoveEvent.pos().y())
        self.setSelection(QRect(dragMoveEvent.pos().x(),dragMoveEvent.pos().y(),1,1),QItemSelectionModel.SelectCurrent | QItemSelectionModel.Rows)
        self.getController().onDragMove(dragMoveEvent)
        
    def dropEvent(self, dropEvent):
        utils.trace('BloopTree','dropEvent', dropEvent)
        self.getController().onDrop(dropEvent)
        
    def setCurrentHoveredItem(self, item):
        self._currentHoveredItem_ = item
        
    def getCurrentHoveredItem(self):
        return self._currentHoveredItem_
    
    def keyPressEvent(self,keyEvent):
        self.emit(BloopTree.SIGNAL_KEY_PRESS,self,keyEvent)
        #it's up to the connected object to handle this.
        #in our case, See MainViewController.connectTreeEvents()
        #it will basically will invoke this tree's controller's
        #onKeyPress() to handle the pressed key.
    
class TreeItem(QTreeWidgetItem):
    '''
    Standard wrapper for any item to be displayed inside a tree
    You can always get a reference to the tree by invoking treeWidget()
    '''
    ICONS = None #Reference to the MainView ICONS
    _iconTypeString_ = None
    _itemData_ = None
    _treeController_ = None #A reference to the Containing Tree Controller
                            #which can also be used to get a hold of the tree
    
    def __init__(self, stringList):
        '''        
        stringList - Accepts a name (string) of the friend        
        '''
        QTreeWidgetItem.__init__(self, stringList)
    
    def setItemData(self, data):
        self._itemData_ = data
        
    def getItemData(self):
        return self._itemData_
    
    def setTreeController(self, treeController):
        self._treeController_ = treeController
        
    def getTreeController(self):
        return self._treeController_
    
    
class BloopItem(TreeItem):

    def __init__(self,stringList,iconTypeString=None):
        '''
        stringList - List of Strings for the columns on the tree. For now pass [name]
        iconTypeString - The type of icon to use, this will be used on the ICONS dir as a key, to grab a pixmap
        '''
        QTreeWidgetItem.__init__(self,stringList)
        self.ICONS = MainView.getInstance().getIcons()
        
        # We'll need to know what icon they're using for later
        # when we render the icon for items marked 'Private'
        self._iconTypeString_ = iconTypeString

        # Set the icon of this BloopItem
        if self.ICONS.has_key(iconTypeString):
            qIcon = QIcon(self.ICONS[iconTypeString])
        else:        
            qIcon = QIcon(self.ICONS['nfo'])
            
        self.setIcon(0,qIcon)
        
        
    def renderIcon(self):
        '''
        We render the icon in this function and not the constructor
        because the constructor doesn't know about the data in the item
        until we call setItemData()
        '''
        
        # Generate the main icon first
        self.ICONS = MainView.getInstance().getIcons()
        if self.ICONS.has_key(self._iconTypeString_):
            qIcon = QIcon(self.ICONS[self._iconTypeString_])
        else:
            qIcon = QIcon(self.ICONS['nfo'])
            
        # Fetch data on this item
        itemData = self.getItemData()
        if itemData is None:
            return

        from PyQt4.Qt import QPainter,QRect,QColor
        # This method might be called if a user sets a file as public/private
        # and we'll need to redraw the icon in those cases.
        if self.isDirectory():
            if itemData.has_key('directoryPrivate') and itemData['directoryPrivate'] == "0":
                self.setIcon(0,QIcon(qIcon))
                self.setToolTip(0, "") #Reset the Tooltip that said the dir was private
                self.setTextColor(0, QColor(0, 0, 0)) #Set the text color back to black
                return
        
        if self.isFile():
            if itemData.has_key('filePrivate') and itemData['filePrivate'] == "0":
                self.setIcon(0,QIcon(qIcon))
                self.setToolTip(0, "") #Reset the Tooltip that said the file was private
                self.setTextColor(0, QColor(0, 0, 0)) #Set the text color back to black
                return
        
        # This item is private, let's setup the small lock

        # Set the text of the item to grey
        self.setTextColor(0, QColor(25, 25, 25, 127))
        if self.isDirectory():
            self.setToolTip(0, "This directory is marked as private.")
        if self.isFile():
            self.setToolTip(0, "This file is marked as private.")
            

        Pixmap = qIcon.pixmap(20,20)
        
        if Pixmap is None:
            return
        
        #Create a painter to manipulate the pixmap 
        assert(Pixmap is not None)
        painter = QPainter(Pixmap)
        
        #Get the corresponding decorator icon from the icon manager
        imagePath = os.path.join("i18n","images","us_en")
        decoratorIcon= QIcon(os.path.join(imagePath,"sm_lock.png"))
        decoratorPixmap = decoratorIcon.pixmap(20,20)
                    
        if decoratorPixmap is None:
            print "Could not get the decorator pixmap"
            return
        
        #The decorator should be a pixmap with transparent background
        #since we'll put it on top the existing icon
        painter.setBackgroundMode(Qt.TransparentMode)
        painter.drawPixmap(QRect(6,6,10,10),decoratorPixmap,QRect(0,0,10,10))
        
        if painter.isActive():
            painter.end()
            
        #we close the painter and use the altered pixmap to create a new QIcon
        #for the qtreewidgetitem.
        self.setIcon(0,QIcon(Pixmap))
        
    def isRoot(self):
        print "TreeItem.isRoot?"
        assert(self.getTreeController() is not None)
        return self.getTreeController().getRootItem() == self

    def isDirectory(self):
        '''Checks the internal data of this BloopItem and tells us if its a directory'''
        if self.getItemData() is None:
            return False
        
        return self.getItemData().has_key('directoryID')
    
    def getDirectoryURL(self):
        '''Returns the URL of the directory.
        Will do so without connecting to the server, by traversing.
        If this is a file, it will return the directory of its parent.
        '''
        userProfile = self.getTreeController().getMainWindowController().getUserProfile()
        userName = userProfile.getUsername()
        rootUrl = "http://www.mybloop.com/%s" % (userName)
        
        if self.isRoot():
            return rootUrl
                
        itemData = self.getItemData()
        if itemData is None:
            return
        
        if not self.isDirectory():
            return self.parent.getDirectoryURL()

        #iterate.
        rootItem = self.getTreeController().getRootItem()
        parentDirectory = self.parent()
        
        dirNames = []
        #add myself first
        itemData = self.getItemData()
        dirNames.append(itemData['directoryName'])
        
        #do it for my ancestors as long as my parent isn't the root
        while parentDirectory is not rootItem:
            dirName = parentDirectory.getItemData()['directoryName']
            
            dirNames.append(dirName)
            parentDirectory = parentDirectory.parent()
        
        dirNames.reverse()
        path = '/'.join(dirNames)
        path = path.replace(" ","_")
        path = path.replace("'","")
        
        return "%s/%s#files" % (rootUrl,path)        
        

    def isFile(self):
        '''Checks the internal data of this BloopItem and tells us if its a file'''
        if self.getItemData() is None:
            return False
        
        return self.getItemData().has_key('fileID')
    
    def isPrivate(self):
        return (self.isDirectory() and self.getItemData()["directoryPrivate"]=="1") or\
               (self.isFile() and self.getItemData()["filePrivate"]=="1")
                   
    def setPrivate(self):
        itemData = self.getItemData()
        if self.isDirectory():
            itemData['directoryPrivate'] = "1"
            self.setItemData(itemData)
        elif self.isFile():
            itemData['filePrivate'] = "1"
            self.setItemData(itemData)
        
        # Redraw the icon
        self.renderIcon()
    
    def setPublic(self):
        itemData = self.getItemData()
        if self.isDirectory():
            itemData['directoryPrivate'] = "0"
            self.setItemData(itemData)
        elif self.isFile():
            itemData['filePrivate'] = "0"
            self.setItemData(itemData)
        
        # Redraw the icon
        self.renderIcon()
    
    
class BloopFriendItem(TreeItem):
    '''
    An item (friend/user) inside a FriendsTree
    '''
    ICONS = None    
    _itemData_ = None # Hold data about this friend
    
    def __init__(self, stringList):
        '''        
        stringList - Accepts a name (string) of the friend        
        '''
        QTreeWidgetItem.__init__(self, stringList)
        
        # Set this to the standard friend icon. 
        # Perhaps later on we can show Online / Offline indicators
        # or a Blooploader-enabled user indicator? :)
        imagePath = os.path.join("i18n","images","us_en")
        
        qIcon = QIcon(os.path.join(imagePath,"friend.png"))
        self.setIcon(0,qIcon)        
