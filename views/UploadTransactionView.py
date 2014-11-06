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

module views.UploadTransactionView
'''
from PyQt4.QtGui import QProgressBar,QTreeWidgetItem
from views.__init__ import View
import utils

class UploadTransactionView(QTreeWidgetItem,View):
    #The widget that shows the progress of the upload.

    #TODO: Add time estimate. Might want to alter the core
    #to include timestamps on the upload transaction for each
    #new uploadToken received.

    #IDEA: Instead of updating the upload token on the UploadTransaction
    #we can add each token to a list on the UploadTransaction (transaction_tokens), and add the
    #timestamp. Then based on past progress, we can tell 3 things:
    # - Get an approximation of the transfer rate kb/s
    # - Time spent uploading
    # - Time left
    COLUMN_FILENAME = 0
    COLUMN_STATUS = 1
    COLUMN_PERCENTAGE = 2
    COLUMN_TEST_WIDGET = 3
    _uploadTransactionModel = None #UploadTransactionModel object
    _treeWidget = None
    
    def __init__(self, parentWidget, uploadTransaction):
        QTreeWidgetItem.__init__(self, None,QTreeWidgetItem.UserType)
        View.__init__(self)
        
        self.setTreeWidget(parentWidget)

        #we bootstrap the inner components and put the "LEGO" together
        self._uploadTransactionModel = uploadTransaction
        self._uploadTransactionProgressBar = QProgressBar()
        self._uploadTransactionProgressBar.setTextVisible(True)
        self._uploadTransactionProgressBar.setAutoFillBackground(True)

        self.setText(UploadTransactionView.COLUMN_FILENAME,utils.getFileName(uploadTransaction.getFilePath()))
        self.setText(UploadTransactionView.COLUMN_STATUS,uploadTransaction.getHumanUploadStatus())
        self.getTreeWidget().setItemWidget(self,UploadTransactionView.COLUMN_PERCENTAGE,self._uploadTransactionProgressBar)
        
    def getUploadTransactionModel(self):
        return self._uploadTransactionModel
        
    def updateUploadTransactionModel(self,uploadTransaction):
        #Given the latest transaction object, we grab its token object
        #and we update the percentage of the transaction
        #and other things
        #print "UploadTransactionView.updateUploadTransactionModel",uploadTransaction

        self._uploadTransactionModel = uploadTransaction
        self.setText(UploadTransactionView.COLUMN_PERCENTAGE,str(uploadTransaction.getUploadPercentage())+'%')
        self.setText(UploadTransactionView.COLUMN_STATUS,uploadTransaction.getHumanUploadStatus())

        self.updateStatus()

    def updateStatus(self):
        self.setText(UploadTransactionView.COLUMN_STATUS,self._uploadTransactionModel.getHumanUploadStatus())

        #Update the progress bar
        if self._uploadTransactionModel:
            #self._uploadTransactionProgressBar.setValue(self._uploadTransactionModel.getUploadPercentage())
            self._uploadTransactionProgressBar = QProgressBar()
            self._uploadTransactionProgressBar.setAutoFillBackground(True)
            self._uploadTransactionProgressBar.setValue(self._uploadTransactionModel.getUploadPercentage())
            self.getTreeWidget().setItemWidget(self,UploadTransactionView.COLUMN_PERCENTAGE,self._uploadTransactionProgressBar)

        
    def setTreeWidget(self, parent):
        self._treeWidget = parent
        
    def getTreeWidget(self):
        return self._treeWidget