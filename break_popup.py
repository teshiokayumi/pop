#!/usr/bin/env python3
"""休憩お知らせポップアップ

決まった時刻になると、デスクトップの最前面にポップアップを表示して休憩を知らせる。
Python 標準ライブラリ (tkinter) だけで動くので、追加インストールは不要。

使い方:
    python break_popup.py          # 常駐して、指定時刻にポップアップ
    python break_popup.py --test   # すぐにポップアップを1回表示して動作確認
"""

from __future__ import annotations

import argparse
import datetime as dt
import random
import tkinter as tk
from pathlib import Path

# ポップアップを出す時刻 (時, 分, 表示するメッセージ)
SCHEDULE = [
    (11, 0, "11:00 です。少し休憩しましょう ☕"),
    (12, 10, "12:10 です。お昼休憩の時間です 🍱"),
]

# ポップアップに表示する PNG 画像を置くフォルダ。
# 既定はこのスクリプトと同じフォルダ。別の場所にしたい場合は例のように書き換える。
#   IMAGE_DIR = Path(r"C:\Users\User\OneDrive\デスクトップ\desktop-popup-break")
IMAGE_DIR = Path(__file__).resolve().parent

# 画像が大きすぎる場合は、画面のこの割合に収まるよう縮小する
MAX_IMAGE_SCREEN_RATIO = 0.6

# PC がスリープ等で時刻ちょうどに動いていなかった場合でも、
# この分数以内に復帰すればポップアップを出す
GRACE_MINUTES = 30

# 時刻をチェックする間隔 (ミリ秒)
CHECK_INTERVAL_MS = 10_000


class BreakNotifier:
    def __init__(self, root: tk.Tk):
        self.root = root
        # 当日すでに表示した (日付, 時, 分) を記録して二重表示を防ぐ
        self.shown: set[tuple[dt.date, int, int]] = set()
        self._skip_past_times()

    def _skip_past_times(self):
        """起動時点で猶予時間も過ぎている時刻は、今日の分を表示済み扱いにする。"""
        now = dt.datetime.now()
        for hour, minute, _ in SCHEDULE:
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if now >= target + dt.timedelta(minutes=GRACE_MINUTES):
                self.shown.add((now.date(), hour, minute))

    def check(self):
        now = dt.datetime.now()
        for hour, minute, message in SCHEDULE:
            key = (now.date(), hour, minute)
            if key in self.shown:
                continue
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now < target + dt.timedelta(minutes=GRACE_MINUTES):
                self.shown.add(key)
                show_popup(self.root, message)
        self.root.after(CHECK_INTERVAL_MS, self.check)


def pick_image() -> Path | None:
    """IMAGE_DIR にある PNG を1枚ランダムに選ぶ。無ければ None。"""
    try:
        pngs = sorted(p for p in IMAGE_DIR.iterdir() if p.suffix.lower() == ".png")
    except OSError:
        return None
    return random.choice(pngs) if pngs else None


def load_image(win: tk.Toplevel, path: Path) -> tk.PhotoImage | None:
    """PNG を読み込み、画面に収まらなければ整数倍で縮小する。"""
    try:
        img = tk.PhotoImage(master=win, file=str(path))
    except tk.TclError:
        return None
    max_w = int(win.winfo_screenwidth() * MAX_IMAGE_SCREEN_RATIO)
    max_h = int(win.winfo_screenheight() * MAX_IMAGE_SCREEN_RATIO)
    factor = max(-(-img.width() // max_w), -(-img.height() // max_h), 1)
    if factor > 1:
        img = img.subsample(factor, factor)
    return img


def show_popup(root: tk.Tk, message: str):
    win = tk.Toplevel(root)
    win.title("休憩のお知らせ")
    win.configure(bg="#fff8e1", padx=40, pady=30)
    win.resizable(False, False)

    image_path = pick_image()
    if image_path is not None:
        img = load_image(win, image_path)
        if img is not None:
            label = tk.Label(win, image=img, bg="#fff8e1")
            label.image = img  # 参照を保持しないと画像が消える
            label.pack(pady=(0, 15))

    tk.Label(
        win, text="休憩タイム", font=("", 28, "bold"), bg="#fff8e1", fg="#e65100"
    ).pack(pady=(0, 10))
    tk.Label(win, text=message, font=("", 16), bg="#fff8e1", fg="#333333").pack(
        pady=(0, 20)
    )
    tk.Label(
        win,
        text=dt.datetime.now().strftime("%Y/%m/%d %H:%M"),
        font=("", 11),
        bg="#fff8e1",
        fg="#888888",
    ).pack(pady=(0, 20))

    btn = tk.Button(win, text="OK", font=("", 14), width=10, command=win.destroy)
    btn.pack()
    win.bind("<Return>", lambda _e: win.destroy())
    win.bind("<Escape>", lambda _e: win.destroy())

    # 画面中央に配置
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    x = (win.winfo_screenwidth() - w) // 2
    y = (win.winfo_screenheight() - h) // 3
    win.geometry(f"+{x}+{y}")

    # 他のウィンドウより前面に出して気付かせる
    win.attributes("-topmost", True)
    win.deiconify()
    win.lift()
    win.focus_force()
    btn.focus_set()
    win.bell()


def main():
    parser = argparse.ArgumentParser(description="休憩お知らせポップアップ")
    parser.add_argument(
        "--test", action="store_true", help="すぐにポップアップを表示して終了する"
    )
    args = parser.parse_args()

    root = tk.Tk()
    root.withdraw()  # メインウィンドウは隠して常駐

    if args.test:
        show_popup(root, "これはテスト表示です。")
        # テスト用ポップアップを閉じたら終了
        root.after(500, lambda: _quit_when_closed(root))
    else:
        BreakNotifier(root).check()

    root.mainloop()


def _quit_when_closed(root: tk.Tk):
    if root.winfo_children():
        root.after(500, lambda: _quit_when_closed(root))
    else:
        root.destroy()


if __name__ == "__main__":
    main()
