' 休憩ポップアップをコンソール画面なしで起動する (Windows 用)
' このファイルのショートカットをスタートアップフォルダ (Win+R → shell:startup) に置くと、
' PC にログインしたとき自動で起動します。
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
CreateObject("WScript.Shell").Run "pythonw """ & dir & "\break_popup.py""", 0, False
