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

module models.qhttp_upload_proxy
'''
from PyQt4.QtCore import SIGNAL,QByteArray,QObject,QString,QBuffer
from PyQt4.QtNetwork import QHttp,QHttpRequestHeader
import sys
import os
sys.path.append(sys.path[0][:sys.path[0].rfind(os.path.sep)]+os.path.sep+'lib')
sys.path.append(sys.path[0][:sys.path[0].rfind(os.path.sep)]+os.path.sep+'lib'+os.path.sep+'simplejson')
import utils
import simplejson
import md5
from models.upload_token import UploadToken, UploadTokenException

class QHttpUploadProxy (QObject):
    SIGNAL_DATA_READ_PROGRESS = SIGNAL("dataReadProgress(int, int)")
    SIGNAL_DATA_SEND_PROGRESS = SIGNAL("dataSendProgress(int, int)")
    SIGNAL_DATA_DONE = SIGNAL("done(bool)")
    SIGNAL_REQUEST_STARTED = SIGNAL("requestStarted (int)")
    SIGNAL_STATE_CHANGED = SIGNAL("stateChanged(int)")
    SIGNAL_READY_READ = SIGNAL("readyRead(QHttpResponseHeader)")
    SIGNAL_REQUEST_FINISHED = SIGNAL("requestFinished(int, bool)")
    
    SIGNAL_NEW_UPLOAD_TOKEN = SIGNAL("newUploadToken(PyQt_PyObject,PyQt_PyObject,PyQt_PyObject)") #newUploadToken, uploadProxy, fileObj
    
    http = None #QHttp
    byteArray = None #QByteArray
    toQIODevice = None #QIOArray
    
    tookOverheadOut = False
    lastBytesDone = 0
    overheadBytes = 0
    
    fileObj = None
    remoteSession = None
    uploadToken = None
    uploadTransaction = None #Every upload transaction should use a different proxy
                             #This way we avoid conflicts in HTTP and we can support
                             #concurrent uploads
                             
    def __init__(self, remoteSession, uploadToken, uploadTransaction):
        '''
        Initialize and connect signals to local methods that will
        invoke the remoteSession methods on QHttp events.
        
        The idea is to let remoteSession know about the progress
        of the upload, and to let it know when its done, by giving
        it a new uploadToken.
        
        remoteSession should keep track of how many bytes it's sent
        for the transaction.
        
        We shall not use the uploadTransaction inside this class, we don't want
        to trigger any signals except ours from here. However
        we keep a reference to uploadTransaction so that
        when we have a QHttp signal, we can tell remoteSession
        which uploadTransaction this upload relates to.
        
        It's up to remoteSession to do whatever it needs to do with the
        uploadTransaction, thus connecting with the controllers.
        We'll stick here strictly to the HTTP layer.

        Parameters:
         remoteSession : RemoteSession Object
         uploadToken : UploadToken Object
         uploadTransaction : UploadTransaction Object
        '''
        try:
            assert(remoteSession is not None)
            assert(uploadToken is not None)
            assert(uploadTransaction is not None)
        except:
            utils.trace("QHttpUploadProxy","__init__","remoteSession:" + str(remoteSession))
            utils.trace("QHttpUploadProxy","__init__","uploadToken:" + str(uploadToken))
            utils.trace("QHttpUploadProxy","__init__","uploadTransaction:" + str(uploadTransaction))
            raise Exception("Cannot instanciate QHttpUploadProxy, all parameters are mandatory")
            
        QObject.__init__(self)
        self.setRemoteSession(remoteSession)
        self.setUploadToken(uploadToken)
        self.setUploadTransaction(uploadTransaction)
        
        self.http = None
        
    def __str__(self):
        debugState={0:"Unconnected",1:"HostLookup",
                    2:"Connecting",3:"Sending",
                    4:"Reading",5:"Connected",
                    6:"Closing"}
        
        result = "<QHttpUploadProxy@" + str(hex(id(self))) + ">:\n"
        
        if self.getQHttp() is not None:
            result = result + "\tQHttp state -> " + debugState[self.getQHttp().state()] + " - lastBytesDone: " + str(self.lastBytesDone) + " - hasPendingRequests: " + str(self.getQHttp().hasPendingRequests()) +"\n"
        
        if self.getUploadTransaction() is not None:
            result = result + "\t" + str(self.getUploadTransaction())
        
        
        
        return result
             
        
    def setFileObject(self, fileObj):
        if self.getFileObject() is not None:
            #close and get rid of the reference to the previous file if its changed for some reason
            f = self.getFileObject()
            f.close()
            del(f)
            print "QHttpUploadProxy.setFileObject() got rid of old file object."

        self.fileObj = fileObj
        assert(self.fileObj.closed==False)
        
    def getFileObject(self):
        return self.fileObj

    def getRemoteSession(self):
        return self.remoteSession
    
    def setRemoteSession(self,remoteSession):
        self.remoteSession = remoteSession

    def getUploadTransaction(self):
        return self.uploadTransaction
    
    def setUploadTransaction(self, uploadTransaction):
        self.uploadTransaction = uploadTransaction

    def getHost(self):
        return self.host
    
    def setHost(self,host):
        self.host = host
    
    def getPort(self):
        return self.port

    def setPort(self, port):
        self.port = port
    
    def getScript(self):
        return self.script
    
    def setScript(self, script):
        self.script = script

    def getUploadToken(self):
        return self.uploadToken
    
    def setUploadToken(self, uploadToken):
        self.uploadToken = uploadToken

        if self.uploadToken is not None:
            #assert(uploadToken.getScript() is not None)
            #assert(uploadToken.getServer() is not None)
            #assert(uploadToken.getPort() is not None)
            self.setScript(uploadToken.getScript())
            self.setHost(uploadToken.getServer())
            self.setPort(uploadToken.getPort())
    
    def encode_multipart_formdata(self,fields, files):
        """
        fields is a sequence of (name, value) elements for regular form fields.
        files is a sequence of (name, filename, value) elements for data to be uploaded as files
        Return (content_type, body) ready for httplib.HTTP instance
        """
        BOUNDARY = '---------BLOOPLOADER_BOUNDARY_$'
        CRLF = '\r\n'
        L = []
        
        for (key, value) in fields:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"' % key)
            L.append('')
            L.append(str(value))
            
        for (key, filename, value) in files:
            L.append('--' + BOUNDARY)
            L.append('Content-Disposition: form-data; name="%s"; filename="%s"' % (key, filename))
            L.append('Content-Type: application/octet-stream')
            L.append('')
            L.append(str(value))
    
        L.append('--' + BOUNDARY + '--')
        L.append('')

        body = CRLF.join(L)
        content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
        return content_type, body
    
    def initQHttp(self):
        utils.trace("QHttpUploadProxy","initQHttp","invoked")
        #in case we're about to get rid of an old http, we disconnect it first
        if self.getQHttp() is not None:
            try:
                self.disconnectQHttpSignals()
            except:
                utils.trace("QHttpUploadProxy","initQHttp","could not disconnect signals of old QHttp")

        self.http = QHttp(self.getHost(),self.getPort(),self)
        self.connectQHttpSignals()
        
    def getQHttp(self):
        return self.http

    def connectQHttpSignals(self):
        assert(self.getQHttp() is not None)
        QObject.connect(self.getQHttp(),QHttpUploadProxy.SIGNAL_DATA_READ_PROGRESS,self.onDataReadProgress)
        QObject.connect(self.getQHttp(),QHttpUploadProxy.SIGNAL_DATA_SEND_PROGRESS,self.onDataSendProgress)
        QObject.connect(self.getQHttp(),QHttpUploadProxy.SIGNAL_DATA_DONE, self.onDataDone)
        QObject.connect(self.getQHttp(),QHttpUploadProxy.SIGNAL_REQUEST_STARTED, self.onRequestStarted)
        QObject.connect(self.getQHttp(),QHttpUploadProxy.SIGNAL_STATE_CHANGED, self.onStateChanged)
        QObject.connect(self.getQHttp(),QHttpUploadProxy.SIGNAL_READY_READ, self.onReadyRead)
        QObject.connect(self.getQHttp(),QHttpUploadProxy.SIGNAL_REQUEST_FINISHED, self.onRequestFinished)
        utils.trace("QHttpUploadProxy","connectQHttpSignals",str(self.getQHttp())+ " connected signals to " + str(self))
        
    def disconnectQHttpSignals(self):
        assert(self.getQHttp() is not None)
        QObject.disconnect(self.getQHttp(),QHttpUploadProxy.SIGNAL_DATA_READ_PROGRESS,self.onDataReadProgress)
        QObject.disconnect(self.getQHttp(),QHttpUploadProxy.SIGNAL_DATA_SEND_PROGRESS,self.onDataSendProgress)
        QObject.disconnect(self.getQHttp(),QHttpUploadProxy.SIGNAL_DATA_DONE, self.onDataDone)
        QObject.disconnect(self.getQHttp(),QHttpUploadProxy.SIGNAL_REQUEST_STARTED, self.onRequestStarted)
        QObject.disconnect(self.getQHttp(),QHttpUploadProxy.SIGNAL_STATE_CHANGED, self.onStateChanged)
        QObject.disconnect(self.getQHttp(),QHttpUploadProxy.SIGNAL_READY_READ, self.onReadyRead)
        QObject.disconnect(self.getQHttp(),QHttpUploadProxy.SIGNAL_REQUEST_FINISHED, self.onRequestFinished)
        utils.trace("QHttpUploadProxy","disconnectQHttpSignals",str(self.getQHttp())+ " disconnected signals from " + str(self) )

    def onRequestStarted(self,id):
        print "QHttpUploadProxy.onRequestStarted() - ",id

    def onStateChanged(self, state):
        """
        QHttp.Unconnected     0  There is no connection to the host.
        QHttp.HostLookup      1  A host name lookup is in progress.
        QHttp.Connecting      2  An attempt to connect to the host is in progress.
        QHttp.Sending         3  The client is sending its request to the server.
        QHttp.Reading         4  The client's request has been sent and the client is reading the server's response.
        QHttp.Connected       5  The connection to the host is open, but the client is neither sending a request, nor waiting for a response.
        QHttp.Closing         6  The connection is closing down, but is not yet closed. (The state will be Unconnected when the connection is closed.)
        """        
        debugState={0:"Unconnected",1:"HostLookup",
                    2:"Connecting",3:"Sending",
                    4:"Reading",5:"Connected",
                    6:"Closing"}
        print "QHttpUploadProxy.onStateChanged()! state:",debugState[state]

    def onDataReadProgress(self, done, total):
        print "QHttpUploadProxy.onDataReadProgress() done:",done,"total:",total
        print "QHttpUploadProxy.onDataDreadProgress() myToken size is:",self.getUploadToken().getChunkSize()

    def onDataSendProgress(self, done, total):
        '''
        Since we only know how many bytes we've done for this request.
        We're going to calculate the delta bytes, vs the last time this
        slot was invoked.
        
        done - represents the number of bytes sent for this request so far.
        total - represents the total number of bytes sent for this request.
        
        We need to take in consideration that there is an overhead
        thanks to all the HTTP headers, but the UploadTransaction object
        only cares about the bytes of its current chunk being uploaded.
        
        So we'll keep in memory a 'lastBytesDone' and we'll start
        telling the upload manager to add  (done - lastBytesDone)
        once we've transfered > HTTP overhead bytes.
        
        Very simple.
        
        Suppose we have an overhead of 100bytes.
        A Chunk of 5000 bytes
        And we start getting dataSendProgress() signals...
        
        done   lastBytesDone   total    bytesToAddUp
        50     0                50         50 < 100 bytes, overhead... dont report
        100    50               150        done-lastBytesDone=50 and total > overhead, report 50 bytes
        300    100              450        200 bytes more went up 
        n      300
        ...
        n+k    n                bytesToAddUp = k 
        '''
        """
        print "QHttpUploadProxy.onDataSendProgress:"
        print "\tdone (so far):",done
        print "\ttotal (C):",total
        print "\toverhead (C):",self.overheadBytes
        print "\tlastDone:",self.lastBytesDone
        print "\tchunkSize:", self.getUploadToken().getChunkSize()
        print "\n"
        """
        bytesSent=0
        
        #once we've sent all the HTTP headers, let's count them out, but let's do this
        #only once...
        #print "done (so far)",done
        if done > self.overheadBytes and not self.tookOverheadOut:
            #report to uploadTransaction only when we've sent more than our overhead.
            bytesSent=done-self.overheadBytes-self.lastBytesDone
            self.getUploadTransaction().addBytesSent(bytesSent)
            self.tookOverheadOut = True
            #raw_input("Added Bytes (" + str(bytesSent) + ") minus overhead ("+str(self.overheadBytes)+") Last Bytes Done is Zero? " + str(self.lastBytesDone))
            self.lastBytesDone = bytesSent
            print
        elif self.lastBytesDone > self.overheadBytes:
            bytesSent = done-self.lastBytesDone
            self.getUploadTransaction().addBytesSent(bytesSent)
            #raw_input("Added Bytes (" + str(bytesSent) + ") Last Bytes Done: " + str(self.lastBytesDone))
            self.lastBytesDone = done
            print

            
        if self.getUploadTransaction().getSafeBytesSent() > self.getUploadTransaction().getFileSize():
            print "WTF\n"*20, "We've sent more than the file is, why?"
            print "Bytes Sent:", self.getUploadTransaction().getBytesSent()
            print "Safe Bytes Sent:", self.getUploadTransaction().getSafeBytesSent()
            print "File Size:", self.getUploadTransaction().getFileSize()
            print "Delta Bytes:", long(self.getUploadTransaction().getBytesSent() - self.getUploadTransaction().getFileSize())
            print "OverHead?:", self.overheadBytes
            print "ChunkSize:", self.getUploadToken().getChunkSize()


    def onReadyRead(self, responseHeader):
        print "QHttpUploadProxy.onReadyRead!!"
        print "QHttpUploadProxy.onreadyRead\n>>>\n",responseHeader.toString(),"<<<"
        
        if responseHeader.statusCode() >= 400 and responseHeader.statusCode() <= 599:
            #oh oh, shutdown
            if self.getQHttp() is not None:
                utils.trace("QHttpUploadProxy","onReadyRead","Got a 400 response, killing QHttp")
                self.disconnectQHttpSignals()
                self.getQHttp().abort()
                self.getQHttp().close()
                self.getFileObject().close()
                
            response = str(QString(self.getQHttp().readAll()))
            print "Error Response Token if any was ->\n",response
            print "==\n"

            #notify the transaction there's been an error
            self.getUploadTransaction().setUploadStatus(self.uploadTransaction.STATUS_ERROR)
        elif responseHeader.statusCode() == 200:
            #Let's read the response from the server.
            response = str(QString(self.getQHttp().readAll()))
            
            #utils.trace("QHttpUploadProxy","onReadyRead","RESPONSE IS THIS")
            #print "<"*40
            #print response
            #print "<"*40
            #print
            
            responseDict = None
            
            try:
                responseDict = simplejson.loads(response)
            except:
                utils.trace("QHttpUploadProxy","onReadyRead","Problems reading the JSON")
                print "is the response valid JSON?\ (Re-transmitting)n\n",response
                print
                #we retransmit the same chunk again
                #we gotta discard whatever bytes were just sent
                self.getUploadTransaction().setSafeBytesSent(self.getUploadToken().getNextOffset())
                self.onNewUploadToken(self.getUploadToken())
                return
            
            if responseDict['status'] == '1':
                uploadTokenDict = responseDict['result']
            else:
                #ON ERRORS REPORTED BY THE NEW TOKEN...
                if int(57) == int(responseDict['errorCode']):
                    #COULD NOT VALIDATE CHECKSUM OF THIS CHUNK, TRY AGAIN
                    utils.trace("QHttpUploadProxy","onReadyRead","Got error 57, RE-SENDING CHUNK")
                    self.onNewUploadToken(self.getUploadToken())
                    return
                
                self.stopUpload(notifyUploadTransaction=True,
                                uploadTransactionStatus=self.getUploadTransaction().STATUS_ERROR)
                
                raise UploadTokenException(responseDict['result']['errorMessage'])
            
            print "QHttpUpload.onReadyRead() this is what came\n",response
            
            #let's create that next token, oh yeah baby
            newUploadToken = None
            try:
                newUploadToken = UploadToken(uploadTokenDict,
                                             self.getUploadToken().getBlooploadChunkFilename(),
                                             self.getUploadTransaction().getRemoteSession(),
                                             self.getFileObject())
                newUploadToken.save() #very important
                
                if newUploadToken.shouldGo() or newUploadToken.shouldStop():
                    self.getUploadTransaction().setSafeBytesSent(newUploadToken.getNextOffset())
                    
                self.getUploadTransaction().setUploadToken(newUploadToken) #TEST WATCH OUT
                self.setUploadToken(newUploadToken)
                self.onNewUploadToken(newUploadToken)
            except UploadEndedException, e:
                utils.showTraceback("onReadyRead: onNewUploadToken raised an UploadEndedException")
                upload_transaction = self.getUploadTransaction()
                upload_transaction.setSafeBytesSent(upload_transaction.getFileSize())
                upload_transaction.setUploadPercentage(100,
                                                       persist=False, 
                                                       emitSignal=True)
                self.stopUpload(notifyUploadTransaction=True,
                                uploadTransactionStatus=upload_transaction.STATUS_ENDED,
                                persist=True)
            except UploadStoppedException, e:
                utils.showTraceback("onReadyRead: onNewUploadToken raised UploadStoppedException")
                self.stopUpload(notifyUploadTransaction=True,
                                uploadTransactionStatus=self.getUploadTransaction().STATUS_STOP,
                                persist=True)
            except UploadTokenException,e:
                utils.showTraceback("onReadyRead: Problems creating nextUploadToken")
                from models.upload_manager import UploadTransaction
                self.stopUpload(notifyUploadTransaction=True,
                                uploadTransactionStatus=self.getUploadTransaction().STATUS_ERROR)
                              
        else:
            response = str(QString(self.getQHttp().readAll()))
            print "QHttpUpload.onReadyRead() ???? ", responseHeader.statusCode()
            print "QHttpUpload.onReadyRead() this is what came\n",response
            print "What do we do...?"

    def onNewUploadToken(self,newUploadToken):
        #TODO: Check if there's a logic conflict here between asking about the
        #transaction  status, and then asking on the Token
        fileObj = self.getFileObject()
        upload_transaction = self.getUploadTransaction()
        
        assert(newUploadToken is not None)
        assert(upload_transaction is not None)
        
        #PAUSE
        if upload_transaction.getUploadStatus() == upload_transaction.STATUS_STOP:
            fileObj.close()
            raise UploadStoppedException(upload_transaction)

        #CANCEL
        if upload_transaction.getUploadStatus() == upload_transaction.STATUS_CANCELLED:
            self.getUploadToken().clear()
            newUploadToken.clear()
            fileObj.close()
            raise UploadCancelledException(upload_transaction)

        #LET'S RE-ARRANGE BEFORE WE CONTINUE
        if newUploadToken is not None:
            upload_transaction.setUploadToken(newUploadToken)
            self.setUploadToken(newUploadToken)
            newUploadToken.save()

        #UPLOAD NEXT CHUNK
        if newUploadToken.shouldGo():
            self.uploadChunk(self.getRemoteSession().getSessionId(), 
                             newUploadToken,
                             fileObj, 
                             False)
            return True
        elif newUploadToken.shouldEnd():
            fileObj.close()
            newUploadToken.clear()
            #utils.trace("QHttpUploadProxy","onNewUploadToken","We were told to finish uploading [%s]" % fileObj.name)
            raise UploadEndedException(upload_transaction)
        elif newUploadToken.shouldStop():
            fileObj.close()
            #utils.trace("QHttpUploadProxy","onNewUploadToken","We'll continue uploading [%s] later" % fileObj.name)
            raise UploadStoppedException(upload_transaction)
        elif newUploadToken.shouldHandleError():
            fileObj.close()
            print "Token Error Message:","(",newUploadToken.getErrorCode(),") ", newUploadToken.getErrorMessage()
            newUploadToken.clear()
            #utils.trace("QHttpUploadProxy","onNewUploadToken","There was a problem uploading the file " + fileObj.name) 
            raise UploadTokenException('Token asks to handle error')
        
    def onRequestFinished(self, id, error):
        print "QHttpUploadProxy.onRequestFinished()"
        
    def startUpload(self,useNewQHttp=True):
        '''
        Starts the process with the first uploadChunk.
        '''
        assert(self.getUploadToken() is not None)
        assert(self.getRemoteSession() is not None)
        assert(self.getUploadTransaction() is not None)
        
        if useNewQHttp:
            self.initQHttp()
            #no need for uploadChunk to initiate another QHttp
            useNewQHttp = False 
        
        if self.getFileObject() is not None and not self.getFileObject().closed:
            self.getFileObject().close()
            
        self.setFileObject(open(self.getUploadTransaction().getFilePath(),"rb"))
        self.uploadChunk(self.getRemoteSession().getSessionId(), 
                         self.getUploadToken(), 
                         self.getFileObject(), 
                         useNewQHttp)

    def onDataDone(self, error):
        print "QHttpUploadProxy.onDataDone booleanResult",error
        if error:
            self.printQHttpError()

    def uploadChunk(self, sessionId, uploadToken, fileObj, useNewQHttp=False):
        '''this will prepare and send an HTTP post to the remote POST handler
        and it will parse the output of that script to return a new
        uploadToken.
        
        This function is not blocking, its executed asynchronously.
        
        Your code should add a listener to this QHttpUploadProxy
        Once it's done you should read what's on getIODevice()
        
        Pass useNewQHttp=True when sending the first chunk, or if we are resuming an upload
        from a past session, this will make this object instanciate a new QHttp
        '''
        assert(sessionId is not None)
        assert(uploadToken is not None)
        assert(fileObj is not None)
        assert(not fileObj.closed)

        #reset counters and flags for new chunk transfer
        self.overheadBytes = 0
        self.lastBytesDone = 0
        self.tookOverheadOut = False
        
        if self.getFileObject() != fileObj:
            self.setFileObject(fileObj) #keep reference for when you're done completely
            
        if self.getUploadToken() != uploadToken:
            utils.trace("QHttpUploadProxy","uploadChunk","Refreshing our uploadToken")
            print uploadToken
            self.setUploadToken(uploadToken)
        
        if uploadToken.shouldEnd():
            from models.RemoteSession import UploadStoppedException
            fileObj.close()
            self.disconnectQHttpSignals()
            utils.trace("QHttpUploadProxy","uploadChunk","We are so done")
            self.getUploadToken().clear() #delete the token file
            self.stopUpload(notifyUploadTransaction=False) #let notification to the exception handler
            raise UploadEndedException("UploadToken says we're done")

        chunkData = None
        try:
            fileObj.seek(uploadToken.getNextOffset(),0)
            chunkData = fileObj.read(uploadToken.getChunkSize()) #we are not responsible of closing this file, its done outside
            uploadToken.setChunkChecksumHash(md5.new(chunkData).hexdigest())
        except Exception,e:
            print "QHttpUploadProxy.uploadChunk() exception - "
            print e
            utils.showStacktrace("QHttpUploadProxy.uploadChunk chunk preparation problem")
        
        assert(uploadToken.getChunkSize() > 0)
        print "ChunkData Size:",len(chunkData),"vs Chunk Size:", uploadToken.getChunkSize()
        assert(len(chunkData) == uploadToken.getChunkSize())
        
        #prepare fields
        fields = [('sessionId',sessionId),
                  ('tokenId',uploadToken.getTokenId()),
                  ('nextOffset',str(uploadToken.getNextOffset())),
                  ('chunkSize',str(uploadToken.getChunkSize())),
                  ('chunkChecksum',uploadToken.getChunkChecksumHash())]


        print "QHttpUploadProxy FIELDS:"
        print ">>"
        for f in fields:
            print "\t",f
        print "<<"

        content_type, body = self.encode_multipart_formdata(fields, [('data',str(self.getUploadToken().getNextOffset()),chunkData)])

        print "Content-type",content_type
        assert(body is not None)
        assert(len(body) > 0)

        httpRequestHeader = None
        
        try:
            httpRequestHeader = QHttpRequestHeader("POST",self.getScript())
            httpRequestHeader.setValue('Host',self.getHost())
            
            from models.mbu_config import meta
            
            httpRequestHeader.setValue("User-Agent","Blooploader " + meta["APPLICATION_VERSION"])        
            httpRequestHeader.setContentType(content_type)
            httpRequestHeader.setContentLength(len(body))

            self.lastBytesDone = 0
            self.tookOverheadOut = False
            
            assert(len(chunkData) == self.getUploadToken().getChunkSize())
            self.overheadBytes = len(body) - int(self.getUploadToken().getChunkSize())
            
            utils.trace("QHttpUploadProxy","uploadChunk","LastBytesDone: " + str(self.lastBytesDone))
            utils.trace("QHttpUploadProxy","uploadChunk","Chunk Data Size: " + str(len(chunkData)))
            utils.trace("QHttpUploadProxy","uploadChunk","Overhead Bytes: " + str(self.overheadBytes))
            
            #THE CHUNK AND FIELDS ENCODED IN MULTIPART FORMAT
            self.byteArray = QByteArray()
            self.byteArray.append(body)
            #self.toQIODevice = QBuffer(self.byteArray)
            
            #In case this is the first chunk
            if useNewQHttp or self.getQHttp() is None:
                utils.trace("QHttpUploadProxy","uploadChunk","Using new QHttp")
                self.initQHttp()

            print "About to send this RequestHeader:\n",">>>"*30,"\n",httpRequestHeader.toString(),"\n","<<<"*30
            self.getQHttp().request(httpRequestHeader, self.byteArray)
            print "http object ->", self.getQHttp()
            print "http state ->",  self.getQHttp().state()
        except:
            fileObj.close()
            utils.showTraceback("FAILED DURING QHttp creation.")
            
    def stopUpload(self,notifyUploadTransaction=False,uploadTransactionStatus=None,persist=False):
        utils.trace("QHttpUploadProxy","stopUpload","WATCH OUT SOMEONE ORDERD THIS UPLOAD TO BE STOPPED")
        if self.getQHttp() is not None:
            self.disconnectQHttpSignals()
            self.getQHttp().abort()
            self.getQHttp().close()

        if self.getUploadTransaction() is not None:
            self.getUploadTransaction().setUploading(False)
        
        if notifyUploadTransaction and uploadTransactionStatus is not None:
            self.getUploadTransaction().setUploadStatus(uploadTransactionStatus,persist)
            
    def printQHttpError(self):
        if self.getQHttp() is None:
            print "QHttpUploadProxy has no QHttp object!!! @"
            print self
            return
        
        print "QHttpUploadProxy.printQHttpError() Error Code:",self.getQHttp().error()
        print "QHttpUploadProxy.printQHttpError() Error Message", self.getQHttp().errorString()

class UploadEndedException(Exception):
       def __init__(self,value):
           self.parameter=value
       def __str__(self):
           return repr(self.parameter)
          
class UploadStoppedException(Exception):
       def __init__(self,value):
           self.parameter=value
       def __str__(self):
           return repr(self.parameter)
       
class UploadCancelledException(Exception):
       def __init__(self,value):
           self.parameter=value
       def __str__(self):
           return repr(self.parameter)