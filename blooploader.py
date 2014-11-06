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

main module

This module starts the Blooploader
'''
import sip
from PyQt4.QtGui import QApplication
import utils
import sys
import controllers
from controllers.AppController import AppController
from controllers.LoginController import LoginController
import views
from views.LoginView import LoginView
from views.MainView import MainView

if __name__=='__main__':
    print "Launching "
    utils.printSupportedImageFormats()
    #mainFrame = MainFrame()
    app = QApplication(sys.argv)
    
    #damn clean (up to here)
    AppController.getInstance().showLoginView()

    #utils.traceQThread(app)
    sys.exit(app.exec_())