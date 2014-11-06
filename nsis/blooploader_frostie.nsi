/**
Blooploader NSIS Installer Script
Copyright (C) 2008 MyBloop, LLC.
*/

;Application Name
!define APPNAME "BloopLoader"
!define EXECUTABLENAME "blooploader.exe"
!define SHRTAPPNAME "blooploader"
!define APPVERSION "0.7"
!define SMLVERSION "0.7"
!define PUBLISHER "MyBloop LLC"
!define SPECIALBUILD "0.7.0.0"
!define PRIVATEBUILD "0.7.0.0"
!define APPNAMEANDVERSION "${APPNAME} ${SMLVERSION}"
!define OUTFILENAME "${SHRTAPPNAME}-${SMLVERSION}.fw.windows.exe"

!define SHRTDESCR1 "Unlimited Free File Storage."
!define SHRTDESCR2 "Upload all your music, pictures and more."

;Other Constants
!define SITE_URL "http://www.mybloop.com/"
!define FROM "frostwire"

;This URL should add a parameter whenever we want to say this comes from FrostWire Referal
!define BLOOPLOADER_ZIP_URL "http://dl.mybloop.com/blooploader/?platform=windows&from=${FROM}&conduit"

Var OFFER_ACCEPT_TOOLBAR_INSTALL
Var OFFER_ACCEPT_LICENSE

;Install settings
Name "${APPNAMEANDVERSION}"
InstallDir "$PROGRAMFILES\${APPNAME}"
InstallDirRegKey HKLM "Software\${APPNAME}" ""
OutFile "${OUTFILENAME}"

;Compression
;SetCompressor /SOLID LZMA
SetCompressor LZMA
;SetCompressor BZIP2

;Styles
XPStyle on
ShowInstDetails hide
ShowUnInstDetails show

; == INCLUDES ==
;Modern UI
!include "MUI.nsh"

;Logic and loops without jumps, IF, WHILE, FOR, Yay
!include "LogicLib.nsh"
;!include "zipdll.nsh"
!include "WinMessages.nsh"
!include "FileFunc.nsh"


;Interface Configuration
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\nsis.bmp" ; optional
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APPNAME}.exe"
!define MUI_FINISHPAGE_LINK "Official Website: ${SITE_URL}"
!define MUI_FINISHPAGE_LINK_LOCATION ${SITE_URL}
!define MUI_FINISHPAGE_LINK_COLOR "0000FF"
!define MUI_ICON "..\blooploader.ico"


;Pages of the installer
;!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_LICENSE "License.txt"
	Page custom StartToolbarOffer ToolbarValidation ": Optional Components"
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
  
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

ReserveFile "ToolbarOffer.ini"
!insertmacro MUI_RESERVEFILE_INSTALLOPTIONS ;InstallOptions plug-in
!insertmacro MUI_RESERVEFILE_LANGDLL
ReserveFile "toolbar-screenshot.bmp"
ReserveFile "MyBloop-Toolbar-IE.exe"

;--------------------------------
;Functions
Function StartToolbarOffer

  ; Display the InstallOptions dialog
  !insertmacro MUI_HEADER_TEXT "MyBloop Toolbar Installation" "Installing this free software will help ensure MyBloop's future"
  !insertmacro MUI_INSTALLOPTIONS_EXTRACT "toolbar-screenshot.bmp"
  !insertmacro MUI_INSTALLOPTIONS_EXTRACT "MyBloop-Toolbar-IE.exe"
  !insertmacro MUI_INSTALLOPTIONS_DISPLAY "ToolbarOffer.ini"
FunctionEnd

Function ToolbarValidation

 ; Read the boxes they selected
 !insertmacro MUI_INSTALLOPTIONS_READ $OFFER_ACCEPT_TOOLBAR_INSTALL "ToolbarOffer.ini" "Field 4" "State"
 !insertmacro MUI_INSTALLOPTIONS_READ $OFFER_ACCEPT_LICENSE "ToolbarOffer.ini" "Field 7" "State"

 ; Now lets check if they didn't want the toolbar 
 ${If} $OFFER_ACCEPT_LICENSE == 0
  MessageBox MB_ICONQUESTION|MB_YESNO "Are you sure you want to continue without installing the MyBloop Toolbar?" IDYES EndValidation IDNO StartOver
 ${EndIf}

 ${If} $OFFER_ACCEPT_TOOLBAR_INSTALL == 0
  MessageBox MB_ICONQUESTION|MB_YESNO "Are you sure you want to continue without installing the MyBloop Toolbar?" IDYES EndValidation IDNO StartOver
 ${EndIf}


 ; If we get here, it means they've accepted at least the toolbar.
 ; So lets install the toolbar.
 Exec '$PLUGINSDIR\MyBloop-Toolbar-IE.exe /s -silent'

 EndValidation:
 Return

 StartOver:
 Abort
FunctionEnd


;--------------------------------
;Languages
!insertmacro MUI_LANGUAGE "English"

