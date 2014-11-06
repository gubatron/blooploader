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

module controller.ActionManager
'''
from PyQt4.QtGui import QAction, QIcon
from PyQt4.QtCore import QObject, SIGNAL
import utils
from utils.Employer import Employer
import i18n
import os


SIGNAL_TRIGGERED = SIGNAL("triggered(bool)")

class ActionManager(Employer):
    """
    A singleton class to define all the actions/commands
    we'll use at:
     -> Menu bar
     -> Button Toolbar
     -> Right click menues
    """
    INSTANCE = None #The ActionManager, the one and only
    
    _uploadManager = None #Reference to the UploadManager singleton instance
    _uploadManagerLoaded = False
    
    _newFolderAction = None
    _refreshFolderAction = None
    _deleteAction = None
    _renameItemAction = None #Let's see if we can rename folders and files with a single action    
    _moveAction = None #Let's see if we can invoke all the move scenarios through a single action
    _setPrivateAction = None
    _setPublicAction = None
    _copyLinkAction = None
    _openLinkAction = None
    _renameAction = None
    
    _bloopItemActions = None #A list to group all the file related actions
    _bloopFriendActions = None #A list to group all the references to friendship related actions
    
    _bloopFileMenuActions = None #List of actions to be displayed on the application's file menu
    _bloopHelpMenuActions = None #List of actions to be displayed on the application's help menu
    
    _bloopUploadManagerActions = None #List of actions to be used on the Upload Manager
    
    # Actions for the File Menu
    _logoutAction = None
    _exitAction = None
    
    # Actions for the Help Menu
    _viewChangelogAction = None
    _sendFeedbackAction = None
    _aboutDialogAction = None
    
    _restoreUploadsAction = None
    _pauseUploadAction = None
    _pauseAllUploadsAction = None
    _resumeUploadAction = None
    _cancelUploadAction = None
    _cancelAllUploadsAction = None
    _clearUnactiveUploadsAction = None
    
    def __init__(self):
        Employer.__init__(self)
        self.__initBloopItemActions__()
        self.__initBloopFileMenuActions()
        self.__initBloopHelpMenuActions()
        self.__initBloopUploadManagerActions()
    
    @staticmethod
    def getInstance():
        if ActionManager.INSTANCE is None:
            ActionManager.INSTANCE = ActionManager()
        return ActionManager.INSTANCE
    
    def __loadUploadManager(self):
        if self._uploadManagerLoaded:
            return
        
        if self._uploadManager is None:
            from models.upload_manager import UploadManager
            self._uploadManager = UploadManager.getInstance()
            self._uploadManagerLoaded = True
    
    def getBloopItemActions(self):
        '''Returns a list with the references to all the BloopItem Actions.
        These are all the actions with manipulating files on the bloop.'''
        if self._bloopItemActions is None:
            self.__initBloopItemActions__()
        return self._bloopItemActions
    
    def __initBloopItemActions__(self):
        '''
        This method will initialize the actions,
        and the lists to group them.
        
        It's up to the listeners to define slots for these actions.
        I'm still onsure if the slot functions should be unique,
        so we don't have to mantain 2 different behaviours.
        Maybe the slots could be defined here, however, many of
        the slots would need to talk to the controllers to know
        about the current status of the application.
        
        Say... you want to create a new folder.
        This could be defined here, but this ActionManager
        would need to get a hold of the controller instances
        and ask what are the current selected items, and also
        go deeper to the model classes.
        '''
        self._bloopItemActions = []

        # We'll need to find  the location of our images
        imagePath = os.path.join("i18n","images","us_en") 
        
        #Define our actions here
        
        #NOTE: It's good that we build the actions on the fly because 
        # depending on what they select, we should show different things.
        # e.g. Selecting dir + file should not show New Directory or Rename, just Delete
        self._newFolderAction = QAction(QIcon(os.path.join(imagePath,"folder_new.png")), i18n.ACTION_BLOOPTREE_NEW_FOLDER, None)
        self._copyLinkAction = QAction(QIcon(os.path.join(imagePath,"copy_link.png")), i18n.ACTION_BLOOPTREE_COPY_LINK, None)
        self._openLinkAction = QAction(QIcon(os.path.join(imagePath,"open_link.png")), i18n.ACTION_BLOOPTREE_OPEN_LINK, None)
        self._downloadFileAction = QAction(QIcon(os.path.join(imagePath,"download.png")), i18n.ACTION_BLOOPTREE_DOWNLOAD_FILE, None)
        self._renameAction = QAction(QIcon(os.path.join(imagePath,"rename.png")), i18n.ACTION_BLOOPTREE_RENAME, None)
        self._deleteAction = QAction(QIcon(os.path.join(imagePath,"delete.png")), i18n.ACTION_BLOOPTREE_DELETE, None)
        self._setPrivateAction = QAction(QIcon(os.path.join(imagePath,"set_private.png")), i18n.ACTION_BLOOPTREE_SET_PRIVATE, None)
        self._setPublicAction = QAction(QIcon(os.path.join(imagePath,"set_public.png")), i18n.ACTION_BLOOPTREE_SET_PUBLIC, None)
        self._refreshFolderAction = QAction(QIcon(os.path.join(imagePath,"refresh.png")), i18n.ACTION_BLOOPTREE_REFRESH, None)

        # This is the order of the appears on the list (there are exlusions depending
        # on the item that is right-clicked).
        self._bloopItemActions.append(self._newFolderAction)
        self._bloopItemActions.append(self._openLinkAction)
        self._bloopItemActions.append(self._copyLinkAction)
        self._bloopItemActions.append(self._downloadFileAction)
        self._bloopItemActions.append(self._renameAction)
        self._bloopItemActions.append(self._deleteAction)
        self._bloopItemActions.append(self._setPrivateAction)
        self._bloopItemActions.append(self._setPublicAction)
        self._bloopItemActions.append(self._refreshFolderAction)

        self.connect(self._newFolderAction, SIGNAL_TRIGGERED, self.onNewFolderAction)
        self.connect(self._openLinkAction, SIGNAL_TRIGGERED, self.onOpenLinkAction)
        self.connect(self._copyLinkAction, SIGNAL_TRIGGERED, self.onCopyLinkAction)
        self.connect(self._downloadFileAction, SIGNAL_TRIGGERED, self.onDownloadFileAction)
        self.connect(self._renameAction, SIGNAL_TRIGGERED, self.onRenameAction)
        self.connect(self._deleteAction, SIGNAL_TRIGGERED, self.onDeleteAction)
        self.connect(self._setPrivateAction, SIGNAL_TRIGGERED, self.onSetPrivateAction)
        self.connect(self._setPublicAction, SIGNAL_TRIGGERED, self.onSetPublicAction)
        self.connect(self._refreshFolderAction, SIGNAL_TRIGGERED, self.onRefreshFolderAction)
        
    def getBloopFileMenuActions(self):
        if self._bloopFileMenuActions is None:
            self.__initBloopFileMenuActions()
        return self._bloopFileMenuActions
    
    def getBloopHelpMenuActions(self):
        if self._bloopHelpMenuActions is None:
            self.__initBloopHelpMenuActions()
        return self._bloopHelpMenuActions
    
    def getBloopUploadManagerActions(self):
        if self._bloopUploadManagerActions is None:
            self.__initBloopUploadManagerActions()
        return self._bloopUploadManagerActions
    
    def __initBloopFileMenuActions(self):
        self._bloopFileMenuActions = []
        
        # We'll need to find  the location of our images for icons in the menu
        imagePath = os.path.join("i18n","images","us_en") 
        
        self._exitAction = QAction(QIcon(os.path.join(imagePath,"exit.png")), i18n.ACTION_EXIT,None)
        self._logoutAction = QAction(QIcon(os.path.join(imagePath,"logout.png")), i18n.ACTION_LOGOUT,None)
        
        self._bloopFileMenuActions.append(self._logoutAction)
        self._bloopFileMenuActions.append(self._exitAction)
        
        self.connect(self._exitAction, SIGNAL_TRIGGERED, self.onExitAction)
        self.connect(self._logoutAction, SIGNAL_TRIGGERED, self.onLogoutAction)        
        
    def __initBloopHelpMenuActions(self):
        self._bloopHelpMenuActions = []
        
        # We'll need to find  the location of our images for icons in the menu
        imagePath = os.path.join("i18n","images","us_en") 
        
        self._sendFeedbackAction = QAction(QIcon(os.path.join(imagePath,"send_feedback.png")), i18n.ACTION_SEND_FEEDBACK,None)
        self._viewChangelogAction = QAction(QIcon(os.path.join(imagePath,"changelog.png")), i18n.ACTION_VIEW_CHANGELOG,None)
        self._aboutDialogAction = QAction(QIcon(os.path.join(imagePath,"about.png")), i18n.ACTION_ABOUT_DIALOG,None)        

        self._bloopHelpMenuActions.append(self._sendFeedbackAction)
        self._bloopHelpMenuActions.append(self._viewChangelogAction)
        self._bloopHelpMenuActions.append(self._aboutDialogAction)
        
        self.connect(self._sendFeedbackAction, SIGNAL_TRIGGERED, self.onSendFeedbackAction)
        self.connect(self._viewChangelogAction, SIGNAL_TRIGGERED, self.onViewChangelogAction)
        self.connect(self._aboutDialogAction, SIGNAL_TRIGGERED, self.onAboutDialogAction)
        
    def __initBloopUploadManagerActions(self):
        '''
        Init all actions related to the Upload Manager.
        Pausing, Resuming, Cancelling, Clearing, Restoring previous uploads
        '''
        #TODO: Have icons for these actions
        self._bloopUploadManagerActions = []

        #instanciate
        self._pauseUploadAction = QAction("Pause Upload",None)
        self._pauseAllUploadsAction = QAction("Pause All",None)
        self._resumeUploadAction = QAction("Resume Upload",None)
        self._cancelUploadAction = QAction("Cancel Upload",None)
        self._cancelAllUploadsAction = QAction("Cancel All",None)
        self._clearUnactiveUploadsAction = QAction("Clear Inactive",None)
        
        #group
        self._bloopUploadManagerActions.append(self._pauseUploadAction)
        self._bloopUploadManagerActions.append(self._pauseAllUploadsAction)
        self._bloopUploadManagerActions.append(self._resumeUploadAction)
        self._bloopUploadManagerActions.append(self._cancelUploadAction)
        self._bloopUploadManagerActions.append(self._cancelAllUploadsAction)
        self._bloopUploadManagerActions.append(self._clearUnactiveUploadsAction)
        
        #connect
        self.connect(self._pauseUploadAction, SIGNAL_TRIGGERED, self.onPauseUploadAction)
        self.connect(self._pauseAllUploadsAction, SIGNAL_TRIGGERED, self.onPauseAllUploadsAction)
        self.connect(self._resumeUploadAction, SIGNAL_TRIGGERED, self.onResumeUploadAction)
        self.connect(self._cancelUploadAction, SIGNAL_TRIGGERED, self.onCancelUploadAction)
        self.connect(self._cancelAllUploadsAction, SIGNAL_TRIGGERED, self.onCancelAllUploadsAction)
        self.connect(self._clearUnactiveUploadsAction, SIGNAL_TRIGGERED, self.onClearUnactiveUploadsAction)
        
    def onSetPublicAction(self):
        utils.trace("ActionManager","onSetPublicAction","")
        
        from AppController import AppController
        bloopTree = AppController.getInstance().getMainViewController().getBloopTree()

        # Grab the currently selected items (could be multiple selections)
        currentItems = bloopTree.selectedItems() 

        if currentItems is None:
            return
        
        # We're going to store our list of files and directories here
        fileList = []
        dirList = []
        
        for item in currentItems:
            itemData = item.getItemData()
            if item.isFile():
                fileList.append(itemData['fileID'])
            elif item.isDirectory():
                dirList.append(itemData['directoryID'])
        
        items = {}
        items['fileList'] = fileList
        items['dirList'] = dirList
        utils.trace("ActionManager","onSetPublicAction",items)
        
        # Grab the remote instance and prepare to make the call
        remoteSession = AppController.getInstance().getRemoteSession()
        remoteSession.setItemVisibility(items, 'public')
        
        # Loop through the items and set their 'filePrivate' fields to 0
        for item in currentItems:
            item.setPublic()
    
    def onSetPrivateAction(self):
        utils.trace("ActionManager","onSetPublicAction","")
        
        from AppController import AppController
        bloopTree = AppController.getInstance().getMainViewController().getBloopTree()

        # Grab the currently selected items (could be multiple selections)
        currentItems = bloopTree.selectedItems() 

        if currentItems is None:
            return
        
        # We're going to store our list of files and directories here
        fileList = []
        dirList = []
        
        for item in currentItems:
            itemData = item.getItemData()
            if item.isFile():
                fileList.append(itemData['fileID'])
            elif item.isDirectory():
                dirList.append(itemData['directoryID'])
        
        items = {}
        items['fileList'] = fileList
        items['dirList'] = dirList
        utils.trace("ActionManager","onSetPublicAction",items)
        
        # Grab the remote instance and prepare to make the call
        remoteSession = AppController.getInstance().getRemoteSession()
        remoteSession.setItemVisibility(items, 'private')
        
        # Loop through the items and set their 'filePrivate' fields to 0
        for item in currentItems:
            item.setPrivate()
    
    def onOpenLinkAction(self):
        utils.trace("ActionManager","onOpenLinkAction","")
        from AppController import AppController
        from PyQt4.QtCore import QUrl
        from PyQt4.QtGui  import QDesktopServices

        bloopTree = AppController.getInstance().getMainViewController().getBloopTree()
        bloopTreeController = AppController.getInstance().getMainViewController().getBloopTreeController()

        itemURLs = [] 

        currentItems = bloopTree.selectedItems() 
        for item in currentItems:
            if item == bloopTreeController.getRootItem():
                remoteSession = AppController.getInstance().getRemoteSession()
                from models.mbu_config import meta
                itemURLs.append('http://' + meta['SERVER'] + '/' + remoteSession.getUsername())
            
            itemData = item.getItemData()
            if item.isFile() and itemData.has_key('fileURL') and itemData['fileURL'] is not None:
                itemURLs.append(itemData['fileURL'])
            else:
                itemURLs.append(item.getDirectoryURL())
            
            
        if len(itemURLs) > 1:
            from PyQt4.Qt import QMessageBox          
            confirmOpen = QMessageBox.warning(AppController.getInstance().getMainView(), 
                                                i18n.LABEL_CONFIRM_OPEN_MULTIPLE_LINKS_TITLE,
                                                i18n.LABEL_CONFIRM_OPEN_MULTIPLE_LINKS_MESSAGE,
                                                QMessageBox.Yes | QMessageBox.Cancel,
                                                QMessageBox.Yes);
            
            if confirmOpen == QMessageBox.Cancel:
                return
            
            
        for url in itemURLs:
            QDesktopServices.openUrl(QUrl(url))   
            
                        
    def onCopyLinkAction(self):
        utils.trace("ActionManager","onCopyLinkAction","")
        
        from AppController import AppController
        bloopTree = AppController.getInstance().getMainViewController().getBloopTree()

        # Grab the currently selected items (could be multiple selections)
        currentItems = bloopTree.selectedItems() 

        if currentItems is None:
            return
        
        from PyQt4.QtGui import QClipboard, QApplication
        clipboard = QApplication.clipboard()
        
        # Store the clipboard text in a specific format 
        copyText = ""
         
        for item in currentItems:
            if item.isFile():
                itemData = item.getItemData()
                copyText += itemData['fileURL'] + "\n"
            elif item.isDirectory() or item.isRoot():
                copyText += item.getDirectoryURL() + "\n"
                                
        clipboard.setText(copyText, QClipboard.Clipboard)
        utils.trace("ActionManager","onCopyLinkAction","Clipboard text set to:\n")
        utils.trace("ActionManager","onCopyLinkAction",copyText)
                      
    def onDownloadFileAction(self):
        utils.trace("ActionManager","onDownloadFileAction","")
        
        from AppController import AppController
        bloopTree = AppController.getInstance().getMainViewController().getBloopTree()

        # Grab the currently selected items (could be multiple selections)
        currentItem = bloopTree.currentItem() 
        if currentItem is None:
            return
        itemData = currentItem.getItemData()
        
        if itemData.has_key('fileDownloadURL'):
            from PyQt4.QtCore import QUrl
            from PyQt4.QtGui  import QDesktopServices
            QDesktopServices.openUrl(QUrl(itemData['fileDownloadURL']))
        else:
            from PyQt4.Qt import QMessageBox          
            confirmOpen = QMessageBox.warning(AppController.getInstance().getMainView(), 
                                                i18n.LABEL_CANNOT_DOWNLOAD_COPIED_FILE_TITLE,
                                                i18n.LABEL_CANNOT_DOWNLOAD_COPIED_FILE_MESSAGE,
                                                QMessageBox.Ok,
                                                QMessageBox.Ok);

    def onRenameAction(self):
        utils.trace("ActionManager","onRenameAction","")

        # Grab the currently selected items (could be multiple selections)
        from AppController import AppController
        bloopTree = AppController.getInstance().getMainViewController().getBloopTree()
        currentItem = bloopTree.currentItem() 
        
        if currentItem is None:
            return
        
        # Prepare to ask the user the new filename
        from PyQt4.QtGui import QInputDialog, QLineEdit

        if currentItem.isFile():
            itemData = currentItem.getItemData()
            itemType = 'FILE'
            itemId   = itemData['fileID']
            itemName = itemData['fileName']
            
            # Let them rename only the filename without the extension
            # The Bloop API doesn't want us to send the extension because
            # it will automatically add it.
            itemNameNoExt = utils.getFileNameNoExt(itemName)
            newName, okPressed = QInputDialog.getText(AppController.getInstance().getMainView(), "Rename File", "Enter the new file name:", QLineEdit.Normal, itemNameNoExt)
            
            # If they enter the same name, just don't bother making an API call.
            if newName == itemNameNoExt:
                return

        elif currentItem.isDirectory():
            itemData = currentItem.getItemData()
            itemType = 'DIRECTORY'
            itemId   = itemData['directoryID']
            itemName = itemData['directoryName']
            newName, okPressed = QInputDialog.getText(AppController.getInstance().getMainView(), "Rename Directory", "Enter the new directory name:", QLineEdit.Normal, itemName)

            # If they enter the same name, just don't bother making an API call.
            if newName == itemName:
                return
                
        # If they press anything but OK, get out of here
        if not okPressed:
            return
        
        AppController.getInstance().getMainView().statusBar().showMessage(i18n.LABEL_BLOOPTREE_STATUS_BAR_RENAMING)
        self.hireWorker(self.renameItem, currentItem, itemData, itemType, itemId, newName)
    
    def renameItem(self,currentItem, itemData, itemType, itemId, newName):
        from AppController import AppController
        AppController.getInstance().getMainView().statusBar().showMessage(i18n.LABEL_BLOOPTREE_STATUS_BAR_RENAMING)
        remoteSession = AppController.getInstance().getRemoteSession()
        result = remoteSession.renameItem(itemType, itemId, str(newName))    

        # If it was unsuccessful then lets display an error message
        if result['status'] == '0':
            from PyQt4.Qt import QMessageBox 
            QMessageBox.critical(AppController.getInstance().getMainView(), 
                                 i18n.LABEL_CONFIRM_RENAME_FILE_FAILED_TITLE,
                                 result['response'],
                                 QMessageBox.Ok,
                                 QMessageBox.Ok);
            AppController.getInstance().getMainView().statusBar().showMessage("")

            return

        # Update the data of the item in the list
        if currentItem.isFile():            
            currentItem.setText(0, result['fileName'])
            itemData['fileName'] = result['fileName']
            itemData['fileURL']  = result['fileURL']
            currentItem.setItemData(itemData)

        elif currentItem.isDirectory():
            currentItem.setText(0, result['directoryName'])
            itemData['directoryName'] = result['directoryName']
            currentItem.setItemData(itemData)

        AppController.getInstance().getMainView().statusBar().showMessage(i18n.LABEL_BLOOPTREE_STATUS_BAR_RENAMING_FINISHED)
        return 


    def onExitAction(self):
        from AppController import AppController
        AppController.getInstance().saveMainWindowSizes()
        import sys
        sys.exit(0)
    
    def onLogoutAction(self):
        utils.trace("ActionManager","onLogoutAction","")
        from AppController import AppController
        AppController.getInstance().logout()

    def onSendFeedbackAction(self):
        utils.trace("ActionManager","onSendFeedbackAction","")
        from PyQt4.QtCore import QUrl
        from PyQt4.QtGui  import QDesktopServices
        QDesktopServices.openUrl(QUrl(i18n.URL_SEND_FEEDBACK))

    def onViewChangelogAction(self):
        utils.trace("ActionManager","onViewChangelogAction","")
        from PyQt4.QtCore import QUrl
        from PyQt4.QtGui  import QDesktopServices
        QDesktopServices.openUrl(QUrl(i18n.URL_CHANGELOG))
        
    def onAboutDialogAction(self):
        utils.trace("ActionManager","onAboutDialogAction","")
        from PyQt4.Qt import QMessageBox , qVersion
        from AppController import AppController
        from models.mbu_config import meta
        QMessageBox.about(AppController.getInstance().getMainView(), 
                             i18n.LABEL_ABOUT_MSGBOX_TITLE,
                             i18n.LABEL_ABOUT_SUMMARY + "\n" + 
                             i18n.LABEL_ABOUT_VERSION + ": " + meta['APPLICATION_VERSION'] + "\n" + 
                             i18n.LABEL_ABOUT_API_VERSION + ": " + meta['API'] + "\n" +
                             i18n.LABEL_ABOUT_QT_VERSION + ": " + meta['QT_VERSION'] + "\n" +
                             i18n.LABEL_ABOUT_OS_NAME + ": " + meta['OS'] + "\n\n" +
                             i18n.LABEL_ABOUT_CREDITS + "\n\n" + 
                             i18n.LABEL_ABOUT_OPENSOURCE + "\n" + 
                             i18n.LABEL_ABOUT_COPYRIGHT);
        return        
        
        
            
    def onRefreshFolderAction(self):
        utils.trace("ActionManager","onRefreshFolderAction","")
        
        # Grab the currently selected item
        from AppController import AppController
        bloopTree = AppController.getInstance().getMainViewController().getBloopTree()
        bloopTreeController = AppController.getInstance().getMainViewController().getBloopTreeController()
        mainView = AppController.getInstance().getMainView()
        currentItem = bloopTree.currentItem()

        # Only executable on the root at this point
        if currentItem.isFile():
            return
        
        # Get the new contents
        mainView.statusBar().showMessage(i18n.LABEL_BLOOPTREE_STATUS_BAR_REQUESTING_FILES)        
        bloopTreeController.hireWorker(bloopTreeController.addItems, currentItem)
        
        # Open up the folder if it's not open already
        currentItem.setExpanded(True)
        mainView.statusBar().showMessage('')
        return
    
    
    def onNewFolderAction(self, val):
        utils.trace("ActionManager","onNewFolderAction","")

        # Grab the currently selected items (could be multiple selections)
        from AppController import AppController
        bloopTree = AppController.getInstance().getMainViewController().getBloopTree()
        bloopTreeController = AppController.getInstance().getMainViewController().getBloopTreeController()
        mainView = AppController.getInstance().getMainView()
        currentItem = bloopTree.currentItem()
        
        if currentItem is None:
            return
        
        # Can only create a new folder underneath the selected folder / root
        if currentItem == bloopTreeController.getRootItem():
            parentDirectoryId = 0 
        elif currentItem.isDirectory():
            itemData = currentItem.getItemData()
            parentDirectoryId = itemData['directoryID']
            
        else:
            mainView.statusBar().showMessage("")
            return
        
        
        # Prepare to ask the user the new filename
        from PyQt4.QtGui import QInputDialog, QLineEdit
        
        folderName = None
        okPressed = None

        while folderName is None or folderName is '':
            folderName, okPressed = QInputDialog.getText(mainView, 
                                                         "Create New Folder", 
                                                         "Enter a name for the new folder:", 
                                                         QLineEdit.Normal)
            if folderName is None:
                continue

            folderName = str(folderName)
            folderName = folderName.strip()
            if not okPressed:
                AppController.getInstance().getMainView().statusBar().showMessage("")
                return

        #Create the folder on a worker thread to keep UI responsive
        self.hireWorker(self.createNewFolder,
                        folderName,
                        currentItem, 
                        parentDirectoryId)
        
        mainView.statusBar().showMessage(i18n.LABEL_BLOOPTREE_STATUS_BAR_CREATING_FOLDER)
        
    def createNewFolder(self, folderName, currentItem, parentDirectoryId):
        #Invoked by onNewFolderAction() on a worker thread
        from AppController import AppController
        bloopTreeController = AppController.getInstance().getMainViewController().getBloopTreeController()
        mainView = AppController.getInstance().getMainView()
        mainView.statusBar().showMessage(i18n.LABEL_BLOOPTREE_STATUS_BAR_CREATING_FOLDER)
        remoteSession = AppController.getInstance().getRemoteSession()
        
        # Setting the new folder as public by default. We could contorl this by either having
        # a checkbox option in the Settings dialog or showing a [x] Mark Private field on the
        # QInputDialog? Will learn how to do that later.
        result = remoteSession.createFolder(folderName, parentDirectoryId, False)    

        print remoteSession.getCallStatus()

        # If the call failed, the result will contain the response message.
        if remoteSession.getCallStatus() == '0':
            from PyQt4.Qt import QMessageBox 
            QMessageBox.critical(mainView, 
                                 i18n.LABEL_CONFIRM_RENAME_FILE_FAILED_TITLE,
                                 result);
            mainView.statusBar().showMessage("")
            return


        # Update the folder contents        
        bloopTreeController.addItems(currentItem)
        
        # Open up the folder if it's not open already
        currentItem.setExpanded(True)
        
        mainView.statusBar().showMessage(i18n.LABEL_BLOOPTREE_STATUS_BAR_FOLDER_CREATED)
        return
    
    def onDeleteAction(self, val):
        '''
        Prepares for deletion of selected folders and files.
        If the user is sure, it will invoke deleteAction on a worker thread.
        '''
        utils.trace("ActionManager","onDeleteAction","")

        from AppController import AppController
        bloopTree = AppController.getInstance().getMainViewController().getBloopTree()

        # Grab the currently selected items (could be multiple selections)
        currentItems = bloopTree.selectedItems() 

        if currentItems is None:
            return

        if len(currentItems) > 0:
            from PyQt4.Qt import QMessageBox
            delConfirmMsg = i18n.LABEL_CONFIRM_FILE_DELETION_MESSAGE if len(currentItems) == 1 else i18n.LABEL_CONFIRM_FILES_DELETION_MESSAGE
            confirmDelete = QMessageBox.warning(AppController.getInstance().getMainView(), 
                                                i18n.LABEL_CONFIRM_FILES_DELETION_TITLE,
                                                delConfirmMsg,
                                                QMessageBox.Yes | QMessageBox.Cancel,
                                                QMessageBox.Yes);
            if confirmDelete == QMessageBox.Cancel:
                AppController.getInstance().getMainView().statusBar().showMessage("")
                return
            
        AppController.getInstance().getMainView().statusBar().showMessage(i18n.LABEL_BLOOPTREE_STATUS_BAR_DELETING)
        self.hireWorker(self.deleteAction, currentItems)
    
    def deleteAction(self, currentItems):
        from AppController import AppController
        bloopTreeController = AppController.getInstance().getMainViewController().getBloopTreeController()
        AppController.getInstance().getMainView().statusBar().showMessage(i18n.LABEL_BLOOPTREE_STATUS_BAR_DELETING)
        
        # Lets start looping through the selected items to gather a list
        # of what files / directories to delete
        itemList = {}
        itemList['fileList'] = []
        itemList['dirList']  = []
        for item in currentItems:
            itemData = item.getItemData()
            if item.isDirectory():
                itemList['dirList'].append(itemData['directoryID'])
            else:
                itemList['fileList'].append(itemData['fileID'])

        # This would always be successful unless they're attempting a hack.
        remoteSession = AppController.getInstance().getRemoteSession()
        remoteSession.deleteItem(itemList)
        
        for item in currentItems:
            itemData = item.getItemData()            
            # This is *way faster* than using the BloopTree's removeItemWidget, which is really slow
            if item != bloopTreeController.getRootItem():
                parent = item.parent()
                parent.removeChild(item)

        #print itemList
        AppController.getInstance().getMainView().statusBar().showMessage(i18n.LABEL_BLOOPTREE_STATUS_BAR_DELETING_FINISHED)
        
    def onPauseUploadAction(self):
        print "ActionManager.onPauseUploadAction()"
        upload_transactions = self.__getSelectedUploadTransactions()
        if upload_transactions is None:
            print "ActionManager.onPauseUploadAction() - No transactions selected"
            return
        
        for upload_transaction in upload_transactions:
            upload_transaction.stopUpload(False) #dont persist, notifyCancelled
        
        self.getUploadManagerViewController().getUploadManager().persistUploadTransactions()
    
    def onPauseAllUploadsAction(self):
        print "ActionManager.onPauseAllUploadsAction()"
        from models.upload_manager import UploadManager
        UploadManager.getInstance().stopAll()
    
    def onResumeUploadAction(self):
        print "ActionManager.onResumeUploadAction()"
        upload_transactions = self.__getSelectedUploadTransactions()
        if upload_transactions is None:
            print "ActionManager.onResumeUploadAction() - No transactions selected"
            return
        
        for upload_transaction in upload_transactions:
            if upload_transaction.getUploadStatus() == upload_transaction.STATUS_STOP:
                upload_transaction.setUploadStatus(upload_transaction.STATUS_GO) #dont persist, notifyCancelled
        
        self.getUploadManagerViewController().getUploadManager().persistUploadTransactions()
    
    def getUploadManagerViewController(self):
        from AppController import AppController
        return AppController.getInstance().getMainViewController().getUploadManagerViewController()
    
    def __getSelectedUploadTransactions(self):
        '''
        If any upload transaction(s) has/have been selected on the UploadManagerView
        this method will return it/them on a list, otherwise it will return None
        '''
        from AppController import AppController
        uploadManagerViewController = AppController.getInstance().getMainViewController().getUploadManagerViewController()
        upload_transactions = uploadManagerViewController.getSelectedUploadTransactions()
        return upload_transactions
    
    def onCancelUploadAction(self):
        print "ActionManager.onCancelUploadAction()"
        upload_transactions = self.__getSelectedUploadTransactions()
        if upload_transactions is None:
            print "ActionManager.onCancelUploadAction() - No transactions selected"
            return
        
        for upload_transaction in upload_transactions:
            upload_transaction.cancelUpload(False) #dont persist, notifyCancelled
        
        self.getUploadManagerViewController().getUploadManager().persistUploadTransactions()
    
    def onCancelAllUploadsAction(self):
        print "ActionManager.onCancelAllUploadsAction()"
        pass
        self.__loadUploadManager() #will be executed only once
        assert(self._uploadManager is not None)
        self._uploadManager.cancellAll()
    
    def onClearUnactiveUploadsAction(self):
        self.__loadUploadManager() #will be executed only once
        assert(self._uploadManager is not None)
        print "ActionManager.onClearUnactiveUploadsAction()"
        self._uploadManager.clearInactiveUploadTransactions()
    
    def getSetPrivateAction(self):
        return self._setPrivateAction
    
    def getCopyLinkAction(self):
        return self._copyLinkAction

    def getRefreshFolderAction(self):
        return self._refreshFolderAction

    def getOpenLinkAction(self):     
        return self._openLinkAction

    def getSetPublicAction(self):
        return self._setPublicAction

    def getNewFolderAction(self):
        return self._newFolderAction
    
    def getDeleteAction(self):
        return self._deleteAction
    
    def getRenameItemAction(self):
        return self._renameAction
    
    def getMoveAction(self):
        return self._moveAction
    
    def getExitAction(self):
        return self._exitAction
    
    def getDownloadFileAction(self):
        return self._downloadFileAction
    
    def getLogoutAction(self):
        return self._logoutAction
    
    def getPauseUploadAction(self):
        return self._pauseUploadAction
    
    def getPauseAllUploadsAction(self):
        return self._pauseAllUploadsAction
    
    def getResumeUploadAction(self):
        return self._resumeUploadAction
    
    def getCancelUploadAction(self):
        return self._cancelUploadAction

    def getCancelAllUploadsAction(self):
        return self._cancelAllUploadsAction
    
    def getClearUnactiveUploadsAction(self):
        return self._clearUnactiveUploadsAction
    
    def getAboutDialogAction(self):
        return self._aboutDialogAction