"""
* Author: Angel Leon
* Date: Oct, 5th, 2008
*
* NOTE: For those developers that got here looking for py2deb, I don't use
* any libraries similar to py2exe or py2app in here. I build my .deb manually.
* I just kept a naming convention since my other scripts are called like that.
* Feel free to see how I build my primitive .deb, nothing too fancy in here.
*
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
import os

LIB_DIR='/usr/lib/blooploader'
BIN_DIR='/usr/bin'
SHARE_DIR='/usr/share'
APP_DIR=SHARE_DIR+'/applications'
HICOLOR_DIR=SHARE_DIR + '/icons/hicolor'
DOC_DIR=SHARE_DIR + '/doc/blooploader'

def rm_rf(d):
  #removes folders recursively
  for path in (os.path.join(d,f) for f in os.listdir(d)):
    if os.path.isdir(path):
      rm_rf(path)
    else:
      os.unlink(path)
  os.rmdir(d)

def cleanCurrentFolder():
  #clean everything but the control file
  contents = os.listdir('.')

  for item in contents:
    if item in ('DEBIAN','.svn'):
      continue
    else:
      if os.path.isdir(item):
        rm_rf(item)
        print '(deleted',item,'folder)'
      elif os.path.isfile(item):
        os.unlink(item)
        print '(deleted',item,'file)'

def makeFolderStructure():
  os.makedirs('.' + LIB_DIR)
  os.makedirs('.' + LIB_DIR + '/resume')

  os.makedirs('.' + SHARE_DIR)
  os.makedirs('.' + HICOLOR_DIR + '/16x16/apps')
  os.makedirs('.' + HICOLOR_DIR + '/32x32/apps')
  os.makedirs('.' + HICOLOR_DIR + '/48x48/apps')
  os.makedirs('.' + HICOLOR_DIR + '/64x64/apps')
  os.makedirs('.' + HICOLOR_DIR + '/128x128/apps')  

  os.makedirs('.' + APP_DIR)
  os.makedirs('.' + BIN_DIR)
  os.makedirs('.' + DOC_DIR)

def copyFiles():
  #copy the launcher scripts and icon
  os.system('cp ../blooploader.py .'+LIB_DIR)
  os.system('cp ../blooploader .'+BIN_DIR)
  os.system('chmod +x .'+BIN_DIR+'/blooploader')

  #take care of the icons
  os.system('cp ../icons/16x16.png .'+ HICOLOR_DIR +'/16x16/apps/blooploader.png')
  os.system('cp ../icons/32x32.png .'+ HICOLOR_DIR +'/32x32/apps/blooploader.png')
  os.system('cp ../icons/48x48.png .'+ HICOLOR_DIR +'/48x48/apps/blooploader.png')
  os.system('cp ../icons/64x64.png .'+ HICOLOR_DIR +'/64x64/apps/blooploader.png')
  os.system('cp ../icons/128x128.png .'+ HICOLOR_DIR +'/128x128/apps/blooploader.png')

  #copy License and changelog to /usr/share/doc/blooploader
  os.system('cp ../changelog.txt .'+DOC_DIR)
  os.system('cp ../License.txt .'+DOC_DIR)

  #copy the desktop launcher
  os.system('cp ../blooploader.desktop .'+APP_DIR)
  os.system('chmod +x .'+APP_DIR+'/blooploader.desktop')

  #copy all the good stuff
  os.system('cp -R ../models .'+LIB_DIR)
  os.system('cp -R ../controllers .'+LIB_DIR)
  os.system('cp -R ../views .'+LIB_DIR)
  os.system('cp -R ../lib .'+LIB_DIR)
  os.system('cp -R ../utils .'+LIB_DIR)
  os.system('cp -R ../i18n .'+LIB_DIR)

  #remove .svn related stuff
  os.chdir('usr/lib/blooploader')
  os.system('rm -rf ./.svn')
  os.system('rm -rf ./*/.svn')
  os.system('rm -rf ./*/*/.svn')
  os.system('rm -rf ./*/*/*/.svn')
  os.system('rm -rf ./*/*/*/*/.svn')
  os.system('rm -rf ./*/*/*/*/*/.svn')
  os.chdir('../../../')

def makePackage():
  #This function asssumes you're standing outside, say on
  #~/workspace/blooploader and that you can see the 'debian'
  #folder.

  #dpkg -D1 -b ${FW_DIR}/ ${FW_DIR}.i586.deb
  os.system('dpkg -D1 -b debian blooploader.i586.deb')

if os.path.exists('blooploader.i586.deb'):
  os.unlink('blooploader.i586.deb')

os.chdir('debian')
cleanCurrentFolder()
makeFolderStructure()
copyFiles()

os.chdir('..')
makePackage()
