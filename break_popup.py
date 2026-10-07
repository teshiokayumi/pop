#!/usr/bin/env python3
"""休憩お知らせポップアップ

決まった時刻になると、デスクトップの最前面にポップアップを表示して休憩を知らせる。
Python 標準ライブラリ (tkinter) だけで動くので、追加インストールは不要。

使い方:
    python break_popup.py          # 常駐して、指定時刻にポップアップ
    python break_popup.py --test   # すぐにポップアップを1回表示して動作確認

pythonw で動かすとエラーが画面に出ないので、動作状況は同じフォルダの
break_popup.log に記録する。画像が出ないときはこのログを見る。
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import random
import sys
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

# 画像はこの大きさ (幅, 高さ ピクセル) に収まるよう縮小する
MAX_IMAGE_SIZE = (360, 270)

# 表示する画像の拡張子 (PNG 以外は Pillow が入っている場合のみ読める)
IMAGE_SUFFIXES = {".png", ".gif", ".jpg", ".jpeg"}

LOG_FILE = Path(__file__).resolve().parent / "break_popup.log"

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
    """IMAGE_DIR にある画像を1枚ランダムに選ぶ。無ければ None。"""
    try:
        images = sorted(
            p for p in IMAGE_DIR.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES
        )
    except OSError:
        logging.exception("画像フォルダを開けません: %s", IMAGE_DIR)
        return None
    if not images:
        logging.warning("画像が見つかりません: %s", IMAGE_DIR)
        return None
    return random.choice(images)


def load_image(win: tk.Toplevel, path: Path):
    """画像を読み込み、MAX_IMAGE_SIZE に収まるよう縮小する。失敗時は None。

    Pillow があればそれで読み込む (どんな PNG/JPEG でも読めて、なめらかに縮小できる)。
    無ければ tkinter 標準の PhotoImage で読み込み、整数分の1に縮小する。
    """
    max_w, max_h = MAX_IMAGE_SIZE
    try:
        from PIL import Image, ImageTk
    except ImportError:
        pass
    else:
        try:
            with Image.open(path) as src:
                src.thumbnail((max_w, max_h), Image.LANCZOS)
                img = ImageTk.PhotoImage(src, master=win)
            logging.info("画像を表示 (Pillow): %s", path)
            return img
        except Exception:
            logging.exception("Pillow で画像を読めません: %s", path)
            return None

    try:
        img = tk.PhotoImage(master=win, file=str(path))
    except tk.TclError:
        logging.exception(
            "画像を読めません: %s (pip install pillow で読めるようになる場合があります)",
            path,
        )
        return None
    factor = max(-(-img.width() // max_w), -(-img.height() // max_h), 1)
    if factor > 1:
        img = img.subsample(factor, factor)
    logging.info(
        "画像を表示 (tkinter): %s 1/%d に縮小 → %dx%d",
        path, factor, img.width(), img.height(),
    )
    return img


def show_popup(root: tk.Tk, message: str):
    win = tk.Toplevel(root)
    win.title("休憩のお知らせ")
    win.configure(bg="#fff8e1", padx=24, pady=16)
    win.resizable(False, False)

    image_path = pick_image()
    if image_path is not None:
        img = load_image(win, image_path)
        if img is not None:
            label = tk.Label(win, image=img, bg="#fff8e1")
            # 参照を保持しないと画像がガベージコレクトされて空白になる
            label.image = img
            win.image = img
            label.pack(pady=(0, 10))

    tk.Label(
        win, text="休憩タイム", font=("", 18, "bold"), bg="#fff8e1", fg="#e65100"
    ).pack(pady=(0, 6))
    tk.Label(win, text=message, font=("", 12), bg="#fff8e1", fg="#333333").pack(
        pady=(0, 6)
    )
    tk.Label(
        win,
        text=dt.datetime.now().strftime("%Y/%m/%d %H:%M"),
        font=("", 9),
        bg="#fff8e1",
        fg="#888888",
    ).pack(pady=(0, 10))

    btn = tk.Button(win, text="OK", font=("", 11), width=8, command=win.destroy)
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


def enable_windows_dpi_awareness():
    """Windows の拡大表示 (125%, 150% など) で画面がぼやけて巨大化するのを防ぐ。"""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def main():
    logging.basicConfig(
        filename=LOG_FILE,
        filemode="w",
        encoding="utf-8",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    logging.info("起動: python %s / 画像フォルダ %s", sys.version.split()[0], IMAGE_DIR)

    parser = argparse.ArgumentParser(description="休憩お知らせポップアップ")
    parser.add_argument(
        "--test", action="store_true", help="すぐにポップアップを表示して終了する"
    )
    args = parser.parse_args()

    enable_windows_dpi_awareness()
    root = tk.Tk()
    logging.info("Tk %s", root.tk.call("info", "patchlevel"))
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
