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

module i18n.us_en
'''
from PyQt4.QtCore import QObject
from models.mbu_config import meta

def tr(str):                                                                                                                                  
    '''Convenience method wrapper'''                                                                                                          
    return QObject().tr(str)                                                                                                                  

LABEL_WINDOW_LOGIN_TITLE = tr("BloopLoader - Login")
LABEL_BLOOPLOADER = tr("BloopLoader")
LABEL_WELCOME = tr("Welcome")
LABEL_SIZE = tr("Size")
LABEL_ONLINE = tr("Online")
LABEL_OFFLINE = tr("Offline")
LABEL_FRIENDSTREE_TITLE_BAR = tr("Friends List")
LABEL_STATUS = tr("Status")
LABEL_BLOOPTREE_STATUS_BAR = tr("Just drag and drop files to start uploading")
LABEL_BLOOPTREE_STATUS_BAR_REQUESTING_FILES = tr("Retrieving list of files from MyBloop...")
LABEL_BLOOPTREE_STATUS_BAR_CREATING_FOLDER = tr("Sexy Time! Creating new folder...")
LABEL_BLOOPTREE_STATUS_BAR_FOLDER_CREATED = tr("Much Success! Folder Created")
LABEL_BLOOPTREE_STATUS_BAR_DELETING = tr("Deleting...")
LABEL_BLOOPTREE_STATUS_BAR_DELETING_FINISHED = tr("Great Success! Finished deleting")
LABEL_BLOOPTREE_STATUS_BAR_RENAMING = tr("Renaming...")
LABEL_BLOOPTREE_STATUS_BAR_RENAMING_FINISHED = tr("Items renamed. You Like? I like!")

LABEL_USERNAME = tr('Username (<a href="http://'+meta['SERVER']+'/register?src=blooploader">Create an Account</a>)')
LABEL_PASSWORD = tr('Password (<a href="http://'+meta['SERVER']+'/pages/forgot.password.o?src=blooploader">Forgot Password?</a>)')
LABEL_REGISTER = tr("Register")
LABEL_REMEMBER_ME = tr("Remember me")
LABEL_LOGIN = tr("Login")
LABEL_OK = tr("Ok")
LABEL_QUIT = tr("Quit")
LABEL_DONE = tr("Done")

LABEL_CONFIRM_FILES_DELETION_TITLE = tr("Confirm Delete")
LABEL_CONFIRM_FILE_DELETION_MESSAGE = tr("Are you sure you want to delete this file?")
LABEL_CONFIRM_FILES_DELETION_MESSAGE = tr("Are you sure you want to delete these files?") 
LABEL_CONFIRM_OPEN_MULTIPLE_LINKS_TITLE = tr("Are you sure you want to open multiple files?")
LABEL_CONFIRM_OPEN_MULTIPLE_LINKS_MESSAGE = tr("You are trying to open multiple files at once. Opening too many files in seperate browser windows may slow down your computer.\n\nAre you sure you want to continue?")
LABEL_CONFIRM_RENAME_FILE_FAILED_TITLE = tr("An error occurred")
LABEL_CANNOT_DOWNLOAD_COPIED_FILE_TITLE = tr("An error occurred")
LABEL_CANNOT_DOWNLOAD_COPIED_FILE_MESSAGE = tr("You cannot download a song that was copied from another user. You can only download songs that you have uploaded in the past.")
LABEL_ABOUT_MSGBOX_TITLE = tr("About ") + LABEL_BLOOPLOADER
LABEL_ABOUT_SUMMARY = tr("The Blooploader. Drag and drop all your files to MyBloop.com")
LABEL_ABOUT_VERSION = tr("Application Version")
LABEL_ABOUT_API_VERSION = tr("Server API Version")
LABEL_ABOUT_OS_NAME = tr("OS Name")
LABEL_ABOUT_QT_VERSION = tr("Qt Version")
LABEL_ABOUT_CREDITS = tr("Concept by Angel Leon and Fitim Blaku\n\nServer Architecture/Development by Fitim Blaku\nClient-side Development by: Angel Leon (Lead role) and Fitim Blaku\nMyBloop.com JSON-RPC API Design: Angel Leon and Fitim Blaku.\n\nThanks to Phill from PyQt4 and to Trolltech for Qt4 being so amazing.\n\nWritten 100% in Python.")
LABEL_ABOUT_COPYRIGHT = tr("(c) 2008 MyBloop LLC. All Rights Reserved.")
LABEL_ABOUT_OPENSOURCE = tr("This product is open source and licensed under the GNU General Public License Version 2.0.\nJoin us at http://code.google.com/p/blooploader")

LABEL_ERROR_REFRESHING_FOLDER = tr("Please try again. I couldn't refresh the folder")

ACTION_BLOOPTREE_REFRESH = tr("&Refresh")
ACTION_BLOOPTREE_NEW_FOLDER = tr("Create &New Folder")
ACTION_BLOOPTREE_DELETE = tr("&Delete")
ACTION_BLOOPTREE_SET_PRIVATE = tr("Mark as P&rivate")
ACTION_BLOOPTREE_SET_PUBLIC = tr("Mark as &Public")
ACTION_BLOOPTREE_COPY_LINK = tr("&Copy Link")
ACTION_BLOOPTREE_COPY_LINKS = tr("&Copy Links")
ACTION_BLOOPTREE_OPEN_LINK = tr("&Open")
ACTION_BLOOPTREE_DOWNLOAD_FILE = tr("&Download File")
ACTION_BLOOPTREE_RENAME = tr("&Rename")

ACTION_LOGOUT = tr("&Logout")
ACTION_EXIT = tr("&Exit")
ACTION_VIEW_CHANGELOG = tr("Recent &Changes")
ACTION_SEND_FEEDBACK = tr("Send &Feedback")
ACTION_ABOUT_DIALOG = tr("&About")


UPDATE_MESSAGE_NEW_VERSION_TITLE = tr('New Version Available')
UPDATE_MESSAGE_WARNING_TITLE = tr('Please upgrade to the newest version of Blooploader')
UPDATE_MESSAGE_MANDATORY = tr("Your version of the Blooploader is no longer compatible. Please upgrade to the newest version to continue.\n\nDo you want to upgrade now?")
UPDATE_MESSAGE_RECOMMENDED =  tr("A new version of the Blooploader is available and is strongly recommended.\n\nDo you want to upgrade to the new version?")

MENU_FILE = tr("&File")
MENU_HELP = tr("&Help")

URL_SEND_FEEDBACK = tr("http://"+meta['SERVER']+"/pages/feedback.o?area=blooploader")
URL_CHANGELOG = tr("http://"+meta['SERVER']+"/blooploader/changelog.o")
