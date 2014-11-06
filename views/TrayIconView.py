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

module views.TrayIconView
"""
from PyQt4.QtGui import QPixmap,QIcon,QSystemTrayIcon,QMenu
from PyQt4.QtCore import Qt
from PyQt4.QtCore import QObject,SIGNAL

from views.MainView import MainView

from controllers.ActionManager import ActionManager

from __init__ import View

import os

class TrayIconView(QSystemTrayIcon, View):
    _menu = None
    
    _aboutAction = None
    
    def __init__(self):
        if QSystemTrayIcon.isSystemTrayAvailable():
            QSystemTrayIcon.__init__(self)
            
            iconPath = os.path.join("i18n","images","us_en","bloop.png")
            self.setIcon(QIcon(QPixmap(iconPath)))
            self.initContextMenu()
            self.show()
            self.show()
    
    def initContextMenu(self):
        self._menu = QMenu(MainView.getInstance())

        self._aboutAction = ActionManager.getInstance().getAboutDialogAction()
        self._menu.addAction(self._aboutAction)

        self.setContextMenu(self._menu)    