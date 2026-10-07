# 休憩お知らせポップアップ

ローカル PC で常駐し、**午前 11:00** と **午後 12:10** にデスクトップの最前面へポップアップを表示して休憩に気付かせる小さなツールです。

- Python 3.9 以上の標準ライブラリ (tkinter) のみで動作。追加インストール不要
- ポップアップは常に最前面・画面中央に表示され、通知音が鳴ります
- 「OK」ボタン / Enter / Esc で閉じられます
- スリープ等で時刻ちょうどに PC が動いていなくても、30 分以内に復帰すれば表示します

## 動作確認

```sh
python break_popup.py --test   # すぐにポップアップを1回表示
```

## 起動

```sh
python break_popup.py          # 常駐して 11:00 と 12:10 に表示
```

## ログイン時に自動起動する

### Windows

1. [python.org](https://www.python.org/) の Python をインストール (tkinter 同梱)
2. `start_windows.vbs` を右クリック → 「ショートカットの作成」
3. `Win + R` → `shell:startup` で開くフォルダに、そのショートカットを移動

次回ログインから、コンソール画面なしで裏で動きます。すぐ起動したい場合は `start_windows.vbs` をダブルクリック。
止めるときはタスクマネージャーで `pythonw.exe` を終了してください。

### macOS

`~/Library/LaunchAgents/com.local.breakpopup.plist` を作成 (パスは自分の環境に合わせて変更):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.local.breakpopup</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/local/bin/python3</string>
    <string>/Users/あなた/pop/break_popup.py</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict>
</plist>
```

```sh
launchctl load ~/Library/LaunchAgents/com.local.breakpopup.plist
```

### Linux (GNOME / KDE など)

tkinter が無い場合は `sudo apt install python3-tk` などで導入し、
`~/.config/autostart/break-popup.desktop` を作成:

```ini
[Desktop Entry]
Type=Application
Name=Break Popup
Exec=python3 /home/あなた/pop/break_popup.py
X-GNOME-Autostart-enabled=true
```

## 時刻やメッセージを変える

`break_popup.py` 冒頭の `SCHEDULE` を編集します。

```python
SCHEDULE = [
    (11, 0, "11:00 です。少し休憩しましょう ☕"),
    (12, 10, "12:10 です。お昼休憩の時間です 🍱"),
    (15, 0, "15:00 です。おやつ休憩 🍪"),  # 追加例
]
```
