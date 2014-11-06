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

module controller.UploadManagerViewController

Controller classes for the UploadManagerView

This module will define the necessary controllers for all the visual objects
that represent the uploads.

The main classes will be the UploadManagerViewController, entry object
to access all the individual upload transactions.
'''
from PyQt4.QtCore import QObject
from UploadTransactionView import UploadTransactionView
from AppController import AppController
from models.upload_manager import UploadManager,UploadTransaction
from __init__ import Controller
import utils
import traceback
import sys

class UploadManagerViewController(Controller):
    _mainWindowController = None
    _remoteSession = None
    _uploadManager = None #reference to the current uploadManager on our remotesession
    _uploadTransactionViewControllers = None #Dictionary with all the UploadManagerViewControllers that
                                             #the uploadManager is working with.
                                             # key=uploadTransaction -> bucket=uploadTransactionViewController
                                             #The keys are the Upload Transactions
    _connectedUploadManagerSignalsAlready = False

    def __init__(self, view, mainWindowController):
        Controller.__init__(self,view)
        self.setMainWindowController(mainWindowController)
        self._uploadTransactionViewControllers = {}
        
        self.attemptConnectUploadManagerSignals()

    def getMainWindowController(self):
        return self._mainWindowController
    
    def setMainWindowController(self, controller):
        self._mainWindowController = controller

    def getRemoteSession(self,refresh=False):
        #Gets a reference to the remote session.
        #If you pass refresh, it will try to get the freshest reference from
        #the app controller at the time of the call.
        #Every time it finds itself without a session, it will try to refresh
        if self._remoteSession is None or refresh == True:
            self._remoteSession = AppController.getInstance().getRemoteSession()
        return self._remoteSession

    def attemptConnectUploadManagerSignals(self):
        '''
        The UploadManagerViewController will be listening for signals sent from
        the core (UploadManager), and it will use these signals to render the
        status of the UploadManager on the UploadManagerView, which is what the
        user sees.
        
        The logic in this method only happens once, this is, when we do our first
        drop (lazily), we don't need to overwhelm the app with signals it won't
        be using.
        
        If you add any more signals from the core, like say, in the future
        we decided to make uploads between 2 people cause a file is too large,
        we could add signals here when we detected that another user is helping
        you on the upload.
        '''
        if not self._connectedUploadManagerSignalsAlready:
            #Make sure that we have a reference to the upload manager on the core
            if self._uploadManager is None:
                self.getUploadManager(True)

            QObject.connect(self._uploadManager,
                            UploadManager.SIGNAL_UPDATE_UPLOAD_PERCENTAGE,
                            self.onUpdateUploadPercentage)
            QObject.connect(self._uploadManager,
                            UploadManager.SIGNAL_UPLOAD_STOPPED,
                            self.onUploadStopped)
            QObject.connect(self._uploadManager,
                            UploadManager.SIGNAL_UPLOAD_FINISHED,
                            self.onUploadFinished)
            QObject.connect(self._uploadManager,
                            UploadManager.SIGNAL_UPLOAD_QUEUED,
                            self.onUploadQueued)
            QObject.connect(self._uploadManager,
                            UploadManager.SIGNAL_UPLOAD_ERRORED,
                            self.onUploadErrored)
            QObject.connect(self._uploadManager,
                            UploadManager.SIGNAL_UPLOAD_CLEARED,
                            self.onUploadCleared)
            QObject.connect(self._uploadManager,
                            UploadManager.SIGNAL_UPLOAD_CANCELLED,
                            self.onUploadCancelled)
            QObject.connect(self._uploadManager,
                            UploadManager.SIGNAL_FOLDER_CREATED,
                            self.onFolderCreated)

            self._connectedUploadManagerSignalsAlready = True

            utils.trace('BloopTreeController','attemptConnectUploadManagerSignals','Connected upload manager to umvController')
    
        
    def getUploadManager(self, refresh=False):
        if self._uploadManager is None or refresh == True:
            self._uploadManager = UploadManager.getInstance(self.getRemoteSession(refresh))

        return self._uploadManager

    def onUpdateUploadPercentage(self, uploadTransaction):
        '''
        This method is supposed to receive an uploadTransaction that just got updated
        from the UploadManager (guy who's monitoring all uploads on the core)
        The goal here is this:
          - We have UploadTransactionViews (what the user sees)
          - They are controlled by UploadTransactionViewControllers
          - We're right now on the UploadManagerViewController...
          - We're supposed to match the UploadTransaction Object to a
            UploadTransactionViewController so that it can update its view with
            the most recent information about the uploadTransaction object
            
        To make this mapping, we have a _uploadTransactionViewControllers_ dict,
        whose keys are uploadTransaction objects.
        
        Right now we're getting exceptions about not finding the uploadTransaction
        object on the dict.
        
        This maybe:
         - Cause we never added it
         - Cause we're receiving a copy of the object or a new instance, instead
           of the same uploadTransaction reference.
        '''
        #utils.trace("UploadManagerViewController","onUpdateUploadPercentage",'Upload state of a transaction')
        #print uploadTransaction

        self.addOrRefreshUploadTransactionView(uploadTransaction)

    def onUploadStopped(self, uploadTransaction):
        utils.trace("UploadManagerViewController","onUploadStopped",uploadTransaction)
        self.addOrRefreshUploadTransactionView(uploadTransaction)

    def onUploadFinished(self, uploadTransaction):
        utils.trace("UploadManagerViewController","onUploadFinished",'Transaction Finished!')
        #print uploadTransaction.getFilePath(), "Finished", "(UMVC)"
        utils.trace("UploadManagerViewController","onUploadFinished",'Status: ' + str(uploadTransaction.getUploadStatus()) + " - " + uploadTransaction.getHumanUploadStatus())
        #print "TELL THE TREE TO REFRESH THE FOLDER WITH ID ->", str(uploadTransaction.getRemoteFolderId())
        assert(uploadTransaction.getRemoteFolderId() is not None)
        assert(self.getMainWindowController() is not None)
        assert(self.getMainWindowController().getBloopTreeController() is not None)
        #print "type of remote folder id",str(uploadTransaction.getRemoteFolderId()),type(uploadTransaction.getRemoteFolderId())
        self.getMainWindowController().getBloopTreeController().refreshFolderByRemoteId(uploadTransaction.getRemoteFolderId())

        self.addOrRefreshUploadTransactionView(uploadTransaction)

    def onUploadQueued(self, uploadTransaction):
        """
        This happens when the UploadManager signals a new UploadTransaction being Queued.
        
        The transaction should not be here, we don't want to upload the same file twice.
        
        This also happens if a transaction used to be in transit and now we put it back to the Queue
        and its status is STOP (paused).
        
        For the future:
         - We could ask if the transaction is here already, check the state and then ask the user
           what he wants to do, stop current transfer if its in progress, keep current transfer.
           
        For now:
         - We'll just ignore repeated uploadTransactions (if we can, since I guess we're using the
           transaction objects themselves as keys and their comparison methods may not be implemented
           yet.)
        
        WHAT HAPPENS HERE:   
            We receive a model an UploadTransaction object. We create a representation
            of it for the view, a UploadTransactionView, we create a controller for this new view.
            Then we map the uploadTransaction to the controller we've created 
            (in self._uploadTransactionViewControllers [dict])
            
            Then we tell our view (UploadManagerView) to add the view object to its display.
        """
        utils.trace("UploadManagerViewController","onUploadQueued",uploadTransaction)        
        
        #this will create the uploadtransaction view and its controller, and map it to this uploadTransaction
        #if that's already been done, it will do what's necessary to upload the view if the object is there already
        self.addOrRefreshUploadTransactionView(uploadTransaction)        

    def onUploadErrored(self, uploadTransaction):
        self.addOrRefreshUploadTransactionView(uploadTransaction)

    def onUploadCleared(self, uploadTransaction):
        '''
        This is the opposite of onUploadQueued, basically we don't want to know anything else
        about this upload transaction, its view counterpart nor the view's controller, so we wipe
        everything out, and then we tell the view to take care of it.
        '''
        if self._uploadTransactionViewControllers.has_key(uploadTransaction):
            utvController = self._uploadTransactionViewControllers.pop(uploadTransaction) #bye bye
            self.getView().removeUploadTransactionView(utvController.getView())
            del utvController
        else:
            print "UMVController uploadTransaction cannot be cleared, not here", uploadTransaction
            
    def onUploadCancelled(self, uploadTransaction):
        self.addOrRefreshUploadTransactionView(uploadTransaction)
    
    def onFolderCreated(self,parentFolderId, newFolderId):
        #utils.trace("UploadManagerViewController","onFolderCreated","Folder created ("+str(parentFolderId)+")")
        parentFolderId = int(parentFolderId)
        
        #Get to the Tree Controller and tell it to update parentFolderId using its map
        self.getMainWindowController().getBloopTreeController().refreshFolderByRemoteId(parentFolderId)
        
    def onTransactionDoubleClicked(self, upload_transaction_view, columnClicked):
        #This will stop (a.k.a. pause) a transaction if its uploading and its double clicked
        #If it was set to stop and we double click it again, we put it back into queued state.
        #Note: This assumes all stopped transactions are back in the UploadManager.UPLOAD_TRANSACTIONS queue. 
        
        upload_transaction = upload_transaction_view.getUploadTransactionModel()        
        assert(upload_transaction is not None)
        #print "=="
        #utils.trace("UploadManagerViewController","onTransactionDoubleClicked",upload_transaction)
        #print "=="
        
        #We pause it if its going
        if upload_transaction.getUploadStatus() == UploadTransaction.STATUS_GO:
            upload_transaction.setUploadStatus(UploadTransaction.STATUS_STOP)
        elif upload_transaction.getUploadStatus() == UploadTransaction.STATUS_QUEUED:
            upload_transaction.setUploadStatus(UploadTransaction.STATUS_GO)
        elif upload_transaction.getUploadStatus() == UploadTransaction.STATUS_STOP:
            upload_transaction.setUploadStatus(UploadTransaction.STATUS_QUEUED) 

    def addOrRefreshUploadTransactionView(self, uploadTransaction):
        '''
        If the given transaction model doesn't have a view, it will create it and assign a controller for it.
        If it's there already, it will get a hold of its controller, and it will tell the controller to
        refresh its old reference to the uploadTransaction, this will refresh the view.
        '''
        uploadTransactionViewController = None
        
        if self._uploadTransactionViewControllers.has_key(uploadTransaction):
            uploadTransactionViewController = self._uploadTransactionViewControllers[uploadTransaction]
        else:
            #Create UploadTransactionView and it's controller, map the uploadTransaction, to the viewController
            uploadTransactionView = UploadTransactionView(self.getView(),uploadTransaction)
            uploadTransactionViewController = UploadTransactionViewController(uploadTransactionView,self,uploadTransaction)
            self._uploadTransactionViewControllers[uploadTransaction] = uploadTransactionViewController
            self.getView().addUploadTransactionView(uploadTransactionView) #won't add twice

        #This should update the model on the controller, the controller should tell the view to refresh with new status
        if uploadTransactionViewController is not None:
            self._uploadTransactionViewControllers[uploadTransaction] = uploadTransactionViewController
            uploadTransactionViewController.setUploadTransaction(uploadTransaction)
            
    def tryRestoringUploads(self):
        try:
            self.getView().clearUploadTransactions()
            self.getUploadManager(True).restoreUploadTransactions()
        except:
            traceback.print_exc(10, file=sys.stdout)
            
    def getSelectedUploadTransactions(self):
        '''
        Returns a list of UploadTransactions objects that are selected.
        If any.
        '''
        if self._uploadTransactionViewControllers is None or len(self._uploadTransactionViewControllers)==0:
            return None

        result = []
        
        upload_transactions = self._uploadTransactionViewControllers.keys()
        for upload_transaction in upload_transactions:
            uploadTransactionViewController = self._uploadTransactionViewControllers[upload_transaction]
            uploadTransactionView = uploadTransactionViewController.getView()
            if uploadTransactionView.isSelected():
                result.append(upload_transaction)
                
        if len(result) == 0:
            return None
        
        return result
            
class UploadTransactionViewController(Controller):
    '''
    Controls a single UploadTransactionView object.
    
    This guy gets orders fromt he UploadManagerViewController.
    He tells him about the stage of its UploadTransaction and he's responsible
    of updating his view.
    '''
    
    _uploadManagerViewController = None
    _uploadTransaction = None #the transaction we're about to represent on screen

    def __init__(self,view,uploadManagerViewController,uploadTransaction = None):
        '''
        Constructor of this controller:
         - view - UploadTransactionView
         - uploadManagerViewController - The UploadManagerViewController for this and 
                                         the rest of the UploadTransactionView objects.
        '''
        Controller.__init__(self,view)
        self.setUploadManagerViewController(uploadManagerViewController)
        self.setUploadTransaction(uploadTransaction)
        
        if uploadTransaction is not None:
            self.getView().updateUploadTransactionModel(uploadTransaction)
        
    def setUploadManagerViewController(self,umvc):
        self._uploadManagerViewController = umvc
        
    def getUploadManagerViewController(self):
        '''
        This UploadTransaction controller has a reference
        to the UploadManagerViewController.
        '''
        return self._uploadManagerViewController
    
    def setUploadTransaction(self, uploadTransaction):
        self._uploadTransaction = uploadTransaction
        assert(self.getView() is not None)
        utils.trace("UploadTransactionViewController","setUploadTransaction","about to tell the view to update the model data")
        self.getView().updateUploadTransactionModel(self.getUploadTransaction())
        
    def getUploadTransaction(self):
        return self._uploadTransaction