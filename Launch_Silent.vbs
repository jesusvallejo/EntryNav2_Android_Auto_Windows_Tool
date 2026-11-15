Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)
batPath = currentDir & "\Launch_Windows_Tool.bat"
WshShell.Run "cmd.exe /c """ & batPath & """", 0, False
