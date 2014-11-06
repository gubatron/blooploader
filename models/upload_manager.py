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

module models.upload_manager
'''
import os
import copy
import simplejson
import sys
import md5
from getter_setter import GetterSetter
from models.upload_token import UploadToken
from models.qhttp_upload_proxy import QHttpUploadProxy, UploadEndedException, UploadStoppedException, UploadCancelledException
from utils import trace, getFileName, showTraceback, printDict, printList
from utils.Employer import Employer
from PyQt4.QtCore import QObject, SIGNAL, QThread, QMutex, QMutexLocker, QTimer


class UploadManager(GetterSetter,Employer):
    UPLOAD_MANAGER = None #Singleton Instance
    UPLOAD_TRANSACTIONS = None
    IN_TRANSIT = None
    MAX_CONCURRENT_UPLOADS = None
    FINISHED = None
    FAILED = None
    REMOTE_SESSION = None
    GUI_CONTROLLER = None
    
    UPLOADS_DAT_FILEPATH = os.path.join('resume','uploads.dat')
    
    UPLOAD_TRANSACTIONS_LOCK = None
    IN_TRANSIT_LOCK = None
    PERSISTENCE_LOCK = None
    
    UPLOAD_TRANSACTIONS_TIMER = None
    
    TRANSACTION_ADDED_TO_IN_TRANSIT = 1
    TRANSACTION_ALREADY_IN_TRANSIT = 0
    TRANSACTION_NOT_ADDED_IN_TRANSIT = -1
    
    #SIGNALS TO REPORT ON % OF UPLOAD, oR CHANGES OF STATUS
    SIGNAL_UPDATE_UPLOAD_PERCENTAGE = SIGNAL('updateUploadPercentage(PyQt_PyObject)') #sends UploadTransaction Object
    SIGNAL_UPLOAD_STOPPED = SIGNAL('uploadStopped(PyQt_PyObject)') #sends UploadTransaction Object
    SIGNAL_UPLOAD_FINISHED = SIGNAL('uploadFinished(PyQt_PyObject)') #sends UploadTransaction Object
    SIGNAL_UPLOAD_QUEUED = SIGNAL('uploadQueued(PyQt_PyObject)') #Sends UploadTransaction Object
    SIGNAL_UPLOAD_ERRORED = SIGNAL('uploadErrored(PyQt_PyObject)') #Sends UploadTransaction Object
    SIGNAL_UPLOAD_CANCELLED = SIGNAL('uploadCancelled(PyQt_PyObject)') #Sends UploadTransaction Object
    SIGNAL_UPLOAD_CLEARED = SIGNAL('uploadCleared(PyQt_PyObject)') #Sends UploadTransaction Object to be cleared
    SIGNAL_FOLDER_CREATED = SIGNAL('folderCreated(int,int)') #Sends the ID of the parent folder and the new folder that was created

    SIGNAL_UPLOAD_TRANSACTIONS_RESTORED = SIGNAL('uploadTransactionsRestored()') #Sent when all transaction are restored to we can start timers from main thread

    ORIGINAL_UPLOAD_MANAGER_THREAD = None

    '''An upload manager is a Singleton object in charge
       of using a RemoteSession to upload a set of files and/or directories.
       
       An UploadTransaction creates its own thread and it should be able to:
       - Upload directories (Creating directories if necessary)
       - Upload files (through an UploadWorker thread, or UploadWorkers)
       - Report on the status of a file upload
       - Report on the complete percentage of the upload transaction
       - Pause the transaction
       - Stop the transaction
       - Pause on of the files from being uploaded
       - Cancel one of the files from being uploaded
       - Generate a final report on the upload transaction (JSON)'''
    
    def __init__(self,remoteSession):
        GetterSetter.__init__(self)
        Employer.__init__(self)
        self.UPLOAD_TRANSACTIONS_LOCK = QMutex()
        self.IN_TRANSIT_LOCK = QMutex()
        self.PERSISTENCE_LOCK = QMutex() #To avoid threads from persisting at the same time
        
        self.UPLOAD_TRANSACTIONS = {} #queue of upload transaction objects
        self.IN_TRANSIT = {}
        
        self.UPLOAD_TRANSACTIONS_TIMER = QTimer()
        self.UPLOAD_TRANSACTIONS_TIMER.setInterval(2000) #check every second for queued transactions
        self.connect(self.UPLOAD_TRANSACTIONS_TIMER,SIGNAL("timeout()"), self.checkUploadTransactions)
        self.connect(self, self.SIGNAL_UPLOAD_TRANSACTIONS_RESTORED, self.attemptToStartUploadTransactionsTimer)

        self.MAX_CONCURRENT_UPLOADS = 3 #when this code is stable enough this will be a user setting (up to a max defined by us)

        #still not too sure about these two here
        self.FINISHED = {} #UploadTransactions that finished (don't know if I want to keep all these alive, will have to flush eventually)
        self.FAILED = {} #UploadTransactions that failed
        
        self.setRemoteSession(remoteSession)
        
        UploadManager.ORIGINAL_UPLOAD_MANAGER_THREAD = self.thread()
    
    @staticmethod
    def getInstance(remoteSession = None):
        #Creates a new Session and tries to recover from uploads.dat
        if UploadManager.UPLOAD_MANAGER is None and remoteSession is not None:
            UploadManager.UPLOAD_MANAGER = UploadManager(remoteSession)

        #If the last UPLOAD_MANAGER INSTANCE has no session, set this session object
        if UploadManager.UPLOAD_MANAGER.getRemoteSession() is None and remoteSession is not None:
            UploadManager.UPLOAD_MANAGER.setRemoteSession(remoteSession)

        #Question: What happens if they give me another remote session?
        #Should I keep 2 instances? several upload managers?

        return UploadManager.UPLOAD_MANAGER
    
    def shutdown(self):
        '''
        Stops all active uploads, clears all inactive ones, resets everything,
        then gets rid of the upload manager singleton. To be used when logging out.
        '''
        self.stopAll()
        self.clearInactiveUploadTransactions()
        self.IN_TRANSIT = {}
        self.UPLOAD_TRANSACTIONS = {}
        self.FINISHED = {}
        self.FAILED = {}
        self.stopUploadTransactionsTimer()
        UploadManager.UPLOAD_MANAGER = None #remote the singleton
        
        
    def cancellAll(self):
        self.stopAll()
        
        if len(self.UPLOAD_TRANSACTIONS) > 0:
            keys = self.UPLOAD_TRANSACTIONS.keys()
            for key in keys:
                uploadTransaction = self.UPLOAD_TRANSACTIONS.pop(key)
                uploadTransaction.cancelUpload(False) #persist=False, notifyCancelled=True
        
        self.persistUploadTransactions()
    
    def stopAll(self):
        '''
        Stops all transaction IN_TRANSIT and moves them back to UPLOAD_TRANSACTION
        Stops the UPLOAD_TRANSACTIONS_TIMER so no queued transactions will go back to
        IN_TRANSIT
        '''
        self.stopUploadTransactionsTimer()
        
        if len(self.IN_TRANSIT) > 0:
            keys = self.IN_TRANSIT.keys()
            for key in keys:
                uploadTransaction = self.IN_TRANSIT.pop(key)
                uploadTransaction.stopUpload(True)

        self.stopUploadTransactionsTimer()
    
    def clearInactiveUploadTransactions(self):
        '''
        Removes all UploadTransactions that are Finished, Cancelled or Errored.
        Emits  signals so that the controller will take care of the views that
        represent these upload transactions.
        
        This method is usually invoked through an action on the ActionManager.
        
        For each UploadTransaction cleared (removed) it will emit a SIGNAL_UPLOAD_CLEARED 
        '''

        def clearUploadTransactionDictionary(dictionary):
            #clear all cancelled,ended, or errored from the given dictionary
            if dictionary is not None and len(dictionary) > 0:
                keys = dictionary.keys()
                for key in keys: #iterate through the keys to avoid RunTime Error when dict changes size
                    uploadTransaction = dictionary[key]
                    assert(uploadTransaction is not None)
                    
                    if uploadTransaction.getUploadStatus() in (UploadTransaction.STATUS_CANCELLED,
                                                               UploadTransaction.STATUS_ENDED,
                                                               UploadTransaction.STATUS_ERROR):
                        dictionary.pop(key) #take it out
                        
                        #Let the controller deal with the GUI and whoever else he needs to deal with
                        #in regards to clearing an UploadTransaction
                        self.emit(UploadManager.SIGNAL_UPLOAD_CLEARED,uploadTransaction)
                        #print "UploadManager.emit(SIGNAL_UPLOAD_CLEARED)"

        clearUploadTransactionDictionary(self.FINISHED)
        clearUploadTransactionDictionary(self.FAILED)
        
        #in case there's a transaction that shouldn't be here
        clearUploadTransactionDictionary(self.UPLOAD_TRANSACTIONS) 

        #Finished and Failed should now be cleared
        assert(len(self.FINISHED) == 0)
        assert(len(self.FAILED) == 0)
        
        self.persistUploadTransactions()

    def removeTransactionFromTransit(self, uploadTransaction):
        #inTransitMutexLocker = QMutexLocker(self.IN_TRANSIT_LOCK)
        if self.IN_TRANSIT.has_key(uploadTransaction.getFilePath()):
            self.IN_TRANSIT.pop(uploadTransaction.getFilePath())

    
    def addTransactionToTransit(self, uploadTransaction):
        """This method won't add a transaction right away to IN_TRANSIT.
        A transaction could already be in transit, or there could be no room left
        to be in transit.
        Return values:
            TRANSACTION_ADDED_TO_IN_TRANSIT
            TRANSACTION_ALREADY_IN_TRANSIT
            TRANSACTION_NOT_ADDED_IN_TRANSIT
        """
        if not self.IN_TRANSIT.has_key(uploadTransaction.getFilePath()):
            if len(self.IN_TRANSIT) > self.MAX_CONCURRENT_UPLOADS:
                return self.TRANSACTION_NOT_ADDED_IN_TRANSIT

            self.IN_TRANSIT[uploadTransaction.getFilePath()] = uploadTransaction
            return self.TRANSACTION_ADDED_TO_IN_TRANSIT
        else:
            trace("UploadManager","addTransactionToTransit","transaction was already in transit")
            return self.TRANSACTION_ALREADY_IN_TRANSIT

            
    def addTransactionToFinished(self, uploadTransaction):
        self.FINISHED[uploadTransaction.getFilePath()] = uploadTransaction
        
    def addTransactionToUploadTransactions(self, uploadTransaction):
        #usually used when an upload has been stopped on purpose, we put it back on the queue
        trace("UploadManager","addTransactionToUploadTransactions",uploadTransaction)
        if not self.UPLOAD_TRANSACTIONS.has_key(uploadTransaction.getFilePath()):
            self.UPLOAD_TRANSACTIONS[uploadTransaction.getFilePath()] = uploadTransaction

    def removeTransactionFromUploadTransactions(self, uploadTransaction):
        #remove an upload transaction from the UPLOAD_TRANSACTIONS dict.
        #this dictionary holds transactions that are Queued, or Stopped (aka Paused)
        #uploadTransactionMutexLocker = QMutexLocker(self.UPLOAD_TRANSACTIONS_LOCK)
        if self.UPLOAD_TRANSACTIONS.has_key(uploadTransaction.getFilePath()):
            self.UPLOAD_TRANSACTIONS.pop(uploadTransaction.getFilePath())
        
    def popNextQueuedUploadTransaction(self):
        '''
        When the upload manager needs to check for a transaction to upload,
        it needs to check if the status of the transaction is good to go or not.
        This will iterate through the UPLOAD_TRANSACTIONS until it finds
        a transaction that's good to go, if it wont find any, it will return
        none.
        '''
        if self.UPLOAD_TRANSACTIONS is None or len(self.UPLOAD_TRANSACTIONS) == 0:
            return None
        
        result = None
        #uploadTransactionMutexLocker = QMutexLocker(self.UPLOAD_TRANSACTIONS_LOCK)

        for filepath in self.UPLOAD_TRANSACTIONS:
            transaction = self.UPLOAD_TRANSACTIONS[filepath]
            
            #we found what we wanted, we'll remove it from the UPLOAD_TRANSACTIONS
            if transaction.getUploadStatus() == UploadTransaction.STATUS_QUEUED:
                result = self.UPLOAD_TRANSACTIONS.pop(filepath)
                break
        
        return result   
        
        
    def addTransactionToFailed(self, uploadTransaction):
        self.FAILED[uploadTransaction.getFilePath()] = uploadTransaction
    
    def getRemoteSession(self):
        return self.REMOTE_SESSION
    
    def setRemoteSession(self,remoteSession):
        self.REMOTE_SESSION = remoteSession
        UploadManager.UPLOADS_DAT_FILEPATH = os.path.join('resume',remoteSession.getUsername(),'uploads.dat')
    
    def addFolder(self,folderPath,targetRemoteFolderId):
        #get files on the remote folder first than anything
        remoteFolderContents = self.REMOTE_SESSION.getUserFiles(targetRemoteFolderId)

        #we check if the folder exists or not up there
        folderAlreadyExists = False
        remoteSubDirId = 0
        if remoteFolderContents is not None:
            remoteFolders = {}
            remoteFolders = remoteFolderContents['directories']
            
            localFolderName = getFileName(folderPath)
            assert(localFolderName is not None)
            assert(localFolderName != "")
            folderAlreadyExists = self._isFolderInRemoteList(localFolderName,remoteFolders)

            if folderAlreadyExists:
                #grab the subfolder id
                #trace("UploadManager","addFolder","Folder already exists, no need to create it ("+localFolderName+")")
                remoteSubDir= self._getFolderInRemoteList(localFolderName,remoteFolders)
                remoteSubDirId = remoteSubDir['directoryID']
            else:
                #create the folder
                try:
                    #trace("UploadManager","addFolder","Folder wasn't there, create it ("+localFolderName+","+str(remoteSubDirId)+")")
                    remoteSubDirId = self.REMOTE_SESSION.createFolder(localFolderName, targetRemoteFolderId, False)
                    #trace("UploadManager","addFolder","REMOTE FOLDER RESULT -> " + str(remoteSubDirId))
		            #Notify here our upload_manager view so it tells the tree that it should put a new folder
	                #Then whatever file will be uploaded to this folder, that folder has to be refreshed to show the progress
                    #of the folder
                except Exception,e:
                    raise e
                self.notifyFolderCreated(targetRemoteFolderId, remoteSubDirId)
        else:
            #empty remote dir, let's create the subdir.
            try:
                localFolderName = getFileName(folderPath)
                #trace("UploadManager","addFolder","Remote Folder was empty, create it ("+localFolderName+","+str(remoteSubDirId)+")")
                remoteSubDirId = self.REMOTE_SESSION.createFolder(localFolderName, targetRemoteFolderId,False)                
                #trace("UploadManager","addFolder","REMOTE FOLDER RESULT -> " + str(remoteSubDirId))
            except Exception, e:
                raise e
        
        localFolderContents = os.listdir(folderPath)
        
        if len(localFolderContents) == 0:
            #nothing to add
            return
        
        for item in localFolderContents:
            #print "folderPath: " + folderPath
            #print "item: " + str(item)
            itemPath = folderPath + os.path.sep + item
            #print "itemPath: " + itemPath
            
            #print "About to add " + itemPath
            if os.path.isdir(itemPath):
                #print "Its a dir"
                self.addFolder(itemPath,remoteSubDirId)
            elif os.path.isfile(itemPath):
                #print "Its a file"
                #self.addFile(itemPath,remoteSubDirId, remoteFolderContents,False)
                self.hireWorker(self.addFile,
                                itemPath,
                                remoteSubDirId,
                                remoteFolderContents,
                                False) #persist=False
            else:
                print "Trying to add something other than a file or directory"
        
        #we persist only at the end
        self.persistUploadTransactions()
        
        #we attempt to start the timer in case it could not be
        #started from the sub-threads
        self.attemptToStartUploadTransactionsTimer()
    
    def addFile(self,filePath,targetRemoteFolderId,remoteFolderContents,persist=True):
        '''
        Once we have a file, we add it to the queue of files to be uploaded
        '''
        assert(filePath is not None)
        assert(targetRemoteFolderId is not None)
        
        #first we check the file doesn't exist already
        fileName = getFileName(filePath)
        remoteFiles = remoteFolderContents['files']

        if self._isFileInRemoteList(fileName,remoteFiles):
            #trace("UploadManager","addFile","Skipping [%s], already uploaded." % fileName)
            dummyTransaction = UploadTransaction(filePath,targetRemoteFolderId,self)
            dummyTransaction.setUploadStatus(UploadTransaction.STATUS_ENDED)
            return

        uploadTransaction = UploadTransaction(filePath, 
                                              targetRemoteFolderId,
                                              self)
        #uploadTransaction.initUploadToken()
        
        #will end up queuing the transaction and starting the upload_transaction timer
        uploadTransaction.setUploadStatus(UploadTransaction.STATUS_QUEUED,persist)
        
        self.attemptToStartUploadTransactionsTimer() 

    def _isFileInRemoteList(self,fileName,remoteFileList):
        #TODO: Add local md5 vs remote md5 check
        '''Given a dir name, checks if the directory is or not on the remote dir list'''
        if remoteFileList == None:
            return False

        for file in remoteFileList:
            if file['fileName'] == fileName:
                return True

        return False

    def _isFolderInRemoteList(self,dirName,remoteDirList):
        '''Given a dir name, checks if the directory is or not on the remote dir list'''
        if remoteDirList == None:
            return False
        
        for dir in remoteDirList:
            if dir['directoryName'] == dirName:
                return True

        return False

    def _getFolderInRemoteList(self,dirName,remoteDirList):
        if remoteDirList == None:
            return False

        for dir in remoteDirList:
            if dir['directoryName'] == dirName:
                return dir

    def attemptToStartUploadTransactionsTimer(self):
        if not self.UPLOAD_TRANSACTIONS_TIMER.isActive():
            trace("UploadManager","attempToStartTimer()","about to...")
            try:
                UploadManager.getInstance().UPLOAD_TRANSACTIONS_TIMER.start()
                trace("UploadManager","attempToStartTimer()",str(self.UPLOAD_TRANSACTIONS_TIMER.isActive()))
            except Exception, e:
                print "OMG",e
            
            assert(self.UPLOAD_TRANSACTIONS_TIMER.isActive())
        else:
            trace("UploadManager","attemptToStartUploadTransactionsTimer","Timer was already running")

        #self.checkUploadTransactions()

    def stopUploadTransactionsTimer(self):
        self.UPLOAD_TRANSACTIONS_TIMER.stop()
        QObject.disconnect(self.UPLOAD_TRANSACTIONS_TIMER,SIGNAL("timeout()"),self.checkUploadTransactions) #disconnects QT signals
        assert(not self.UPLOAD_TRANSACTIONS_TIMER.isActive())

    def checkUploadTransactions(self):
        '''This checks how many upload transactions are in transit
        and how many are queued up.
        If there's room to start a new upload this will do so.
        '''
        self.traceUploadTransactions("checkUploadTransactions")

        if len(self.UPLOAD_TRANSACTIONS) == 0:
            trace("UploadManager", "checkUploadTransactions","Stopping the timer, nothing further to transfer")
            self.UPLOAD_TRANSACTIONS_TIMER.stop()
            return

        if len(self.IN_TRANSIT) >= self.MAX_CONCURRENT_UPLOADS:
            trace("UploadManager","checkUploadTransactions","still not ready to add more transactions on the in TRANSIT queue")
            return

        #execute those who are waiting if there's room for more workers
        if len(self.UPLOAD_TRANSACTIONS) > 0 and len(self.IN_TRANSIT) < self.MAX_CONCURRENT_UPLOADS:
            #self.traceUploadTransactions()

            #put popped transaction in here
            upload_transaction = self.popNextQueuedUploadTransaction()

            #Upload Transactions available are stopped, or errored, nobody else is ready
            #We shutdown the transactions timer
            if upload_transaction is None:
                self.stopUploadTransactionsTimer()
                return

            #it will start uploading if it hasn't done so already, put it on the right queue, and what not.
            upload_transaction.setUploadStatus(UploadTransaction.STATUS_GO)

    def notifyUploadGoing(self, uploadTransaction, persistUploadTransactions=True, emitSignal=True):
        trace('UploadManager','notifyUploadGoing(): persistUploadTransactions=',str(persistUploadTransactions)+" Uploaded " + str(uploadTransaction.getUploadPercentage()) + "% of " + unicode(uploadTransaction.getFilePath()).encode('iso-8859-1'))
        
        if emitSignal:
            self.emit(UploadManager.SIGNAL_UPDATE_UPLOAD_PERCENTAGE, uploadTransaction)
            
        if persistUploadTransactions:
            self.persistUploadTransactions()

    def notifyUploadPercentageChanged(self,uploadTransaction, persistUploadTransactions=True, emitSignal=True):
        trace('UploadManager','notifyUploadPercentageChanged(): persistUploadTransactions=',str(persistUploadTransactions)+" Uploaded " + str(uploadTransaction.getUploadPercentage()) + "% of " + unicode(uploadTransaction.getFilePath()).encode('iso-8859-1'))

        '''
        I see no reason to move the upload from wherever it is on this method.
        This logic should probably be elsewhere.
        self.removeTransactionFromUploadTransactions(uploadTransaction)        
        
        if putInTransit:
            self.addTransactionToTransit(uploadTransaction)
        '''

        if emitSignal:
            self.emit(UploadManager.SIGNAL_UPDATE_UPLOAD_PERCENTAGE,uploadTransaction)
            print "UploadManager.emit(SIGNAL_UPLOAD_UPLOAD_PERCENTAGE)"
        
        if persistUploadTransactions:
            #self.hireWorker(self.persistUploadTransactions)
            self.persistUploadTransactions()

    def notifyUploadStopped(self, uploadTransaction, persistUploadTransactions=True):
        trace('UploadManager','notifyUploadStopped','Upload stopped ('+uploadTransaction.getFilePath()+')')
        self.removeTransactionFromTransit(uploadTransaction)
        self.addTransactionToUploadTransactions(uploadTransaction)
        self.emit(UploadManager.SIGNAL_UPLOAD_STOPPED,uploadTransaction)
        print "UploadManager.emit(SIGNAL_UPLOAD_STOPPED)"
        
        if persistUploadTransactions:
            #self.hireWorker(self.persistUploadTransactions)
            self.persistUploadTransactions()
    
    def notifyUploadFinished(self, uploadTransaction, persistUploadTransactions=True):
        trace('UploadManager','notifyUploadFinished','Upload finished ('+uploadTransaction.getFilePath()+')')
        self.removeTransactionFromTransit(uploadTransaction)
        self.removeTransactionFromUploadTransactions(uploadTransaction) #just in case
        self.addTransactionToFinished(uploadTransaction)
        self.emit(UploadManager.SIGNAL_UPLOAD_FINISHED,uploadTransaction)
        print "UploadManager.emit(SIGNAL_UPLOAD_FINISHED)"

        if persistUploadTransactions:
            #self.hireWorker(self.persistUploadTransactions)
            self.persistUploadTransactions()

        self.checkUploadTransactions()

    def notifyUploadQueued(self, uploadTransaction, persistUploadTransactions=True):
	    # this is the first state of a transaction, however, we never know if
        # by allowing users to put a setting on how many transactions at the same time they may do
        # when they reduce the number, in transit transactions could be sent to a queued state
        # and we might need to notify other objects of the new state of the transaction
        trace('UploadManager','notifyUploadQueued','Upload queued('+uploadTransaction.getFilePath()+')')
        self.removeTransactionFromTransit(uploadTransaction)
        self.addTransactionToUploadTransactions(uploadTransaction)
        self.emit(UploadManager.SIGNAL_UPLOAD_QUEUED, uploadTransaction)
        print "UploadManager.emit(SIGNAL_UPLOAD_QUEUED)"
        
        if persistUploadTransactions:
            #self.hireWorker(self.persistUploadTransactions)
            self.persistUploadTransactions()
        
        if not self.UPLOAD_TRANSACTIONS_TIMER.isActive():
            self.attemptToStartUploadTransactionsTimer()

    def notifyUploadErrored(self, uploadTransaction, persistUploadTransactions=True):
        # this could be the same as notify upload added
        trace('UploadManager','notifyUploadQueued','Upload queued('+uploadTransaction.getFilePath()+')')
        self.removeTransactionFromTransit(uploadTransaction)
        self.removeTransactionFromUploadTransactions(uploadTransaction) #just in case
        self.addTransactionToFailed(uploadTransaction)
        self.emit(UploadManager.SIGNAL_UPLOAD_ERRORED, uploadTransaction)
        print "UploadManager.emit(SIGNAL_UPLOAD_ERRORED)"
        uploadTransaction.setUploadProxy(None)
        
        if uploadTransaction.getUploadToken():
            uploadTransaction.getUploadToken().clear()
        
        if persistUploadTransactions:
            #self.hireWorker(self.persistUploadTransactions)
            self.persistUploadTransactions()

    def notifyUploadCancelled(self, uploadTransaction, persistUploadTransaction=True):
        trace('UploadManager','notifyCancelled','Upload cancelled ('+uploadTransaction.getFilePath()+')')
        self.emit(UploadManager.SIGNAL_UPLOAD_CANCELLED, uploadTransaction)
        print "UploadManager.emit(SIGNAL_UPLOAD_CANCELLED)"
        
        self.removeTransactionFromTransit(uploadTransaction) #just in case
        self.removeTransactionFromUploadTransactions(uploadTransaction) #just in case

        if persistUploadTransaction:
            #self.hireWorker(self.persistUploadTransactions)
            self.persistUploadTransactions()
        
    def notifyFolderCreated(self, parentFolderId, newFolderId):
        trace('UploadManager','notifyFolderCreated','('+str(parentFolderId)+','+str(newFolderId)+')')
        self.emit(UploadManager.SIGNAL_FOLDER_CREATED,int(parentFolderId), int(newFolderId))
        print "UploadManager.emit(SIGNAL_UPLOAD_FOLDER_CREATED)"
    
    def traceUploadTransactions(self,context=None):
        print
        print "="*90
        if context is not None:
            print "(",context,")"
        trace("UploadManager","traceUploadTransactions","IN_TRANSIT (uploading): " + str(len(self.IN_TRANSIT)) + " @" + str(hex(id(self))))
        printDict(self.IN_TRANSIT)
        trace("UploadManager","traceUploadTransactions","UPLOAD_TRANSACTIONS (waiting): " + str(len(self.UPLOAD_TRANSACTIONS)) + " @" + str(hex(id(self))))
        printDict(self.UPLOAD_TRANSACTIONS)
        print "="*90
        print

    def persistUploadTransactions(self):
        '''
        Persists the status of all transactions on the .resume/ folder
        so that we can recover in case the user closes the application
        or on crash.
        
        Invoke this method on meaningful transaction events.
        
        The states will be persisted on a file called .resume/uploads.dat
        
        It will persist a list of simple dictionaries that represent
        each one of the transactions that were pending or in traffic.
        '''
        trace("UploadManager","persistUploadTransactions","invoked")
        persistence_list = []
        
        def _appendTransactionDicts(persistence_list, transaction_dictionary):
            if transaction_dictionary is not None and len(transaction_dictionary) > 0:
                filePaths = transaction_dictionary.keys()
                seenHashes = []
                for filePath in filePaths:
                    upload_transaction = None
                    if transaction_dictionary.has_key(filePath):
                        upload_transaction = transaction_dictionary[filePath]
                    else:
                        #no longer here. This dictionary could be altered while this happens
                        continue
                    
                    if upload_transaction.getUploadStatus() in (upload_transaction.STATUS_ERROR,
                                                                upload_transaction.STATUS_CANCELLED,
                                                                upload_transaction.STATUS_ENDED):

                        #skip irrelevant transaction and clear token files if they exist
                        if upload_transaction.getUploadToken() is not None:
                            try:
                                upload_transaction.getUploadToken().clear()
                            except:
                                pass
                        continue
                    
                    hash = None
                    if upload_transaction.getFileData() is None:
                        upload_transaction.prepareFileData(upload_transaction.getFilePath())
                    hash = upload_transaction.getFileData()['fldFileMD5']
                    
                    #latest upload token we got
                    uploadToken = upload_transaction.getUploadToken()
                    bytesSent = 0
                    
                    #we'll count only until the last token, sorry.
                    if uploadToken is not None:
                        if uploadToken.shouldEnd():
                            bytesSent = upload_transaction.getFileSize()
                        else:
                            bytesSent = upload_transaction.getSafeBytesSent()
                    
                    #avoid persisting a hash with 2 different states
                    if hash in seenHashes:
                        print "persistUploadTransaction: Warning, there's a transaction in 2 dictionaries at the same time"
                        print hash,filePath
                        continue
                    
                    seenHashes.append(hash)
                    persistence_list.append({'hash':hash,
                                             'filePath':filePath,
                                             'status':upload_transaction.getUploadStatus(),
                                             'remoteFolderId':upload_transaction.getRemoteFolderId(),
                                             'bytesSent':bytesSent,
                                             'uploadPercentage':upload_transaction.getUploadPercentage()})
            return persistence_list

        #persistenceMutexLocker = QMutexLocker(self.PERSISTENCE_LOCK)
        persistence_list = _appendTransactionDicts(persistence_list, self.UPLOAD_TRANSACTIONS)
        persistence_list = _appendTransactionDicts(persistence_list, self.IN_TRANSIT)

        #Blooploader... Persist!
        filePath = UploadManager.UPLOADS_DAT_FILEPATH
        
        if os.path.exists(filePath):
            try:
                os.unlink(filePath)
            except:
                showTraceback("UploadManager.persistUploadTransactions() could not unlink the past file")
            finally:
                pass
        else:
            #make sure all folders are there to persist the transactions
            if not os.path.exists('resume'):
                os.mkdir('resume')
            
            if not os.path.exists(os.path.join('resume',self.getRemoteSession().getUsername())):    
                os.mkdir(os.path.join('resume',self.getRemoteSession().getUsername()))
        
        try:
            filePath = os.path.abspath(filePath)
            f = open(filePath,"w")
            f.write(simplejson.dumps(persistence_list))
            f.close()
            
            trace("UploadManager","persistUploadTransactions","persisted sucessfully at " + filePath)
            printList(persistence_list)
        except Exception:
            showTraceback("UploadManager.persistUploadTransactions() could not serialize the list")

    def restoreUploadTransactions(self):
        trace("UploadManager","restoreUploadTransactions()","ABOUT TO RESTORE!")
        filePath = UploadManager.UPLOADS_DAT_FILEPATH
        if not os.path.exists(filePath):
            trace("UploadManager","restoreUploadTransactions()","No file where to restore from. Nothing to restore.")
            return
        
        f = None
        try:
            f = open(filePath,'rb')
            persistence_list = simplejson.loads(f.read())
            f.close()
            os.unlink(filePath)
        except:
            showTraceback("UploadManager.restoreUploadTransactions() could not recover from uploads.dat")
            sys.exit(1)

        if persistence_list is None or len(persistence_list) == 0:
            trace("UploadManager","restoreUploadTransactions()","Nothing to restore.")
            return
        
        for transaction_dict in persistence_list:
            filePath = transaction_dict['filePath']
            
            #If the file to upload is not there anymore
            if not os.path.exists(filePath):
                print "File no longer exists:",filePath
                #try to remove any blooploadChunk leftovers
                if transaction_dict['hash'] is not None:
                    tokenFilePath = os.path.join('resume',self.getRemoteSession().getUsername(),transaction_dict['hash']+'.blooploadChunk')
                    if os.path.exists(tokenFilePath):
                        os.unlink(tokenFilePath)
                print "Skipping restoring",filePath
                continue

            dummyUploadTransaction = UploadTransaction(filePath,transaction_dict['remoteFolderId'],self)
            dummyUploadTransaction.setUploadPercentage(transaction_dict['uploadPercentage'], False)
            
            if transaction_dict['hash'] is not None:
                #pass the upload token it had the last time
                tokenFileName = transaction_dict['hash']+'.blooploadChunk'
                tokenFromFile = None
                
                try:
                    tokenFromFile = UploadToken.load(tokenFileName,self.getRemoteSession(),open(filePath,'rb'))
                    
                    if tokenFromFile is not None and tokenFromFile.shouldGo():
                        assert(tokenFromFile.getTokenId() is not None)
                        print "UploadManager.restoreUploadTransactions(): Restored Token does have a token id:", tokenFromFile.getTokenId()
                except Exception, e:
                    showTraceback("UploadManager.restoreUploadTransactions() - Problems fetching token from file - no token probably")
                
                if tokenFromFile is None:
                    #No token was saved, we tell it to recreate the token
                    print "UploadManager.restoreUploadTransactions() - No token from file, build it!"
                    #dummyUploadTransaction.initUploadToken() #we'll create token only when we are put in traffic. 
                    assert(dummyUploadTransaction is not None)
                else:
                    print "UploadManager.restoreUploadTransaction() - Got the token from file."
                    print "Check integrity from that token", tokenFromFile.checkIntegrity()
                    dummyUploadTransaction.setUploadToken(tokenFromFile)

            dummyUploadTransaction.setUploading(False) #not uploading yet whatever the case.
            dummyUploadTransaction.setResurrecting(True)
            
            bytesSent = transaction_dict['bytesSent']
            dummyUploadTransaction.setBytesSent(bytesSent)                
            
            if transaction_dict['status'] == UploadTransaction.STATUS_GO:
                transaction_dict['status'] = UploadTransaction.STATUS_QUEUED
                print "UploadManager.restoreUploadTransaction() - switched to QUEUED"
                #raw_input("Press enter\n")

            dummyUploadTransaction.setUploadStatus(transaction_dict['status'],False)
        
        #Kick start them
        self.attemptToStartUploadTransactionsTimer()

class UploadTransaction(GetterSetter):
    '''An upload transaction represents the status of a file being uploaded.
    Upload Transactions are no longer worker threads, since now files are uploaded
    An Upload manager manipulates UploadTransactions    '''
    STATUS_ERROR = 0
    STATUS_GO = 1
    STATUS_STOP = 3
    STATUS_ENDED = 4
    STATUS_QUEUED = 5
    STATUS_CANCELLED = 7
    
    HUMAN_STATUSES = {}

    _filePath = None
    _fileData = None
    _remoteFolderId = None
    _uploadManager = None
    _uploadPercentage = None
    _bytesSent = None
    _safeBytesSent = None
    _uploadStatus = None
    
    _resurrecting = False
    
    _sessionCopy = None #a RemoteSession copy so that I can upload on my own.
    _uploadToken = None #a reference to the current token being transfered, or about to be transfered
    _uploading = False #True while uploading
    _uploadProxy = None

    #TODO: From The RemoteSession uploadFile method, set a new property on the uploadTransaction
    #called, uploadingLastChunk = True | False. Its based on the nextOffset + chunkSize of the token
    #if the addition of these equals or is greater to the size of the file, it means the upload
    #cannot be stopped since its on its last chunk.
    
    def __init__(self,filePath,remoteFolderId,uploadManager):
        UploadTransaction.HUMAN_STATUSES = {UploadTransaction.STATUS_ERROR : 'Error',
                                            UploadTransaction.STATUS_GO:'Uploading',
                                            UploadTransaction.STATUS_ENDED:'Complete',
                                            UploadTransaction.STATUS_QUEUED:'Queued',
                                            UploadTransaction.STATUS_STOP:'Paused',
                                            UploadTransaction.STATUS_CANCELLED:'Cancelled'}
        GetterSetter.__init__(self)
        self.setFilePath(filePath)
        self.setRemoteFolderId(remoteFolderId)
        self.setUploadManager(uploadManager)
        #self.setUploadPercentage(0,False,False,False)
        self.setResurrecting(False)
        self.setUploading(False)
        self.prepareFileData(self.getFilePath())
        self.setSafeBytesSent(0)

    def setUploadStatus(self,status,persist=True): #add persistence flag here
        '''
        This function is the center of the universe when it comes to
        how uploads behave.
        
        Depending on their state, the object will interact with the
        UploadManager and tell it about what's happened.
        
        0: Error
        1: Go (Starts Uploading, uploadManager will attempt adding it to IN_TRANSIT)
        3: Stop        
        4: Transfer Ended
        5: Queued for Upload (when you just add this to the upload manager)
        6: Cancelling
        7: Cancelled
        '''
        lastState = self._uploadStatus
        self._uploadStatus=int(status)
        stateChanged = lastState != self._uploadStatus
        
        if status == UploadTransaction.STATUS_GO and self.isResurrecting():
            self.setResurrecting(False) #not anymore, we're resurrected now
            #print "UploadTransaction.setUploadStatus(STATUS_GO): Back from the dead."
            result = self.getUploadManager().addTransactionToTransit(self)
                        
            if result == UploadManager.TRANSACTION_ADDED_TO_IN_TRANSIT:
                #print "Much Success, Added to in transit"
                try:
                    self.setUploading(True)
                    self.startUpload()
                    self.getUploadManager().notifyUploadGoing(self,persist,True)
                except UploadEndedException,e:
                    #print "UploadTransaction.resumeUpload() sent an UploadEndedException"
                    self.setUploading(UploadTransaction.STATUS_ENDED)
                assert(self.isUploading())                
            else:
                #The queue is full at the moment when it comes to in transit
                #we'll have to queue it, sorry.
                self.setUploading(False) #just to make sure
                self.setUploadStatus(UploadTransaction.STATUS_QUEUED)
                self.getUploadManager().notifyUploadQueued(self,persist)
            return
        
        if int(status) == UploadTransaction.STATUS_GO:
            if not self.isUploading():
                result = self.getUploadManager().addTransactionToTransit(self)
                if result == UploadManager.TRANSACTION_ADDED_TO_IN_TRANSIT:
                    self.setUploading(True)
                    self.startUpload()
                elif stateChanged:
                    #print "UploadTransaction.setUploadStatus(GO): Sorry have to put you back to ->", lastState
                    self.setUploadStatus(lastState)
            return
                                
        if int(status) == UploadTransaction.STATUS_STOP:
            if self.isResurrecting() and not self.isUploading():
                self.setResurrecting(False)
                #this guys is coming back from the dead, let's put him as queued.
                #print "*** UploadTransaction.setUploadStatus(STATUS_STOP) [STOPPED COMING FROM THE DEAD] ",self
                self.setUploadStatus(UploadTransaction.STATUS_QUEUED, persist)
            elif self.isUploading():
                self.stopUpload(persist)
            return

        if int(status) == UploadTransaction.STATUS_ENDED:
            if self.isUploading():
                self.stopUpload(persist,notifyStopped=False)
            self._uploadStatus = UploadTransaction.STATUS_ENDED
            self.getUploadManager().notifyUploadFinished(self, persist)
            return

        if int(status) == UploadTransaction.STATUS_QUEUED:
            if self.isUploading():
                self.stopUpload(persist,notifyStopped=False)
            self._uploadStatus = UploadTransaction.STATUS_QUEUED
            self.getUploadManager().notifyUploadQueued(self, persist)
            return

        if int(status) == UploadTransaction.STATUS_ERROR:
            if self.isUploading():
                self.stopUpload(persist,notifyStopped=False)
            self._uploadStatus = UploadTransaction.STATUS_ERROR
            self.getUploadManager().notifyUploadErrored(self, persist)
            self.setUploading(False)
            return

        if int(status) == UploadTransaction.STATUS_CANCELLED:
            if self.isUploading():
                self.stopUpload(persist,notifyStopped=False)
            self._uploadStatus = UploadTransaction.STATUS_CANCELLED
            self.getUploadManager().notifyUploadCancelled(self, persist)
            self.setUploading(False)
            return

    def setUploadProxy(self,uploadProxy):         
        self._uploadProxy = uploadProxy
        
    def getUploadProxy(self):
        return self._uploadProxy

    def getFilePath(self):
        return self._filePath

    def setFilePath(self,path):
        self._filePath = path

    def prepareFileData(self,filePath):
        '''Returns a dictionary with relevant info for this file.
        Used on prepareUpload.

        fldFileName, fldFileDescription, fldFileSize, fldFilePrivate(0/1),
        fldFileMD5

        TODO: Put a real description.
        '''
        assert(os.path.exists(filePath))
        f = file(filePath,'rb')

        fileData = {}
        fileData['fldFileName'] = getFileName(f.name) #just the file name (from mbu_utils)
        fileData['fldFileDescription'] = 'Upload all your files to MyBloop.com with the Blooploader'
        f.seek(0,2)
        fileData['fldFileSize'] = f.tell()
        f.seek(0)
        fileData['fldFilePrivate'] = '0' #public by default
        digest = md5.new(f.read()).hexdigest()
        fileData['fldFileMD5'] = digest

        f.close()
        
        self.setFileData(fileData)

        return fileData
        
    def setFileData(self,fdata):
        '''
        Stores a dictionary with information relevant to the file
        fldFileName, fldFileDescription, fldFileSize, fldFilePrivate(0/1),
        fldFileMD5
        
        See prepareFileData(filePath)
        '''
        self._fileData = fdata
        
    def getFileData(self):
        return self._fileData
    
    def getFileSize(self):
        assert(self.getFileData() is not None)
        return self.getFileData()['fldFileSize']
    
    def getRemoteFolderId(self):
        return self._remoteFolderId
    
    def setRemoteFolderId(self, folderId):
        self._remoteFolderId = folderId

    def getUploadManager(self):
        return self._uploadManager
    
    def setUploadManager(self, uploadManager):
        self._uploadManager = uploadManager
    
    def getRemoteSession(self):
        return self.getUploadManager().getRemoteSession()

    def getSafeBytesSent(self):
        return self._safeBytesSent

    def setSafeBytesSent(self,bytes):
        '''
        Safe Bytes represent the number of bytes sent up to the last
        chunk. Any other bytes sent while the current chunk hasn't finished
        will be resent (as of now), since we could in the future, negotiate
        with the server, and ask, up to where did the server get,  
        '''
        self._safeBytesSent = bytes
        self.setBytesSent(bytes)
        self.tryUpdateUploadPercentage()

    def getBytesSent(self):
        return self._bytesSent
    
    def setBytesSent(self,bytes):
        self._bytesSent = long(bytes)
    
    def addBytesSent(self,bytes):
        if self._bytesSent is None:
            self._bytesSent = long(0)

        self._bytesSent += long(bytes)
        self.tryUpdateUploadPercentage()
    
    def tryUpdateUploadPercentage(self):
        #calculates percentage and asks for UI notification (signal)
        assert(self.getFileData() is not None)
        percentage = (self._bytesSent*100)/self.getFileSize()
        
        #update the percentage only if it actually changed
        if percentage != self.getUploadPercentage():
            self.setUploadPercentage(percentage, persist=True, emitSignal=True)
    
    def setUploadPercentage(self, percentage, persist=True, emitSignal=True):
        '''
        Receives a percentage (from RemoteSession.uploadFile usually)
        and tells its upload manager to notify whoever is listening about
        the current status of this transaction.
        
        Parameters:
          percentage - int [0,100]
          persist - bool, whether or not to save the state of this transaction for future restoring
          putInTransit - bool, if true, when it notifies the UploadManager the upload manager
                         will know that this method was invoked cause the transaction is in transit.
                         pass this False and the transaction will be updated and it will stay
                         on the UPLOAD_TRANSACTION queue (waiting for its turn)
        '''
        self._uploadPercentage=percentage
        self.getUploadManager().notifyUploadPercentageChanged(self, persist, emitSignal)

    
    def getUploadPercentage(self):
        if self._uploadPercentage is None:
            self._uploadPercentage = 0
        return int(self._uploadPercentage)

    def getUploadStatus(self):
        if self._uploadStatus is not None:
            return int(self._uploadStatus)

        print "UploadTransaction @ ",hex(id(self))
        print "OH OH\n"*3
        print "getUploadStatus() Defaulting to Queued????"
        self._uploadStatus = UploadTransaction.STATUS_QUEUED

        return self._uploadStatus
    
    def getHumanUploadStatus(self):
        return UploadTransaction.HUMAN_STATUSES[self.getUploadStatus()]

    def cancelUpload(self, persist, notifyCancelled=True):
        self.stopUpload(False,False) #but don't notify or persist this state, since we're gonna cancel
        self.setUploadStatus(UploadTransaction.STATUS_CANCELLED,persist)
        
        if self.getUploadToken() is not None:
            self.getUploadToken().clear()
            
        if notifyCancelled:
            self.getUploadManager().notifyUploadCancelled(self, persist)
        else:
            self.getUploadManager().persistUploadTransactions()

        #Make sure its not on the wrong queues.
        self.getUploadManager().removeTransactionFromUploadTransactions(self)
        self.getUploadManager().removeTransactionFromTransit(self)
        self.getUploadManager().addTransactionToFinished(self)
    
    def stopUpload(self,persist,notifyStopped=True):
        if self.getUploadStatus() != UploadTransaction.STATUS_STOP:
            #in case we're not being stopped from setUploadStatus, we make sure our status is correct
            self._uploadStatus = UploadTransaction.STATUS_STOP

        self.setUploading(False)
        
        #Fix count of bytes sent, discard the last bytes of the next chunk
        #will have to revert to your last chunk.
        
        if notifyStopped:
            self.getUploadManager().notifyUploadStopped(self, persist) #will make sure it goes to UPLOAD_TRANSACTIONS
        else:
            #at least make sure it's taken out of IN_TRANSIT ANT PUT BACK INTO QUEUED.
            self.getUploadManager().removeTransactionFromTransit(self)
            self.getUploadManager().addTransactionToUploadTransactions(self)


        if self.getUploadProxy() is not None:
            self.getUploadProxy().stopUpload(notifyUploadTransaction=False) #we're already here

    def startUpload(self):
        if self.getUploadStatus() != UploadTransaction.STATUS_GO:
            self._uploadStatus = UploadTransaction.STATUS_GO 

        try:
            self.bootstrapQHttpUploadProxy()
            self.setUploading(True)
            self.getUploadProxy().startUpload()
            self.getUploadManager().persistUploadTransactions()
        except UploadEndedException, e:
            showTraceback("UploadTransaction.startUpload - Detected upload UploadEndedException")
            self.setUploadStatus(UploadTransaction.STATUS_ENDED)
        except UploadStoppedException, e:
            showTraceback("UploadTransaction.startUpload - Detected upload UploadStoppedException")
            self.setUploading(False)
            self.setUploadStatus(UploadTransaction.STATUS_STOP)
            return
        except UploadCancelledException:
            showTraceback("UploadTransaction.startUpload - Detected upload UploadCancelledException")
            self.setUploading(False)
            self.setUploadStatus(UploadTransaction.STATUS_CANCELLED)
            return
        except Exception:
            trace("UploadTransaction","startUpload","Problem with RemoteSession.uploadFile, sending to Failed")
            self.setUploading(False)
            showTraceback("UploadTransaction.startUpload - on Exception.")
            self.setUploadStatus(UploadTransaction.STATUS_ERROR)
            return

    def initUploadToken(self):
        '''
        When a file is dropped it should probably have a basic upload token with what it knows.
        This  will basically talk to the server to get the first token needed for this transaction
        and it will save it to disk on the correspondent resume folder.
        
        For convenience it returns the created token.
        '''
        assert(self.getFilePath() is not None)
        assert(self.getRemoteFolderId() is not None)
        
        if self.getFileData() is None:
            self.prepareFileData(self.getFilePath())
        
        rs = self.getRemoteSession()
        try:
            blooploadChunkFilename = self.getFileData()['fldFileMD5'] + '.blooploadChunk'
            virginToken = rs.prepareUploadToken(blooploadChunkFilename, 
                                                self.getFilePath(), 
                                                self.getRemoteFolderId(),
                                                self.getFileData())
            
            assert(virginToken.getRemoteSession() is not None)
            self.setUploadToken(virginToken)
            virginToken.save()
        except:
            showTraceback("problems with initUploadToken - probably restoring token that didn't get initialized")
            return None
        return self.getUploadToken()

    def bootstrapQHttpUploadProxy(self):
        '''
        This method attempts to recreate this UploadTransaction from a file.
        Otherwise, it will invoke self.initUploadToken() which will make a request
        for a virgin token from the server. 
        '''
        #this newUploadToken, may be brand new or it could be de-serialized by prepareUploadToken
        assert(self.getFilePath() is not None)
        
        fdata = self.getFileData()
        if fdata is None:
            fdata = self.prepareFileData(self.getFilePath())
        
        blooploadChunkFilename = fdata['fldFileMD5'] + '.blooploadChunk'

        newUploadToken = self.getUploadToken()
        if newUploadToken is None:
            try:
                newUploadToken = self.initUploadToken()
            except Exception, e:
                trace('UploadTransaction','bootstrapQHttpUploadProxy',"Problems creating uploadToken, not uploading this one")
                trace('UploadTransaction','bootstrapQHttpUploadProxy','exception')
                print e
                if newUploadToken is None:
                    return False
        else:
            trace('UploadTransaction','bootstrapQHttpUploadProxy','It recovered from a token saved on a past session')

        self.setUploadToken(newUploadToken)

        if newUploadToken.shouldEnd():
            trace('UploadTransaction','bootstrapQHttpUploadProxy','We have an instant upload!')
            self.setUploadPercentage(100)
            self.setUploadStatus(newUploadToken.getStatus())
            self.setUploadProxy(None)
            raise UploadEndedException(self)

        if newUploadToken.shouldGo():
            trace('UploadTransaction','bootstrapQHttpUploadProxy','UploadToken says we should go, creating new Upload Proxy')
            self.setUploadProxy(None)
            self.setUploadProxy(QHttpUploadProxy(self.getRemoteSession(), newUploadToken, self))

    def getUploadToken(self):
        return self._uploadToken
    
    def setUploadToken(self, uploadToken):
        #assert(uploadToken.checkIntegrity())
        self._uploadToken = uploadToken
    
    def isUploading(self):
        return self._uploading
    
    def setUploading(self, status):
        self._uploading = status
        
    def isResurrecting(self):
        return self._resurrecting

    def setResurrecting(self,status):
        self._resurrecting = status
    def __str__(self):
        return "UploadTransaction: "+self.getFilePath()+" @ "+hex(id(self))+ " " +"Status: " + self.getHumanUploadStatus() + " isUploading:" + str(self.isUploading()) + " isResurrecting:" + str(self.isResurrecting())