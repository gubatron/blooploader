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

module models.upload_token
'''
from getter_setter import GetterSetter
import os
import simplejson
import md5
from utils import trace,showTraceback

class UploadTokenException(Exception):
    def __init__(self,value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class UploadToken(GetterSetter):
    '''Class to represent an upload Token.
    An upload token is the piece of data sent to the
    server everytime we try to upload a file chunk.

    An upload token will have:
    { serverParams,{'server':x.x.x.x, 'port':dd, 'api' : 'x.y'}
      tokenId,
      status, //'0':ERROR  '1':GO, '2':STOP, '3':TRANSFER ENDED, 
      errorCode,
      errorMessage,
      filePath, //local 
      size, //total size of file in bytes 
      description, //desc, set automagically (preferably sent null over wire, set by server to sa
      destinationDirId, 
      nextOffset, //client uploaded fine before, this will be the next offset to send
      chunkSize, //the size in bytes the server is expecting
      lastTimestamp, //the last time this guy did a sucessful chunk upload of this file
      checksumAlgo, //md5,sha1,false
      checksumHash, //set if checksumAlgo != false, and the token is sent back on upload
     }


    IMPORTANT:
    IF THE SERVER NEEDS TO SEND SOMETHING NULL, IT WILL JUST PUT A 0
    on the field.

    We need all the keys set to know this is a well formed UploadToken.
    '''
    remoteSession = None
    fileObject = None #reference to the (complete) file being uploaded by the upload transaction

    def __init__(self,uploadTokenDict,blooploadChunkFilename, remoteSession, fileObject):
        GetterSetter.__init__(self)

        if remoteSession is not None:
            self.setRemoteSession(remoteSession)

        if blooploadChunkFilename is not None:
            self.setBlooploadChunkFilename(blooploadChunkFilename)
        
        if fileObject is not None:
            self.setFileObject(fileObject)
        
        if uploadTokenDict == None and blooploadChunkFilename == None:
            '''They want to use an empty object'''
            trace("UploadToken","__init__","Using empty constructor")
            return

        if uploadTokenDict is None:
            trace("UploadToken","__init__","UploadToken Constructor: Missing token dict.")
            raise UploadTokenException("UploadToken Constructor: Missing token dict.")
        
        for x in uploadTokenDict:
            #trace('UploadToken','__init__', x + ':' + str(uploadTokenDict[x]))
            self._set(x,uploadTokenDict[x])

        #End transfer.
        #trace('UploadToken','__init__', "The Upload Token->")
        #trace('UploadToken','__init__', uploadTokenDict)
        
        if uploadTokenDict['status'] == '1' :
            try:
                self._checkIncomingKeys()
            except UploadTokenException, e:
                raise e
        
        if self.getChunkSize() is None:
            return
        
        #Set chunksize and checksum hash if you can.

        fileObject.seek(0,2)
        fileSize = fileObject.tell()

        #now we check that the chunkSize is not bigger than the file size
        if self.getChunkSize() > fileSize:
            self.setChunkSize(fileSize)

        fileObject.seek(0,0)
        fileObject.seek(self.getNextOffset())
        chunkData = fileObject.read(self.getChunkSize()) #we are not responsible of closing this file, its done outside
        self.setChunkChecksumHash(md5.new(chunkData).hexdigest())

    def checkIntegrity(self):
        '''Makes sure all the properties of this token are good.
        You should enclose this method on a try/except block.'''
        self._checkIncomingKeys()
        self._checkOutgoingKeys()
        #won't get here if these two methods will raise exceptions
        return True

    def _checkOutgoingKeys(self):
        '''Checks that the outgoing token has all the required keys'''
        
        self.outgoing_keys = ['tokenId','nextOffset','chunkChecksumHash']

        for k in self.outgoing_keys:
            #print "Checking that it has the key " + k
            if self.properties.has_key(k)==False:
                #print "It didnt have the key " + k
                raise UploadTokenException,('UploadToken._checkOutgoingKeys(): Missing key in Token: '+k)
                return False
                
        return True

    def _checkIncomingKeys(self):
        '''Checks that the incoming token has all the required keys'''
        self.incoming_keys = ['serverParams',
                              'tokenId','status','errorCode',
                              'errorMessage','nextOffset','chunkSize',
                              'lastTimestamp','checksumAlgo']
        
        #Transfer Ended
        if self.properties['status']=='3':
            return True
            

        for k in self.incoming_keys:
            #print "Checking that it has the key " + k
            if self.properties.has_key(k)==False:
                #print "It didnt have the key " + k
                raise UploadTokenException('UploadToken._checkIncomingKeys(): Missing key in Token: '+k)
                return False
            
        #check serverParams
        if not self.properties.has_key('serverParams'):
            raise UploadTokenException('UploadToken._checkIncomingKeys(): Missing serverParams')
         
        serverParamKeys = ('server','port','script') #'api' not anymore? gotta ask Fitim.
        for k in serverParamKeys:
            if not self.properties['serverParams'].has_key(k):
                raise UploadTokenException('UploadToken._checkIncomingKeys(): Missing key in serverParams: '+k)
        
        return True

    def getServer(self):
        '''Returns the server name'''
        if self._get('serverParams') is None:
            return None
        
        return self._get('serverParams')['server']

    def getPort(self):
        '''Returns the server port'''
        if self._get('serverParams') is None:
            return None
        
        return self._get('serverParams')['port']

    def getScript(self):
        '''Returns the server Script path'''
        if self._get('serverParams') is None:
            return None

        return self._get('serverParams')['script']

    def getProxyUrl(self):
        if self.properties.has_key('server_url') == False:
            self._set('server_url',"http://%s:%s%s" % (
                self.getServer(),
                self.getPort(),
                self.getScript()))

        '''Returns the server url where to make the jsonrpc calls'''
        return self._get('server_url')

    def getTokenId(self):
        return self._get('tokenId')

    def getStatus(self):
        '''Status can be:
        0: Error
        1:  Go
        2:  Stop        
        3:  Transfer Ended

        Depending on the status I can either continue transfering or
        stop, wheter to save my token, or cause Im done with the transfer.
        '''
        return self._get('status')

    def shouldHandleError(self):
        return self.getStatus() == '0'

    def shouldGo(self):
        return self.getStatus() == '1'

    def shouldStop(self):
        '''True if server asked to stop and save for later resume'''
        return self.getStatus() == '2'

    def shouldEnd(self):
        '''True if transfer is finally completed'''
        return self.getStatus() == '3'

    def getErrorCode(self):
        return self._get('errorCode')

    def getErrorMessage(self):
        return self._get('errorMessage')

    def getNextOffset(self):
        if self._get('nextOffset') is None:
            return None
        
        return int(self._get('nextOffset'))
    
    def getChunkSize(self):
        '''Returns the size in bytes of the chunk that will be sent'''
        if self._get('chunkSize') is None:
            return None
        
        return int(self._get('chunkSize'))
    
    def setChunkSize(self, size):
        self._set('chunkSize',int(size))

    def getLastTimestamp(self):
        '''Useful for timeouts'''
        return self._get('lastTimestamp')

    def getChecksumAlgorithm(self):
        return self._get('checksumAlgo')

    def setChunkChecksumHash(self,hash):
        self._set('chunkChecksumHash',hash)

    def getChunkChecksumHash(self):
        '''The checksum hash of the current chunk'''
        return self._get('chunkChecksumHash')

    def getBlooploadChunkFilepath(self):
        result = self._get('blooploadChunkFilepath')
        
        if result is None:
            result = os.path.join('resume',self.getRemoteSession().getUsername(),self.getBlooploadChunkFilename())
            self._set('blooploadChunkFilepath',result)

        return os.path.abspath(result)
        
    def getBlooploadChunkFilename(self):
        return self._get('blooploadChunkFilename')
    
    def setBlooploadChunkFilename(self,fname):
        self._set('blooploadChunkFilename',fname)
        
    def setRemoteSession(self, rs):
        self.remoteSession = rs
        
    def getRemoteSession(self):
        return self.remoteSession
    
    def setFileObject(self,fileObject):
        self.fileObject = fileObject
        
    def getFileObject(self):
        return self.fileObject

    @staticmethod
    def load(blooploadChunkFilename,remoteSession,fileObject):
        '''Loads the uploadToken from its [resume/<lastChunkMd5>.blooploadChunk] file
        
        Returns The Deserialized UploadToken Object or None if not there.
        '''
        assert(remoteSession is not None)
        assert(fileObject is not None)
        assert(not fileObject.closed)
        
        fpath = os.path.join('resume',remoteSession.getUsername(),blooploadChunkFilename)
                
        if os.path.exists(fpath):
            f = open(fpath)
            tempProps = simplejson.loads(f.read())
            f.close()
            uploadToken = UploadToken(tempProps,blooploadChunkFilename,remoteSession,fileObject)
            
            if not uploadToken._checkOutgoingKeys():
                raise Exception("UploadToken.load() deserialized token missing outgoing keys")
            
            if not uploadToken._checkIncomingKeys():
                raise Exception("UploadToken.load() deserialized token missing incoming keys")
            
            return uploadToken
        else:
            #trace("UploadToken","load","FILE PATH NOT FOUND - " + fpath)
            pass
        return None

    def save(self):
        '''Saves this UploadToken properties for further use'''
        if self.getRemoteSession() is None:
            raise Exception("Can't save upload token if there's no session associated to it")
        
        #create resume folder if it doesn't exist
        if not os.path.exists('resume'):
            os.mkdir('resume')

        if not os.path.exists(os.path.join('resume',self.getRemoteSession().getUsername())):
            os.mkdir(os.path.join('resume',self.getRemoteSession().getUsername()))
        
        fpath = self.getBlooploadChunkFilepath()
        
        if os.path.exists(fpath):
            self.clear()
        
        f = open(fpath,'w')
        f.write(simplejson.dumps(self.properties))
        f.close()
        #trace("UploadToken", "save", "Chunk saved " + fpath)
        return True

    def clear(self):
        '''Deletes the file from disk that represented this token'''
        fpath = self.getBlooploadChunkFilepath()
        if os.path.exists(fpath):
            #trace('UploadToken','clear','Removing'  + fpath)
            os.unlink(fpath)
            return True
        else:
            #trace('UploadToken','clear','Did not find ' + fpath)
            return False