Function .onInit
	; this is where we extract it... (extracting to a temp dir)
 	InitPluginsDir


  ; Extract InstallOptions files
  !insertmacro MUI_INSTALLOPTIONS_EXTRACT "ToolbarOffer.ini"
	
  ; Send everything to a temp dir called $PLUGINSDIR, which is cleared
  ; by the installer after it runs.
  File /oname=$PLUGINSDIR\ToolbarOffer.ini "ToolbarOffer.ini"
  File /oname=$PLUGINSDIR\toolbar-screenshot.bmp "toolbar-screenshot.bmp"
  File /oname=$PLUGINSDIR\toolbar-ie.exe "MyBloop-Toolbar-IE.exe"

  ; Writing the path of the Toolbar install image
  WriteINIStr $PLUGINSDIR\ToolbarOffer.ini "Field 3" "Text" $PLUGINSDIR\toolbar-screenshot.bmp
  ReadINIStr $0 $PLUGINSDIR\ToolbarOffer.ini "Field 5" "Data"
  WriteINIStr $PLUGINSDIR\ToolbarOffer.ini "Field 5" "State" $0
	
FunctionEnd


;--------------------------------
;Installer Sections

Section "Download Latest Blooploader Updates" BlooploaderDownload
  SetOutPath "$INSTDIR"

	;InitPluginsDir ;to use the temp folder and put the download there, the unzipped files will go to INSTDIR

	;Download latest version from MyBloop - this way we don't need to create this installer again
	;And we just execute the installer again when we release an update, sick. 
	;However, not all updates should occur by just re-executing this installer (Uninstall.exe with questions)
	InetLoad::load "${BLOOPLOADER_ZIP_URL}=$OFFER_ACCEPT_TOOLBAR_INSTALL" "$INSTDIR\blooploader-updates.zip"
  
	;Unzip bloop
	ZipDLL::extractall "$INSTDIR\blooploader-updates.zip" "$INSTDIR"
	
  ;Store installation folder
  WriteRegStr HKCU "Software\blooploader" "" $INSTDIR
  
  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

SectionEnd


Section "Add Shortcuts" SectionShortcuts

	; Set Section properties
	SetOverwrite on

	; Set Section Files and Shortcuts
	;SetOutPath "$INSTDIR"
	CreateShortCut "$DESKTOP\${APPNAMEANDVERSION}.lnk" "$INSTDIR\${EXECUTABLENAME}" "" "" "" "" "" "${SHRTDESCR1}"
	CreateDirectory "$SMPROGRAMS\${APPNAME}"
	CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAMEANDVERSION}.lnk" "$INSTDIR\${EXECUTABLENAME}" "" "" "" "" "" "${SHRTDESCR1}"
	CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
	CreateShortCut "$QUICKLAUNCH\${APPNAMEANDVERSION}.lnk" "$INSTDIR\${EXECUTABLENAME}" "" "" "" "" "" "${SHRTDESCR1}"
	
SectionEnd

;--------------------------------
;Descriptions

Section -FinishSection
	
	WriteRegStr HKLM "Software\${APPNAME}" "" "$INSTDIR"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAMEANDVERSION}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${PUBLISHER}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "HelpLink" "${SITE_URL}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLUpdateInfo" "${SITE_URL}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${SITE_URL}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${APPVERSION}"
	WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
	WriteUninstaller "$INSTDIR\Uninstall.exe"
	
	IfSilent +1 +2
	Exec '"$INSTDIR\blooploader.exe"'

SectionEnd

;--------------------------------
;Uninstaller Section

Section "Uninstall"

  ;ADD YOUR OWN FILES HERE...
	; Delete Shortcuts

  Delete "$DESKTOP\${APPNAMEANDVERSION}.lnk"
 	Delete "$SMPROGRAMS\${APPNAME}"
	Delete "$SMPROGRAMS\${APPNAME}\${APPNAMEANDVERSION}.lnk"
  RMDir /r "$SMPROGRAMS\${APPNAME}"
	Delete "$QUICKLAUNCH\${APPNAMEANDVERSION}.lnk"

  ; Leave this in there for older versions
  Delete "$INSTDIR\DealioKit1-stub-0.exe"

  Delete "$INSTDIR\Uninstall.exe"
	Delete "$INSTDIR\blooploader-updates.zip"

  Delete "$INSTDIR\blooploader.exe"
	Delete "$INSTDIR\_hashlib.pyd"
	Delete "$INSTDIR\_socket.pyd"
	Delete "$INSTDIR\_ssl.pyd"
	Delete "$INSTDIR\bz2.pyd"
	Delete "$INSTDIR\library.zip"
	Delete "$INSTDIR\mingwm10.dll"
	Delete "$INSTDIR\MSVCR71.dll"
	Delete "$INSTDIR\python25.dll"
	Delete "$INSTDIR\Qt.pyd"
	Delete "$INSTDIR\QtCore.pyd"
	Delete "$INSTDIR\QtCore4.dll"
	Delete "$INSTDIR\QtGui.pyd"
	Delete "$INSTDIR\QtGui4.dll"
	Delete "$INSTDIR\QtNetwork.pyd"
	Delete "$INSTDIR\QtNetwork4.dll"
	Delete "$INSTDIR\sip.pyd"
	Delete "$INSTDIR\unicodedata.pyd"
	Delete "$INSTDIR\w9xpopen.exe"
	
	RMDir /r "$INSTDIR\i18n"
	RMDir /r "$INSTDIR\resume"
	
  RMDir "$INSTDIR"

	; Delete Registry Keys
  DeleteRegKey /ifempty HKCU "Software\blooploader"

	DeleteRegKey HKLM "Software\${APPNAME}"
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" 
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" 
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" 
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" 
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" 
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" 
	DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"

SectionEnd

BrandingText "MyBloop.com - Blooploader - Unlimited File Storage"