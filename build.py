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

Just invoke this script to build, no matter on what OS you are.
All you need to do is

$ python build.py

It should do everything in one step, meaning building the distributable build for your current os.
'''

import os
import sys

def rm_rf(d):
  #removes folders recursively
  for path in (os.path.join(d,f) for f in os.listdir(d)):
    if os.path.isdir(path):
      rm_rf(path)
    else:
      os.unlink(path)
  os.rmdir(d)

def darwinBuild():
  dirs = ('dist','build')
  for d in dirs:
    if os.path.exists(d):
      rm_rf(d)

  print "build.py: darwinBuild() - Building Application"
  os.system('python setup_py2app.py')

  print "Done"  

def win32Build():
  #builds for windows
  dirs = ('dist','build')
  for d in dirs:
    if os.path.exists(d):
      rm_rf(d)

  print "build.py: win32Build() - Building Application"
  os.system('python setup_py2exe.py')

def linuxBuild():
  #makes .deb and .rpm packages.
  os.system('python setup_py2deb.py')

  #TODO: make the RPM with alien
  #check the .deb exists
  #alien --to-rpm frostwire-${FW_VERSION}.i586.deb

if 'uname' in dir(os):
  if os.uname()[0] == 'Linux':
    linuxBuild()
  elif os.uname()[0] == 'Darwin':
    darwinBuild()
elif os.name == 'nt':
  win32Build()

