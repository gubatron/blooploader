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

"""
from setuptools import setup
import os
import shutil
import utils
import sys

from models.mbu_config import meta

BLOOPLOADER_VERSION = meta['APPLICATION_VERSION']
IMAGE_VOLUME_NAME="Blooploader-%s" % BLOOPLOADER_VERSION
IMAGE_VOLUME_NAME_LOWERCASE="blooploader-%s" % BLOOPLOADER_VERSION
VOLUME_FOLDER='BLOOPLOADER_DMG_VOLUME_FOLDER'

sys.argv.append('py2app')

APP = ['blooploader.py']

dist_dir = 'dist'
build_dir = 'build'

def createDMG():
    """Creates a plain DMG image for MacOS users.
    It serves the purpose as it is. It just doesn't have
    a background image, or a custom icon when it's mounted.

    Any Mac User should know what to do with this, basically
    double click it, and then drag the Blooploader icon to
    the Applications folder (be it the symlink provided in the
    image, or the real Applications folder)
    """

    print "Deleting any DMG files present"
    os.system('rm *.dmg')
    
    print "Creating Volume Folder"
    os.system("rm -rf %s" % VOLUME_FOLDER)
    os.system("mkdir %s" % VOLUME_FOLDER)

    print "Moving Blooploader.app to Volume Folder"
    os.system("mv dist/blooploader.app %s" % VOLUME_FOLDER)

    print "Copying License"
    os.system("cp License.txt %s" % VOLUME_FOLDER)

    print "Creating Symlink to Applications Folder so they drag n drop"
    os.system("ln -s /Applications %s/Applications" % VOLUME_FOLDER)

    print "Creating DMG"
    os.system("hdiutil create -srcfolder %s -volname %s %s" % (VOLUME_FOLDER, IMAGE_VOLUME_NAME, IMAGE_VOLUME_NAME_LOWERCASE))

    print "Finished"

################################

# Start building the .APP

# Setup all options, resources and dependencies

#Clean existing builds
if os.path.exists(dist_dir):
  print "Old distribution directory removed (" + dist_dir + ")"
  shutil.rmtree(dist_dir)

if os.path.exists(build_dir):
  print "Old build directory remvoed (" + build_dir + ")"
  shutil.rmtree(build_dir)

#we add all the images as data_files
images = []
files = os.listdir('i18n/images/us_en')
for file in files:
    if file.endswith('png') or file.endswith('jpg') or file.endswith('gif'):
        print "Appending",'i18n/images/us_en/'+file
        images.append('i18n/images/us_en/'+file)
DATA_FILES = [('i18n/images/us_en',images)]

includes = ['jsonrpc','simplejson','i18n','utils']

OPTIONS = {'argv_emulation': True, 
           'resources': ['i18n','lib'],
           'optimize':2,
           'includes':includes,
           'iconfile':'blooploader.icns'}

#Perform the actual build
setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)

createDMG()

