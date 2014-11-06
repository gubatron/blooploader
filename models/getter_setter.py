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

module models.getter_setter
'''
class GetterSetter:
    '''Class you can inherit to have safe get and set methods easily'''
    def __init__(self):
        self.properties = {}

    def _get(self,property,value=None):
        '''Getter method, but can be set to return a default value'''
        if self.properties == None:
            return value

        if self.properties.has_key(property) == False:
            return value

        return self.properties[property]

    def _set(self,key,value):
        self.properties[key] = value
