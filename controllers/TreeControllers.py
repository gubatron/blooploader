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

module controller.TreeControllers

For now we'll just have a controller for the BloopTree cause that's all we need.
The idea (design-wise), is that each Tree has its own controller class, and they should
either implement a base TreeController interface or inherit from a TreeController class.

For now, we'll just have a concrete controller, which will be used for the Bloop tree,
the one that lets the user do all the stuff with his files.

This controller talks to main window controller.

It gets input from the BloopTree class, which is a dummy tree.

This BloopTreeController, gives life to that Tree.
'''
import utils
from views.BloopTreeView import BloopItem,BloopFriendItem
from AppController import AppController
from ActionManager import ActionManager
from __init__ import Controller
from utils.Employer import Employer #to be able to easily manage many GenericWorker threads
from PyQt4.QtGui import QDesktopServices,QMenu,QCursor
from PyQt4.QtCore import Qt, QUrl, SIGNAL
import i18n


class TreeController(Controller):
    """
    Abstract Class to define the basic behaviour of TreeControllers.
    
    All TreeController implementation classes must implement the
    abstract methods defined in this class.
    """
    _mainWindowController = None
    
    def __init__(self,view,mainWindowController):
        Controller.__init__(self,view)
        self.setMainWindowController(mainWindowController)

    def setMainWindowController(self, controller):
        self._mainWindowController = controller
        
    def getMainWindowController(self):
        return self._mainWindowController
    
    def getRootItem(self):
        return self.getView().topLevelItem(0)
        
    def getRemoteSession(self):
        return AppController.getInstance().getRemoteSession()
        
    #abstract
    def onItemEntered(self, item, column):
        raise Exception('onItemEntered not implemented')
    
    #abstract
    def onDoubleClick(self):
        raise Exception('onDoubleClick not implemented')
    
    #abstract
    def onLeftClick(self):
        raise Exception('onLeftClick not implemented')
    
    #abstract
    def onRightClick(self):
        raise Exception('onRightClick not implemented')
    
    #abstract
    def onDragEnter(self,dragEnterEvent):
        raise Exception('onDragEnter not implemented')
    
    #abstract
    def onDragLeave(self,dragLeaveEvent):
        raise Exception('onDragLeave not implemented')

    #abstract
    def onDragMove(self,dragMoveEvent):
        raise Exception('onDragMove not implemented')
    
    #abstract
    def onDrop(self,dropEvent):
        raise Exception('onDrop not implemented')
    
    def onKeyPress(self, keyEvent):
        raise Exception('onKeyPress not implemented')
    
    #abstract
    def addItems(self, treeItem):
        '''This method should add the child items of the treeItem given,
        if the given treeItem is a container.'''
        raise Exception('addItems not implemented')

class BloopTreeController(TreeController,Employer):
    '''
    Implementation of a Tree Controller.
    This Controller is in charge of handling all the events and logic
    of the Bloop Tree, the one that displays all of the users files in his Bloop.
    '''
    _droppedURIs_ = None #A list of File Paths
    
    _idsToItems_ = None #A Map of targetIds to TreeItem objects
                        #I don't think it will be worth it now make this
                        #map to complex in terms of adding/removing
                        #the references, even if an user drops a thousand objects
                        #they will be dropped on a few target folders
                        #It's probably very hard to find a case where an user will
                        #drop thousand of files on thousands of different folders
    
    _uploadManager = None #A reference to the upload manager
    
    _uploadManagerViewController_ = None
    
    _mainWindowController_ = None
    
    SIGNAL_FINISHED_FETCHING_FOLDER_CONTENTS = SIGNAL('finishedFetchingFolderContents(PyQt_PyObject,PyQt_PyObject)')

    def __init__(self,view,mainWindowController):
        TreeController.__init__(self,view,mainWindowController)
        Employer.__init__(self)
        
        # Set some labels to look better  
        view.setHeaderLabels([i18n.LABEL_WELCOME + ", " + str(AppController.getInstance().getRemoteSession().getUsername().capitalize()) + "!", i18n.LABEL_SIZE])        
        AppController.getInstance().getMainView().setWindowTitle(i18n.LABEL_BLOOPLOADER + " - " + AppController.getInstance().getRemoteSession().getUsername().capitalize())
        
        self._idsToItems_ = {}
        assert(mainWindowController is not None)
        self.setMainWindowController(mainWindowController)
        self.setUploadManagerViewController(mainWindowController.getUploadManagerViewController())
        
        self.connect(self,self.SIGNAL_FINISHED_FETCHING_FOLDER_CONTENTS,self.addDirectoriesAndFiles,Qt.QueuedConnection)

    def setUploadManagerViewController(self, uploadManagerViewController):
        self._uploadManagerViewController_ = uploadManagerViewController
 
    def getUploadManagerViewController(self):
        return self._uploadManagerViewController_
    
    def getMainWindowController(self):
        return self._mainWindowController_
    
    def setMainWindowController(self, mainWindowController):
        self._mainWindowController_ = mainWindowController
 
    def onDoubleClick(self):
        currentItem = self.getView().currentItem()

        if currentItem is None:
            return

        # We don't want to make an API request when we're
        # hiding a directory's contents
        if currentItem.isDirectory():
#            if currentItem.isExpanded():
#                #currentItem.setExpanded(False)
            mainView = AppController.getInstance().getMainView()
            mainView.statusBar().showMessage(i18n.LABEL_BLOOPTREE_STATUS_BAR_REQUESTING_FILES)

            #self.hireWorker(self.addItems,currentItem)
            self.addItems(currentItem)
            #mainView.showStatusBarDefaultText()            
            return
        
        if currentItem == self.getRootItem():
            from models.mbu_config import meta
            QDesktopServices.openUrl(QUrl("http://" + meta['SERVER'] + "/" + AppController.getInstance().getUserProfile().getUsername()))
            return
        
        data = currentItem.getItemData()

        # If it's the MyBloop root item, return none
        if data is None:
            return

        if data.has_key('fileURL') and data['fileURL'] is not None:
            QDesktopServices.openUrl(QUrl(data['fileURL']))

    def onLeftClick(self):
        print "CLICKED ON ", self.getView().currentItem()
        if self.getView().currentItem() is None:
            return
        
        if self.getView().currentItem().isFile():
            print "My Parent folder is", self.getView().currentItem().parent()

            if self.getView().currentItem().parent().getItemData() is not None:
                print self.getView().currentItem().parent().getItemData()['directoryID']

    def onRightClick(self):
        if self.getView() is None:
            #somebody is using this wrong let's skip
            raise Exception("TreeController.onRightClick() invoked and there's no view, wtf")
        
        currentItem = self.getView().getCurrentHoveredItem() #we'll considered the hovered item
        if currentItem is None:
            #utils.trace("BloopTreeController", "onRightClick:", "Clicked on no element, skipping right click menu")
            return

        #TODO: Depending on what we're right clicking on we enable or disable actions
        #at the Action Manager. For now, we'll just create a popup
        if currentItem is None or currentItem.isDirectory() or\
        currentItem == self.getRootItem():
            #utils.trace("BloopTreeController","onRightClick","Clicked on directory")
            if currentItem is None:
                #utils.trace("BloopTreeController","onRightClick","Clicked on nothing, consider the root actually")
                pass
        elif currentItem.isFile():
            #utils.trace("BloopTreeController","onRightClick","Clicked on file")
            pass
        self.showBloopItemActionsPopup()

    def showBloopItemActionsPopup(self):
        currentItem = self.getView().getCurrentHoveredItem() #we'll considered the hovered item

        mvc = AppController.getInstance().getMainViewController()

        parentView = mvc.getView() if currentItem is not None else self.getView()
        #utils.trace('BloopTreeController','showBloopItemActionsPopup()',currentItem)

        tempMenu = QMenu(parentView)
        bloopItemActions = ActionManager.getInstance().getBloopItemActions()
        actionsNotForRoot = [ActionManager.getInstance().getDeleteAction(),
                             ActionManager.getInstance().getSetPrivateAction(),
                             ActionManager.getInstance().getSetPublicAction(),
                             ActionManager.getInstance().getRenameItemAction(),
                             ActionManager.getInstance().getMoveAction(),
                             ActionManager.getInstance().getDownloadFileAction()]

        actionsNotForDir = [ActionManager.getInstance().getDownloadFileAction()]
        
        actionsNotForFiles = [ActionManager.getInstance().getNewFolderAction(),
                              ActionManager.getInstance().getRefreshFolderAction()]

        actionsNotForMultipleSelection = [ActionManager.getInstance().getRenameItemAction(),
                                          ActionManager.getInstance().getOpenLinkAction(), #debatable
                                          ActionManager.getInstance().getNewFolderAction(),
                                          ActionManager.getInstance().getRefreshFolderAction(),
                                          ActionManager.getInstance().getDownloadFileAction()]

        currentItems = mvc.getBloopTree().selectedItems()

        for action in bloopItemActions:
    
            #Skip delete action if we're right clicking on the root on the root
            if (currentItem == self.getRootItem() and action in actionsNotForRoot) or\
               (currentItem.isDirectory() and action in actionsNotForDir):
                continue

            # Actions not for files
            if (action in actionsNotForFiles and currentItem.isFile()):
                continue

            # If they select more than one item, show both the public and private options
            #Some actions are not meant to be shown when we have selected several elements
            if len(currentItems) > 1:
                print "Current Action:",action
                print "Actions not for multiple selection:",actionsNotForMultipleSelection
                print
                
            if len(currentItems) > 1 and action in actionsNotForMultipleSelection:
                continue
            
            # There's a bug with selectedItems() where it returns len(currentItems) = 0
            # the first time you right click an item in the tree. This <= 1 clause below fixes that.
            if len(currentItems) <= 1:
                itemData = currentItem.getItemData()
                if currentItem.isPrivate() and action == ActionManager.getInstance().getSetPrivateAction():
                    continue
                if not currentItem.isPrivate() and action == ActionManager.getInstance().getSetPublicAction():
                    continue

            #Change text to plural on the actions where it makes sense
            if len(currentItems) > 1 and \
               action == ActionManager.getInstance().getCopyLinkAction():
                action.setText(i18n.ACTION_BLOOPTREE_COPY_LINKS)
            elif action == ActionManager.getInstance().getCopyLinkAction():
                action.setText(i18n.ACTION_BLOOPTREE_COPY_LINK)   

            tempMenu.addAction(action)
            
        tempMenu.popup(QCursor.pos())

    
    def onDragEnter(self,dragEnterEvent):
        #utils.trace('BloopTreeController','onDragEnter',dragEnterEvent)
        dragEnterEvent.accept()
        mimeData = dragEnterEvent.mimeData().data('text/uri-list')
        self.setDroppedURIsFromMimeData(mimeData)
        
    def setDroppedURIsFromMimeData(self,mimeData):
        #utils.trace('BloopTreeController','onDragEnter',mimeData)
        import urllib
        
        self._droppedURIs_ = str(mimeData).strip()
        print "DROPPED URIS"
        print self._droppedURIs_
        self._droppedURIs_ = self._droppedURIs_.replace("\r",'').replace('file://','').split('\n')
        
        #Remove None Elements, and url decode the paths so that they can be found        
        self._droppedURIs_ = [ urllib.unquote(x) for x in filter(lambda(x): x is not None,self._droppedURIs_)]
    
    def getDroppedURIs(self):
        return self._droppedURIs_
        
    def onDragLeave(self, dragLeaveEvent):
        #utils.trace('BloopTreeController','onDragLeave',dragLeaveEvent)
        self._droppedURIs_ = None
        
    def onDragMove(self, dragMoveEvent):
        '''
        As we move our mouse over the tree, we gotta calculate what item
        will be the target for the drop.
        '''
        #utils.trace('BloopTreeController','onDragMove','-')
        if self.getView() is None:
            return
        
        #hoveredItem = self.getView().getCurrentHoveredItem()

        
    def onDrop(self, dropEvent):
        '''
        When a file is dropped, the tree controller will:
         - Determine if you're dropping on top of a file 
         - Determine if you're dropping on a folder 
         - If you're dropping on the root of the bloop
         - or if you're dropping on a file at the first level
         
         This controller has a map of remote folder Ids, to TreeItems that represent
         those folders. This map gets created as we drop.
         
         When a transaction finishes, she will say what containing dir needs to be
         upgraded.
         
         For the Root element we use 0 as a key, and the topLevelItem(0) of the tree as Item.

        The URIs will come as Mime Data and they should be set already onDragEnter for us.
        '''
        if self.getDroppedURIs() is not None:
            #Item where we dropped
            currentTarget = self.getView().getCurrentHoveredItem()
            
            #Root of the Tree (BloopItem), and RPC Proxy
            bloopRoot = self.getMainWindowController().getBloopTreeRoot()
            
            #Prepare the UploadManagerViewController to receive signals from the
            #UploadManager (Model Object), if it hasn't done so already
            #self.attemptConnectUploadManagerSignals(remoteSession)
            
            filePathList = self.getDroppedURIs()
            currentTargetDirectoryItem = None

            #Define which is the directory that will have to be refreshed when this transfers finish.
            if currentTarget is None:
                currentTargetDirectoryItem = bloopRoot
            elif currentTarget.isDirectory() or currentTarget == bloopRoot:
                currentTargetDirectoryItem = currentTarget
            else:
                currentTargetDirectoryItem = currentTarget.parent()

            targetItemID = 0
            if currentTargetDirectoryItem != bloopRoot:
                assert(currentTargetDirectoryItem.getItemData().has_key('directoryID'))
                targetItemID = int(currentTargetDirectoryItem.getItemData()['directoryID'])

            #Add all the files to the upload manager, but do it on a worker thread to not block the UI
            #self.hireWorker(self._addFilePathListToUploadManager,filePathList,targetItemID,currentTargetDirectoryItem)
            self._addFilePathListToUploadManager(filePathList,targetItemID,currentTargetDirectoryItem)

    def _addFilePathListToUploadManager(self,filePathList,targetItemID,currentTargetDirectoryItem):
        from os.path import isfile,isdir
        
        remoteSession = AppController.getInstance().getRemoteSession()
        
        if self._uploadManager is None:
            self._uploadManager = self.getUploadManagerViewController().getUploadManager()
        
        for fp in filePathList:
            #ignore invalid files
            if fp == "" or fp is None or len(fp) == 0 or fp == '\0':
                continue
    
            #fix filepaths for windows files, remove '/' from beginning
            if utils.isWindows() and fp.startswith('/'):
                fp = fp[1:]
    
            #more filepath fixing
            if fp.endswith('/') or fp.endswith("\\"):
                fp = fp[:-1]
    
            print "DROPPING","["+fp+"]","at",str(targetItemID)
    
            if isfile(fp):
                #Add the file and attempt to map the target directory id to its BloopItem object
                #MIGHT DO: Put this addFile on a thread for snappier UI response.
                self._uploadManager.addFile(fp,
                                            targetItemID,
                                            remoteSession.getUserFiles(targetItemID),
                                            persist=False)
                
                #self.hireWorker(self._uploadManager.addFile,
                #                fp,#filepath
                #                targetItemID,#remoteid 
                #                remoteSession.getUserFiles(targetItemID), #remoteFiles
                #                False) #persist=False
                self.mapDirIdToDirBloopItem(targetItemID,currentTargetDirectoryItem)
            elif isdir(fp):
                self._uploadManager.addFolder(fp, targetItemID)
            else:
                raise Exception("Something is wrong with this dropped file path " + str(fp))
        
        self._uploadManager.persistUploadTransactions()

        
    def __str__(self):
        return "BloopTreeController at " +  str(hex(id(self))) +  "My view is " + str(self.getView())
    
    def addItems(self, treeItem):
        '''
        Given a treeItem, if its a folder, it will fetch the contents on the server,
        empty the local elements (if it has something already) and it will add whatever
        it gets from the server.
        
        It will get only its child elements.
        '''
        remoteSession = self.getRemoteSession()
        
        theTree = self.getView()
        treeItem.setTreeController(self)

        rootElement = theTree.topLevelItem(0)
        
        if treeItem == rootElement or treeItem.isDirectory():
            treeItem.takeChildren() #Clear whatever was in there, we'll add again

        if treeItem == rootElement:
            self.hireWorker(self.fetchFolderContents,
                            rootElement,
                            0)
        elif treeItem.isDirectory():
            utils.printDict(treeItem.getItemData())
            self.hireWorker(self.fetchFolderContents,
                            treeItem,
                            treeItem.getItemData()['directoryID'])
            mainView = AppController.getInstance().getMainView()
            mainView.statusBar().showMessage(i18n.LABEL_ERROR_REFRESHING_FOLDER)
        
    def fetchFolderContents(self, treeItem, remoteFolderId):
        '''
        This function is meant to be called on a worker thread.
        When it ends, it should somehow send a signal and notify
        the GUI thread about the data it obtained and tell it
        on which item to put it.
        
        I'll try to do this by doing an emit. And the signal should be
        tied to the right method.
        '''
        remoteSession = self.getRemoteSession()
        results = remoteSession.getUserFiles(remoteFolderId)
        utils.trace("BloopTreeController","fetchFolderContents","The results are " + str(results))
        self.emit(self.SIGNAL_FINISHED_FETCHING_FOLDER_CONTENTS, treeItem, results)
        return results

    def refreshFolderByRemoteId(self, remoteFolderId):
        '''
        It will use the map of remoteFolderId -> TreeItems, 
        
        if the item is there it will invoke addItems(item)
        which will do the necessary rpc calls to refresh the contents of the tree.
        '''
        #assert(type(remoteFolderId)==int)
        assert(remoteFolderId is not None)
        assert(self._idsToItems_ is not None)
        #assert(self._idsToItems_.has_key(remoteFolderId))
        #utils.trace("BloopTreeController","refreshFolderByRemoteId","Folder ID - " + str(remoteFolderId))
        if self._idsToItems_.has_key(remoteFolderId):
            #utils.trace("BloopTreeController","refreshFolderByRemoteId",self._idsToItems_[remoteFolderId])
            pass
        
        #utils.trace("BloopTreeController", "refreshFolderByRemoteId","_idsToItems_:")
        #utils.printDict(self._idsToItems_)
        
        if remoteFolderId == 0:
            self.addItems(self.getView().topLevelItem(0)) #to the root
            self.getView().topLevelItem(0).setExpanded(True)
            return
        
        if self._idsToItems_ is not None and self._idsToItems_.has_key(remoteFolderId):
            self.addItems(self._idsToItems_[remoteFolderId])
            self._idsToItems_[remoteFolderId].setExpanded(True)
   
            
    def addDirectoriesAndFiles(self, bloopItem, folderContents):
        '''
        Given an Item, if it has any children it will clear them
        and it will add first the directories, then the files.
        
        bloopItem - The Parent BloopItem on the tree
        folderContents - A python dict that may have 'directories' and 'files'

        (slot for SIGNAL_FINISHED_FETCHING_FOLDER_CONTENTS
        Only meant to be executed on the GUI thread.)
        '''
        if folderContents is None:
            return
        
        if folderContents.has_key('directories') and \
           folderContents['directories'] is not None:
            for d in folderContents['directories']:
                #print "About to add directory data"
                #utils.printDict(d)
                dirItem = BloopItem([d['directoryName']],'folder')
                dirItem.setItemData(d)
                dirItem.renderIcon()
                dirItem.setTreeController(self)
                bloopItem.addChild(dirItem)
            
        if folderContents.has_key('files') and \
           folderContents['files'] is not None:
            for f in folderContents['files']:
                #print "About to add data to a file" 
                #utils.printDict(f)
                fileItem = BloopItem([f['fileName'],f['fileSize']],f['fileType'])
                fileItem.setItemData(f)
                fileItem.renderIcon()
                fileItem.setTreeController(self)
                bloopItem.addChild(fileItem)

        mainView = AppController.getInstance().getMainView()
        mainView.statusBar().showMessage(i18n.LABEL_DONE)
        bloopItem.setExpanded(True)

            
    def mapDirIdToDirBloopItem(self,targetId,targetDirTreeItem):
        '''
        When a Upload Transaction ends, we want to show this on the Tree.
        We don't want to do a tree lookup, since this could take a long time
        if the user has dropped a file on the Nth folder.
        
        Here's what we do... When an upload starts, we know the ID (BloopDB)
        of the target folder, and we also know what BloopTreeItem object
        represents this target ID on the UI.
        
        Whenever a file is dropped, or a folder is dropped, we'll make an entry
        on a private map of targetIds to TreeItem objects.
        
        The idea is this, when the UploadManager signals an Upload Finished,
        the UploadManagerViewController can tell the tree controller about the
        target ID of an upload that has finished... since this controller
        holds the relationship between that ID and a visual representation of the object
        the TreeController can get the reference of the TreeItem and invoke
        self.addItems(theTreeItemInQuestion), this method will wipe out the internal
        contents, and with an RPC call will get the new contents of the folder.
        
        Brilliantly simple
        '''
        if self._idsToItems_.has_key(targetId):
            print ("BloopTreeController","mapTargetIdToTreeItem", "Folder has already been mapped (" + str(targetId) + ")")
            return

        #If we get nothing as target ID, we make sure we associate this
        #to the root
        if targetDirTreeItem is None or targetId == 0:
            targetId = 0 #make sure it will be zero if no target dir was passws
            targetDirTreeItem = self.getMainWindowController().getBloopTreeRoot()
        
        assert(targetDirTreeItem is not None)
        targetId = int(targetId) #make sure the key is an integer
        #utils.trace("BloopTreeController","mapTargetIdToTreeIem mapping id= ",targetId)
        #utils.trace("BloopTreeController","mapTargetIdToTreeItem to item", targetDirTreeItem)
        
        assert(targetDirTreeItem.isDirectory() or targetDirTreeItem == self.getMainWindowController().getBloopTreeRoot())
        
        #Map it only if you haven't done sone already, the folder objects shouldn't change
        if not self._idsToItems_.has_key(targetId):
            self._idsToItems_[targetId] = targetDirTreeItem
            #utils.trace("BloopTreeController","mapTargetIdToTreeItem","now the map looks like this")
            #utils.printDict(self._idsToItems_)
            
    def onKeyPress(self, keyEvent):
        if not 'Qt' in dir():
            from PyQt4.QtCore import Qt

        if keyEvent.key() == Qt.Key_Delete or keyEvent.key() == Qt.Key_Backspace:
            ActionManager.getInstance().getDeleteAction().trigger()
        if keyEvent.key() == Qt.Key_F2:
            ActionManager.getInstance().getRenameItemAction().trigger()
    
class FriendsTreeController(TreeController):
    def __init__(self, view, mainViewController):
        TreeController.__init__(self,view, mainViewController)
        
    def onLeftClick(self):
        print "CLICKED ON ", self.getView().currentItem()
        
    def buildTree(self):
        theTree = self.getView()
        rootElement = theTree.topLevelItem(0)     
        self.addItems(rootElement)
        rootElement.setExpanded(True)

    def onDoubleClick(self):    
        # This are of the code is mainly to refresh your friends list. 
        # They will be able to double click the root folder to refresh.
        from utils import trace        

        theTree = self.getView()
        currentItem = theTree.currentItem()
        rootElement = theTree.topLevelItem(0)     

        if currentItem == rootElement:
            #trace('FriendsTreeController', '__init__', 'Got root element: ' + str(rootElement))
            #trace('FriendsTreeController', '__init__', 'Fetching friends list')
            #might do: put this on a worker thread
            self.addItems(currentItem)

    def addItems(self, currentItem):
        remoteSession = self.getRemoteSession()
        
        friendsList = remoteSession.getFriendsList()
                
        #for user in friendsList:
            #print "Username: " + user['username']
            
        self.addFriendsToTree(currentItem, friendsList)
        return


    def addFriendsToTree(self, currentElement, friendsList):
        '''
        Given an Item, if it has any children it will clear them
        and it will add first the directories, then the files.
        '''
        for user in friendsList:
            #print "About to add user data"
            #utils.printDict(user)
            friendItem = BloopFriendItem([user['username'],i18n.LABEL_OFFLINE])
            friendItem.setItemData(user)
            currentElement.addChild(friendItem)

        
class GroupsTreeController(TreeController):
    def __init__(self, view, mainViewController):
        TreeController.__init__(self,view, mainViewController)
        #view.setHeaderLabel("Drag and drop files to your friends!")        
