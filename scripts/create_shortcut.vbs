Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "..\dist\AntaresWebServer_shortcut.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
    oLink.TargetPath = "%CD%\..\dist\AntaresWebServer\AntaresWebServer.exe"
    oLink.IconLocation = "..\webapp\favicon.ico"
oLink.Save