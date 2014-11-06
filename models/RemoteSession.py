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

module models.RemoteSession
'''
import sys
import os
from mbu_config import meta
from getter_setter import GetterSetter
from jsonrpc import ServiceProxy
from user_profile import UserProfile
from upload_token import UploadToken, UploadTokenException
from qhttp_upload_proxy import QHttpUploadProxy
from utils import trace, getFileName
from utils.GenericWorker import GenericWorker
from PyQt4.QtCore import QMutex,QObject,SIGNAL

imported_UploadTransaction = False
#TODO: Implement support for disabling API and client handling it..
#e.g. we might need to take down DB and set API_DISABLED = 1 flag on server
# and the client should know this and go to the login view.


class RemoteSession(GetterSetter,QObject):
    '''This is the main high level object of the core of the Uploader.
    You need to create a remote session and use its methods in order
    to communicate and upload file to the Bloop servers'''

    def __init__(self):
        self.remote_url = "http://%s:%s/api/%s/index.o" % (
            meta['SERVER'],
            meta['PORT'],
            meta['API'])

        self.server = ServiceProxy(self.remote_url)
        
        QObject.__init__(self)
        GetterSetter.__init__(self)
        
    def onStateChanged(self, state):
        print "RemoteSession.onStateChanged()! state:",state
    
    def _readRemoteResponse(self,result):
        '''Used in every request, this parses the
        returned array and fills in several variables'''
        if result.has_key(u'result'):

            if result.has_key(u'status'):
                self.status = result[u'status']

            if result.has_key(u'api_name'):
                self.api_name = result[u'api_name']

            if result.has_key(u'api_version'):
                self.api_version = result[u'api_version']

            if result.has_key(u'time'):
                self.time = result[u'time']

            if result.has_key(u'result'):
                result = result[u'result']

        return result

    def setSessionId(self,sessionId):
        '''Sets the session Id.(Set to None when
        the session is destroyed)'''
        self._set('session_id',sessionId)

    def getSessionId(self):
        '''Gets the current session Id.'''
        return self._get('session_id')

    def setUsername(self,username):
        self._set('username',username)

    def setPassword(self,password):
        self._set('password',password)

    def getUsername(self):
        return self._get('username')
    
    def getCallStatus(self):
        return self.status

    def _getPassword(self):
        return self._get('password')
    
    def invalidate(self):
        '''Gets rid of all the data about this object, basically reset it, make it invalid'''
        self.setUsername(None)
        self.setPassword(None)
        self.setSessionId(None)
        self.setUserProfile(None)

    def create(self,username,password):
        '''
        Request for session creation.
        
        This is the handshake with the
        server.
        
        We should come out of this with a session ID.
        '''
        result = None
        r = None
        try:
            r = self.server.create(username,password,meta)
            result = self._readRemoteResponse(r)
        except Exception,e:
            self.invalidate()
            raise e

        if self.status != u'1':
            self.invalidate()
            raise Exception(result)
        
        self.setUsername(username)
        self.setPassword(password)

        assert(result.has_key(u'sessionId'))

        self.setSessionId(result[u"sessionId"])

        return result

    def destroy(self):
        result = None
        try:
            result = self._readRemoteResponse(
                self.server.destroy(self.getSessionId(),
                                    self.getUsername(),
                                    self._getPassword()))
        except Exception,e:
            raise e

        if self.status != '1':
            raise Exception(result,self.status)

        self.setSessionId(None)
        return True


    def setUserProfile(self,remoteData):
        if remoteData is None:
            self._set('user_profile',None)
        else:
            self._set('user_profile',UserProfile(remoteData))

    def getUserProfile(self):
        return self._get('user_profile')

    def getRemoteUserProfile(self):
        '''Gets the User Profile from the remote
        server and sets the local instance'''
        result = None
        try:
            result = self._readRemoteResponse(self.server.getUserProfile(self.getSessionId()))
        except Exception,e:
            raise e
        
        if self.status != '1':
            raise Exception(result,self.status)

        #will create an UserProfile object
        self.setUserProfile(result)

        return self.getUserProfile()

    def getUserFiles(self,folderId):
        assert(folderId is not None)
        if type(folderId) != int:
            folderId = int(folderId)
        
        result = None
        try:
            result = self._readRemoteResponse(
                self.server.getUserFiles(
                    self.getSessionId(),
                    folderId))
        except Exception,e:
            trace('RemoteSession','getUserFiles() exception',e)
            import traceback
            traceback.print_exc(10,file=sys.stdout)
            raise e

        if self.status != '1':
            raise Exception(result,self.status)

        return result

    def prepareUploadToken(self,blooploadChunkFilename, filePath, dirId, fileData):
        '''
        This will return an UploadToken object to either start or resume
        a previous transfer.
        
        This will send the server the file info, and it will
        obtain a hash with the info needed to construct an
        UploadToken object, this will return a UploadToken object.
        
        @param blooploadFilename - Filename where we might have serialized an UploadToken
                                   object for a previous attempt to bloopload this file.
                                   This filename consists of the md5 of the file and the
                                   extension ',blooploadChunk'
                                   
        @param filePath - Full file path.

        @param dirId - The ID of the remote dir where this file will be uploaded to.
        
        @param fileData - A Dictionary with the file data (see UploadTransaction.prepareFileData())
        
        @return UploadToken Object

        The remote function takes as a second parameter a fileData
        dictionary that should contain a dictionary with the following keys:

        fldFileName, fldFileDescription, fldFileSize, fldFilePrivate(0/1),
        fldFileMD5
        '''
        #Try first to load the UploadToken
        assert(blooploadChunkFilename is not None)
        assert(filePath is not None)
        assert(dirId is not None)
        assert(fileData is not None)
        
        uploadToken = None
        
        try:
            uploadToken = UploadToken.load(blooploadChunkFilename, self, open(filePath,'rb'))
        except UploadTokenException,e:
            print "Received a token but the token doesn't have a tokenId, never talked to server"
            uploadToken = None #will set it as none and create it from server since now its the correct time
        #No need to call the server to get the first chunk
        if uploadToken is not None:
            #trace("RemoteSession","prepareUploadToken","RESUMING PREVIOUS TRANSFER FROM LOADED FILE - " + blooploadChunkFilename)
            return uploadToken
        else:
            #trace("RemoteSession","prepareUploadToken","ASKING FOR NEW CHUNK")
            pass
        
        result = None
        
        try:
            #trace("RemoteSession","prepareUploadToken","Before server.prepareUpload")
            #print "sessionId",self.getSessionId()
            #print "dirId", dirId
            #print "fileData", fileData
            
            #Each upload request will use its own JSONRPC proxy, since the proxy is not Threadsafe.
            prepareUploadServiceProxy = ServiceProxy(self.remote_url)
            result = prepareUploadServiceProxy.prepareUpload(self.getSessionId(),fileData,dirId)

            #trace("RemoteSession","prepareUploadToken result->",result)
            
            result = self._readRemoteResponse(result)
        except Exception,e:
            print "RemoteSession.prepareUploadToken() -> Exception, we got this as a result so far\nResult:\n",result,"\nException Object:\n",e,"\n","*"*40
            raise e

        if self.status != '1':
            raise Exception(result,self.status)

        #With the result we build an UploadToken Object.
        uploadToken = None

        try:
            #print "result",result
            #print "blooploadChunkFilename",blooploadChunkFilename
            uploadToken = UploadToken(result,blooploadChunkFilename,self,open(filePath,'rb'))
        except UploadTokenException, e:
            print "RemoteSession.prepareUpload() -> Problems creating the UploadToken",e
            print result
            raise e

        return uploadToken
        

    def createFolder(self, folderName, parentFolderId, private):
        '''Should return the ID of the newly created folder'''
        result = None
        #trace("RemoteSession","createFolder","About to create folder with parameters:")
        #trace("RemoteSession","createFolder","folderName: " + folderName)
        #trace("RemoteSession","createFolder","parentFolderId: " + str(parentFolderId))
        #trace("RemoteSession","createFolder","private: " + str(private))
        
        if private == True:
            private = 1
        elif private == False:
            private = 0

        try:
            result = self._readRemoteResponse(
                self.server.createFolder(self.getSessionId(),
                                         folderName,
                                         parentFolderId,
                                         private))
        except UploadTokenException,e:
            raise e

        return result

    def deleteItem(self, itemList):
        result = None
        
        #trace("RemoteSession","deleteItem","About to make deleteItem() call")
        result = self._readRemoteResponse(self.server.deleteItem(self.getSessionId(), itemList))
        #trace("RemoteSession","deleteItem","Finished call: Result: " + result)
        #trace("RemoteSession","deleteItem","Finished call: Status: " + self.status)
    
        if self.status == '0':
            return False
        
        return True
    
    def renameItem(self, itemType, itemId, newName):
        result = None
        
        #trace("RemoteSession","renameItem","About to make renameItem() call")
        result = self._readRemoteResponse(self.server.renameItem(self.getSessionId(), itemType, itemId, newName))
        #trace("RemoteSession","renameItem","Finished call: Result: ")
        #trace("RemoteSession","renameItem",result)        
        #trace("RemoteSession","renameItem","Finished call: Status: " + self.status)
    
        # Add the result to the response array
        if self.status == '1':
            result['status'] = self.status
            return result        
        else:
            response = {}
            response['status'] = self.status
            response['response'] = result
            return response
            
        
    def getFriendsList(self):
        result = None
        
        #trace("RemoteSession","getFriendsList","About to make getFriendsList() call")
        result = self._readRemoteResponse(self.server.getFriendsList(self.getSessionId()))        
        #trace("RemoteSession","getFriendsList","Finished call: Result: " + result)
        #trace("RemoteSession","getFriendsList","Finished call: Status: " + self.status)
        return result
    
    def setItemVisibility(self, items, mode = 'public'):
        # Prevent any accidental typos
        mode = mode.lower()
        if mode != 'public':
            mode = 'private'

        #trace("RemoteSession","setItemVisibility","About to make setItemVisibility() call with mode: " + mode)
        result = self._readRemoteResponse(self.server.setItemVisibility(self.getSessionId(), items, mode))        
    
        #trace("RemoteSession","setItemVisibility","Finished call: Status: " + self.status)
        #trace("RemoteSession","setItemVisibility",result)
        return result
        

    def dummyUpload(self):
        '''Proof of concept method to upload a file to mybloop'''
        from base64 import b64encode
        '''will upload a dummy file'''
        fp = open('01.mp3')
        fp.seek(0,2)

        fileSize = fp.tell()

        fp.seek(0)

        chunkNum = 0
        chunkSize = 131072
        offset = 0


        while fp.tell() < fileSize:

            fp.seek(offset)
            chunkData = fp.read(chunkSize)
            
            trace("RemoteSession","dummyUpload","Sending chunk")
            self.server.dummyUpload(chunkNum,
                                    chunkSize,
                                    b64encode(chunkData))

            offset += chunkSize
            trace("RemoteSession","dummyUpload","Uploaded " + str(offset))

        fp.close()
        
    def moveFiles(self, items, targetId, progressCallback):
        token = self.server.prepareMove(items, targetId)
        
        from threading import Thread
        class FileMove(threading.Thread):
            def __init__(self, server, token, targetId, callBack):
                self._callback_ = callBack
                self._token_ = token
                self._targetId_ = targetId
                self._server_ = server
            
            def run(self):
                #Thread keeps talking to the server and sending current status
                #to callback
                pass