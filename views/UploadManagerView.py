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

module views.UploadManagerView
"""
from PyQt4.QtCore import QString, QStringList,QMutex, QMutexLocker, SIGNAL
from PyQt4.QtGui import QTreeWidget
from PyQt4.QtGui import QToolBar
from views.__init__ import View
import utils

class UploadManagerView(QTreeWidget,View):
    """
    This component has a list of UploadTransactionView
    objects. This component depicts the status of the UploadManager
    object.
    """
    _widget = None
    _uploadTransactionViews = None
    _mainLayout = None
    _toolbar = None
    
    def __init__(self,parentWidget):
        QTreeWidget.__init__(self,parentWidget)
        View.__init__(self)
        
        self._mutex = QMutex()
        
        self._uploadTransactionViews = []
        
        self.setColumnCount(3)
        
        columnNames = QStringList()
        columnNames.append("Filename")
        columnNames.append("Status")
        columnNames.append("Upload progress")
        self.setHeaderLabels(columnNames)
        self.setSelectionMode(self.ExtendedSelection)
        
        #on double click of a transaction, let's have the controller deal with whatever happened
        self.connect(self,SIGNAL("itemDoubleClicked (QTreeWidgetItem *,int)"), self.onItemDoubleClicked)
        #self.adjustSize()
        
        self.initToolBar()
        
    def initToolBar(self):
        self._toolbar = QToolBar(QString("Blooploads"),self.parent())
        from controllers.ActionManager import ActionManager
        uploadManagerActions = ActionManager.getInstance().getBloopUploadManagerActions()
        
        for action in uploadManagerActions:
            self._toolbar.addAction(action)
            
        #utils.trace("UploadManagerView","initToolBar()",self._toolbar)

    def getToolBar(self):
        if self._toolbar is None:
            self.initToolBar()
        #utils.trace("UploadManagerView","getToolBar()",self._toolbar)
        return self._toolbar
                 
    def onItemDoubleClicked(self, uploadTransactionView, column):
        if self.getController() is not None:
            self.getController().onTransactionDoubleClicked(uploadTransactionView, column)
    
    def addUploadTransactionView(self, uploadTransactionView):
        #We won't add it if its there already
        
        if uploadTransactionView in self._uploadTransactionViews:
            #print
            #utils.trace("UploadManagerView","addUploadTransactionView","Skipping, transaction exists already on the view")
            #print uploadTransactionView
            #print
            return
        
        self._uploadTransactionViews.append(uploadTransactionView)

        itemCount = len(self._uploadTransactionViews)
        self.insertTopLevelItem(itemCount-1,uploadTransactionView)
        #uploadTransactionView.updateStatus()
        #utils.trace("UploadManagerView","addUploadTransactionView","ADDED ONE TRANSACTION TO THE VIEW")
        #utils.trace("UploadManagerView","addUploadTransactionView",uploadTransactionView)

    def clearUploadTransactions(self):
        '''
        It will clear whatever is on the UploadTransactionView.
        '''
        while len(self._uploadTransactionViews) > 0:
            uploadTransactionView = self._uploadTransactionViews.pop()
            self.takeTopLevelItem(self.indexOfTopLevelItem(uploadTransactionView))
            self._uploadTransactionViews.remove(uploadTransactionView)
            uploadTransactionView.deleteLater()

        self._uploadTransactionViews = []


    def removeUploadTransactionView(self, uploadTransactionView):
        try:
            self._uploadTransactionViews.remove(uploadTransactionView)
        except ValueError:
            #utils.trace("UploadManagerView","removeUploadTransactionView","ELEMENT IS GONE ALREADY, CANT REMOVE")
            pass
        
        indexOfUploadTransactionView = self.indexOfTopLevelItem(uploadTransactionView)
        self.takeTopLevelItem(indexOfUploadTransactionView)
        #utils.trace("UploadManagerView","removeUploadTransactionView",uploadTransactionView)
        #utils.trace("UploadManagerView","removeUploadTransactionView","at index " + str(indexOfUploadTransactionView))