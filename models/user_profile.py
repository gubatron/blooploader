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

module models.user_profile
'''
from getter_setter import GetterSetter

class UserProfile(GetterSetter):
    def __init__(self,properties):
       GetterSetter.__init__(self)
       
       #fricking sweet constructor, fields will be always based on the db
       #fldLastname,fldEmail,fldFirstname,fldUsername,fldDateTime,
       #fldCountry,fldState,fldProfileViews,fldLoginCount
       for x in properties:
           self._set(x,properties[x])

    def getFirstname(self):
        return self._get('fldFirstname')

    def getLastname(self):
        return self._get('fldLastname')

    def getEmail(self):
        return self._get('fldEmail')

    def getUsername(self):
        return self._get('fldUsername')

    def getDateTime(self):
        return self._get('fldDateTime')

    def getCountry(self):
        return self._get('fldCountry')

    def getState(self):
        return self._get('fldState')

    def getProfileViews(self):
        return self._get('fldProfileViews')

    def getLoginCount(self):
        return self._get('fldLoginCount')

    def getProfilePictureURL(self):
        return self._get('fldProfilePictureURL')
