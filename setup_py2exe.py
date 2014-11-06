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
from distutils.core import setup
import py2exe
import shutil
import os
import utils
import sys

sys.argv.append('py2exe')
dist_dir = 'dist'
build_dir = 'build'

#Clean existing builds
if os.path.exists(dist_dir):
  print "Old distribution directory removed (" + dist_dir + ")"
  shutil.rmtree(dist_dir)

if os.path.exists(build_dir):
  print "Old build directory removed (" + build_dir + ")"
  shutil.rmtree(build_dir)

opts = {"py2exe":{}}
opts["py2exe"]['optimize'] = 2
opts["py2exe"]['includes'] = ['jsonrpc','simplejson']


#we add all the images as data_files
images = []
files = os.listdir('i18n\\images\\us_en')
for file in files:
    if file.endswith('png') or file.endswith('jpg') or file.endswith('gif'):
        images.append('i18n\\images\\us_en\\'+file)

#A list of tuples, first element is the path of the directory, the second
#is a list of the files that you want to include on that directory
d_files = [('i18n\\images\\us_en',images)]

#setup(console=|windows=
setup(windows=[{'script':'blooploader.py',
                'icon_resources':[(1,'blooploader.ico')]}],
      options=opts, 
      data_files=d_files)
