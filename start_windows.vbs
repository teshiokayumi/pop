Option Explicit

' Run break_popup.py in this folder without a console window (Windows).
' Put a shortcut to this file in the Startup folder (Win+R -> shell:startup)
' to start it automatically at logon.

Dim pos, dir, shell
pos = InStrRev(WScript.ScriptFullName, "\")
dir = Left(WScript.ScriptFullName, pos)

Set shell = CreateObject("WScript.Shell")
shell.Run "pythonw """ & dir & "break_popup.py""", 0, False
