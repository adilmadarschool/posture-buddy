#!/usr/bin/env python3
"""
Posture Buddy - a goofy character pops up every 30-60 minutes to say
"Hi, mind your posture!".

Windows app built with tkinter. The tray icon uses pystray + Pillow.

Run:        python posture_buddy.py
Test fast:  python posture_buddy.py --fast      (pops up every 10-20 seconds)
Test build: python posture_buddy.py --test      (pops up every 5 seconds)
Start now:  python posture_buddy.py --now
"""
import argparse
import math
import os
import queue
import random
import sys
import time
import tkinter as tk

IS_WIN = sys.platform == "win32"
APP_NAME = "PostureBuddy"

MIN_MINUTES, MAX_MINUTES = 30, 60   # random gap between visits
HOLD_SECONDS = 7.0                  # how long the character stays on screen
FULLSCREEN_RETRY_MIN = 5            # try again later if you're in a fullscreen app

W, H = 300, 330                     # character window size
KEY = "#010101"                     # colour made transparent on Windows
INK = "#2b2320"                     # outline colour

MAIN_LINE = "Hi, mind your posture!"
SHARED_LINES = [
    "Shoulders down, back tall.",
    "Unclench your jaw, too.",
    "Feet flat on the floor, please.",
    "Screen at eye level!",
    "Time to un-hunch.",
]


# --------------------------------------------------------------------------
# Drawing helpers
# --------------------------------------------------------------------------
def oval(c, x0, y0, x1, y1, fill, w=3, outline=INK):
    return c.create_oval(x0, y0, x1, y1, fill=fill, outline=outline, width=w, tags="char")


def line(c, pts, fill=INK, w=3):
    return c.create_line(*pts, fill=fill, width=w, capstyle="round",
                         joinstyle="round", tags="char")


def poly(c, pts, fill, w=3, smooth=False):
    return c.create_polygon(*pts, fill=fill, outline=INK, width=w, smooth=smooth,
                            joinstyle="round", tags="char")


def eye(c, x, y, r=9, look=(0, 0)):
    oval(c, x - r, y - r, x + r, y + r, "white", 2)
    pr = r * 0.45
    px, py = x + look[0], y + look[1]
    c.create_oval(px - pr, py - pr, px + pr, py + pr, fill=INK, outline=INK, tags="char")


def arc(c, box, start, extent, w=3, color=INK):
    return c.create_arc(*box, start=start, extent=extent, style="arc",
                        outline=color, width=w, tags="char")


def rrect_pts(x0, y0, x1, y1, r):
    return [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1,
            x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]


# --------------------------------------------------------------------------
# Characters.  Each draw function gets (canvas, cx, by, t):
#   cx = horizontal centre, by = baseline (feet) y, t = seconds since start
# --------------------------------------------------------------------------
def draw_potato(c, cx, by, t):
    b = math.sin(t * 3) * 3
    wave = math.sin(t * 6) * 10
    look = (math.sin(t * 1.3) * 2, 1)
    oval(c, cx - 42, by - 14, cx - 8, by, "#8a5f35")
    oval(c, cx + 8, by - 14, cx + 42, by, "#8a5f35")
    line(c, (cx - 60, by - 85 + b, cx - 84, by - 52 + b), "#8a5f35", 12)
    line(c, (cx + 60, by - 85 + b, cx + 86, by - 122 + b + wave), "#8a5f35", 12)
    oval(c, cx - 64, by - 164 + b, cx + 64, by - 8, "#c4955e")
    for dx, dy, r in ((-34, -44, 5), (28, -58, 6), (38, -112, 5), (-40, -126, 6), (6, -26, 4)):
        c.create_oval(cx + dx - r, by + dy + b - r, cx + dx + r, by + dy + b + r,
                      fill="#a8773f", outline="", tags="char")
    eye(c, cx - 23, by - 104 + b, 12, look)
    eye(c, cx + 23, by - 104 + b, 12, look)
    line(c, (cx - 40, by - 132 + b, cx - 12, by - 121 + b), INK, 5)   # grumpy brows
    line(c, (cx + 12, by - 121 + b, cx + 40, by - 132 + b), INK, 5)
    arc(c, (cx - 18, by - 78 + b, cx + 18, by - 56 + b), 20, 140, 4)   # frown


def draw_cactus(c, cx, by, t):
    b = abs(math.sin(t * 2.5)) * 4
    wave = math.sin(t * 6) * 10
    look = (math.sin(t * 1.1) * 2, 1)
    # pot
    poly(c, (cx - 38, by - 40, cx + 38, by - 40, cx + 30, by, cx - 30, by), "#c8643c")
    c.create_rectangle(cx - 46, by - 54, cx + 46, by - 38, fill="#d9774a",
                       outline=INK, width=3, tags="char")
    arms = [((cx - 28, by - 92 - b, cx - 58, by - 92 - b, cx - 58, by - 128 - b)),
            ((cx + 28, by - 98 - b, cx + 58, by - 98 - b, cx + 58, by - 134 - b - wave))]
    body = (cx, by - 56, cx, by - 138 - b)
    for pts in arms:                       # outlines first, fills second -> seamless union
        line(c, pts, INK, 36)
    line(c, body, INK, 78)
    for pts in arms:
        line(c, pts, "#4fa860", 28)
    line(c, body, "#4fa860", 70)
    for x, y in ((-26, -70), (26, -76), (-20, -120), (22, -118), (0, -150)):
        line(c, (cx + x, by + y - b, cx + x + (4 if x > 0 else -4), by + y - b - 6), INK, 2)
    # flower
    fy = by - 176 - b
    for k in range(5):
        a = k * 2 * math.pi / 5 + t
        fx, fyy = cx + 11 * math.cos(a), fy + 11 * math.sin(a)
        c.create_oval(fx - 7, fyy - 7, fx + 7, fyy + 7, fill="#ff8fb1", outline=INK,
                      width=2, tags="char")
    oval(c, cx - 6, fy - 6, cx + 6, fy + 6, "#ffd23f", 2)
    # face
    eye(c, cx - 15, by - 104 - b, 8, look)
    eye(c, cx + 15, by - 104 - b, 8, look)
    arc(c, (cx - 10, by - 96 - b, cx + 10, by - 78 - b), 200, 140, 3)
    c.create_oval(cx - 30, by - 90 - b, cx - 20, by - 82 - b, fill="#ff9aa8", outline="", tags="char")
    c.create_oval(cx + 20, by - 90 - b, cx + 30, by - 82 - b, fill="#ff9aa8", outline="", tags="char")


def draw_ghost(c, cx, by, t):
    f = math.sin(t * 2.2) * 8
    cy, r = by - 108 + f, 56
    # held "spine"
    for i in range(6):
        x = cx - r - 26 + math.sin(t * 4 + i) * 4
        y = cy - 18 + i * 14
        oval(c, x - 9, y - 6, x + 9, y + 6, "#eadfc4", 2)
    # body
    pts = []
    for a in range(180, 361, 10):
        pts += [cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))]
    n = 7
    for i in range(n * 2 + 1):
        x = cx + r - (2 * r) * i / (2 * n)
        y = cy + 64 + (8 if i % 2 == 0 else -4) + math.sin(t * 5 + i) * 2
        pts += [x, y]
    poly(c, pts, "#f1f3ff")
    oval(c, cx - r - 12, cy + 4, cx - r + 14, cy + 28, "#f1f3ff")   # arm holding spine
    # stethoscope
    arc(c, (cx - 34, cy + 6, cx + 34, cy + 62), 205, 130, 5, "#555a66")
    oval(c, cx - 7, cy + 52, cx + 7, cy + 66, "#c7ccd6", 2)
    # glasses + eyes
    look = (math.sin(t * 1.5) * 2, 2)
    for sx in (-1, 1):
        ex = cx + sx * 21
        oval(c, ex - 15, cy - 24, ex + 15, cy + 6, "white", 3)
        c.create_oval(ex - 4 + look[0], cy - 13 + look[1], ex + 4 + look[0], cy - 5 + look[1],
                      fill=INK, outline=INK, tags="char")
    line(c, (cx - 6, cy - 10, cx + 6, cy - 10), INK, 3)
    line(c, (cx - 34, cy - 36, cx - 10, cy - 30), INK, 4)   # disapproving brows
    line(c, (cx + 10, cy - 30, cx + 34, cy - 36), INK, 4)
    line(c, (cx - 9, cy + 24, cx + 9, cy + 24), INK, 3)     # flat mouth


def draw_pigeon(c, cx, by, t):
    hb = math.sin(t * 7) * 5          # the famous pigeon head-bob
    b = abs(math.sin(t * 3.5)) * 2
    for x in (-16, 12):
        line(c, (cx + x, by - 34, cx + x, by - 4), "#e07a8f", 4)
        line(c, (cx + x - 8, by - 2, cx + x + 8, by - 2), "#e07a8f", 4)
    poly(c, (cx + 36, by - 84 + b, cx + 82, by - 62 + b, cx + 72, by - 44 + b, cx + 30, by - 50 + b), "#7c879f")
    oval(c, cx - 64, by - 112 + b, cx + 52, by - 28 + b, "#9aa5bd")
    oval(c, cx - 28, by - 98 + b, cx + 34, by - 52 + b, "#8793ad", 2)   # wing
    oval(c, cx - 66 + hb * .5, by - 124 + b, cx - 28 + hb * .5, by - 88 + b, "#6fb596", 0, "")  # neck sheen
    hx, hy = cx - 48 + hb, by - 132 + b
    oval(c, hx - 25, hy - 25, hx + 25, hy + 25, "#7d89a6")
    poly(c, (hx - 22, hy + 2, hx - 48, hy + 10, hx - 22, hy + 16), "#f0a030")  # beak
    oval(c, hx - 15, hy - 12, hx - 1, hy + 2, "#ffb347", 2)
    c.create_oval(hx - 11, hy - 8, hx - 5, hy - 2, fill=INK, outline=INK, tags="char")
    # clipboard
    c.create_rectangle(cx + 6, by - 106, cx + 62, by - 38, fill="#b5834a", outline=INK, width=3, tags="char")
    c.create_rectangle(cx + 12, by - 98, cx + 56, by - 44, fill="white", outline=INK, width=2, tags="char")
    c.create_rectangle(cx + 25, by - 112, cx + 43, by - 102, fill="#9aa0aa", outline=INK, width=2, tags="char")
    for k, wlen in enumerate((30, 22, 28)):
        line(c, (cx + 17, by - 86 + k * 11, cx + 17 + wlen, by - 86 + k * 11), "#7a7f8c", 2)
    line(c, (cx + 18, by - 54, cx + 24, by - 48, cx + 38, by - 62), "#d64545", 3)   # red mark
    oval(c, cx - 6, by - 78 + b, cx + 14, by - 56 + b, "#8793ad", 2)   # wing holding it


def draw_banana(c, cx, by, t):
    sw = math.sin(t * 2.5) * 3
    ax, ay, R = cx + 26, by - 90, 66
    box = (ax - R, ay - R, ax + R, ay + R)
    top = (ax + R * math.cos(math.radians(105)), ay - R * math.sin(math.radians(105)))
    bot = (ax + R * math.cos(math.radians(255)), ay - R * math.sin(math.radians(255)))
    line(c, (top[0], top[1] - 4, top[0] + 8, top[1] - 24), INK, 18)
    line(c, (top[0], top[1] - 4, top[0] + 8, top[1] - 24), "#7a8a3a", 11)
    arc(c, box, 105, 150, 62, INK)
    arc(c, box, 105, 150, 55, "#f6d34a")
    oval(c, bot[0] - 9, bot[1] - 4, bot[0] + 9, bot[1] + 12, "#5a4020", 2)
    # tiny legs
    line(c, (bot[0] - 4, bot[1] + 10, bot[0] - 10, by - 2), INK, 4)
    line(c, (bot[0] + 6, bot[1] + 10, bot[0] + 12, by - 2), INK, 4)
    # face
    look = (math.sin(t * 1.4) * 2, 1)
    fx, fy = cx - 40 + sw, by - 90
    eye(c, fx - 12, fy, 8, look)
    eye(c, fx + 12, fy, 8, look)
    oval(c, fx + 1, fy - 13, fx + 25, fy + 11, "", 3, INK)          # monocle
    line(c, (fx + 25, fy + 4, fx + 34, fy + 30), "#999", 2)
    arc(c, (fx - 8, fy + 8, fx + 8, fy + 22), 200, 140, 3)
    line(c, (fx - 15, fy - 16, fx - 3, fy - 13), INK, 3)             # raised brow


CHARACTERS = [
    ("Spud the potato", draw_potato,
     ["Even a potato sits straighter than you.", "Spud is unimpressed. Sit up."]),
    ("Prickles the cactus", draw_cactus,
     ["Be prickly, not slouchy!", "Stand tall. Photosynthesize your posture."]),
    ("Dr. Boo the ghost", draw_ghost,
     ["Your spine called. It's upset.", "I'm a spectral chiropractor. Sit up!"]),
    ("Pidge the pigeon", draw_pigeon,
     ["Coo! Official posture inspection.", "Chin up, shoulders back. Coo."]),
    ("Sir Curve the banana", draw_banana,
     ["I'm curved. You don't have to be.", "Don't go bananas, just sit up straight."]),
]


def pick_line(own_lines):
    r = random.random()
    if r < 0.45:
        return MAIN_LINE
    if r < 0.75:
        return random.choice(own_lines)
    return random.choice(SHARED_LINES)


# --------------------------------------------------------------------------
# Windows helpers
# --------------------------------------------------------------------------
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def launch_command():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --quiet'
    exe = sys.executable
    pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    if os.path.exists(pyw):
        exe = pyw
    return f'"{exe}" "{os.path.abspath(__file__)}" --quiet'


def autostart_enabled():
    if not IS_WIN:
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, APP_NAME)
            return True
    except OSError:
        return False


def set_autostart(on):
    if not IS_WIN:
        return
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if on:
            winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, launch_command())
        else:
            try:
                winreg.DeleteValue(k, APP_NAME)
            except OSError:
                pass


def single_instance():
    """Return False if another copy is already running (Windows only)."""
    if not IS_WIN:
        return True
    import ctypes
    ctypes.windll.kernel32.CreateMutexW(None, False, APP_NAME + "SingleInstance")
    return ctypes.windll.kernel32.GetLastError() != 183   # ERROR_ALREADY_EXISTS


def foreground_is_fullscreen():
    if not IS_WIN:
        return False
    import ctypes
    from ctypes import wintypes
    u = ctypes.windll.user32
    hwnd = u.GetForegroundWindow()
    if not hwnd:
        return False
    cls = ctypes.create_unicode_buffer(64)
    u.GetClassNameW(hwnd, cls, 64)
    if cls.value in ("Progman", "WorkerW", "Shell_TrayWnd"):
        return False
    r = wintypes.RECT()
    u.GetWindowRect(hwnd, ctypes.byref(r))
    return (r.left <= 0 and r.top <= 0 and
            r.right >= u.GetSystemMetrics(0) and r.bottom >= u.GetSystemMetrics(1))


def work_area(root):
    if IS_WIN:
        import ctypes
        from ctypes import wintypes
        r = wintypes.RECT()
        if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(r), 0):  # SPI_GETWORKAREA
            return r.left, r.top, r.right, r.bottom
    return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()


# --------------------------------------------------------------------------
# The app
# --------------------------------------------------------------------------
class App:
    def __init__(self, args):
        self.args = args
        self.root = tk.Tk()
        self.root.withdraw()
        self.q = queue.Queue()
        self.paused = False
        self.win = None
        self.canvas = None
        self.timer = None
        self.last_char = None
        self.icon = None

        if args.test:
            self.lo = self.hi = 5                # test build: every 5 seconds
        elif args.fast:
            self.lo, self.hi = 10, 20            # seconds
        else:
            self.lo, self.hi = MIN_MINUTES * 60, MAX_MINUTES * 60

        self.start_tray()
        self.root.after(200, self.poll)
        if args.now or not args.quiet:
            self.root.after(1500, self.show)
        self.schedule_next()

    # ---- tray ---------------------------------------------------------
    def start_tray(self):
        try:
            import pystray
            from PIL import Image, ImageDraw
        except ImportError:
            print("pystray/Pillow not installed - running without a tray icon "
                  "(Ctrl+C in the console to quit).")
            return
        img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.ellipse((4, 6, 60, 62), fill="#c4955e", outline="#2b2320", width=3)
        d.ellipse((18, 24, 28, 36), fill="white", outline="#2b2320")
        d.ellipse((36, 24, 46, 36), fill="white", outline="#2b2320")
        d.line((14, 20, 28, 25), fill="#2b2320", width=3)
        d.line((36, 25, 50, 20), fill="#2b2320", width=3)
        d.arc((24, 42, 40, 54), 200, 340, fill="#2b2320", width=3)

        items = [
            pystray.MenuItem("Say hi now", lambda: self.q.put("show"), default=True),
            pystray.MenuItem("Pause", lambda: self.q.put("pause"), checked=lambda i: self.paused),
        ]
        if IS_WIN:
            items.append(pystray.MenuItem("Start with Windows", lambda: self.q.put("autostart"),
                                          checked=lambda i: autostart_enabled()))
        items.append(pystray.MenuItem("Quit", lambda: self.q.put("quit")))
        self.icon = pystray.Icon(APP_NAME, img, "Posture Buddy" + (" (TEST)" if self.args.test else ""), pystray.Menu(*items))
        self.icon.run_detached()

    def poll(self):
        try:
            while True:
                cmd = self.q.get_nowait()
                if cmd == "show":
                    self.show()
                elif cmd == "pause":
                    self.toggle_pause()
                elif cmd == "autostart":
                    set_autostart(not autostart_enabled())
                elif cmd == "quit":
                    self.quit()
                    return
        except queue.Empty:
            pass
        self.root.after(200, self.poll)

    def quit(self):
        if self.icon:
            self.icon.stop()
        self.root.destroy()

    # ---- scheduling ---------------------------------------------------
    def schedule_next(self, seconds=None):
        if self.timer:
            self.root.after_cancel(self.timer)
            self.timer = None
        if self.paused:
            return
        if seconds is None:
            seconds = random.uniform(self.lo, self.hi)
        self.timer = self.root.after(int(seconds * 1000), self.on_timer)

    def toggle_pause(self):
        self.paused = not self.paused
        self.schedule_next()

    def on_timer(self):
        self.timer = None
        if self.win is not None:
            self.schedule_next(1 if self.args.test else 60)
        elif foreground_is_fullscreen():
            self.schedule_next(FULLSCREEN_RETRY_MIN * 60)
        else:
            self.show()
            self.schedule_next()

    # ---- the character ------------------------------------------------
    def show(self):
        if self.win is not None:
            return
        choices = [ch for ch in CHARACTERS if ch[0] != self.last_char] or CHARACTERS
        name, self.draw, lines = random.choice(choices)
        self.last_char = name
        self.text = pick_line(lines)

        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.configure(bg=KEY)
        try:
            win.attributes("-transparentcolor", KEY)
        except tk.TclError:
            pass
        c = tk.Canvas(win, width=W, height=H, bg=KEY, highlightthickness=0, bd=0)
        c.pack()
        c.bind("<Button-1>", lambda e: self.dismiss())
        c.configure(cursor="hand2")

        left, top, right, bottom = work_area(self.root)
        self.tx = right - W - 12
        self.ty = bottom - H - 4
        self.sx = right + 4                       # starts just off the right edge
        win.geometry(f"{W}x{H}+{self.sx}+{self.ty}")

        self.win, self.canvas = win, c
        self.phase, self.phase_start, self.t0 = "in", time.time(), time.time()
        self.tick()

    def dismiss(self):
        if self.win is not None and self.phase in ("in", "hold"):
            self.phase, self.phase_start = "out", time.time()

    def tick(self):
        if self.win is None:
            return
        now = time.time()
        c = self.canvas
        c.delete("char")
        self.draw(c, W // 2, H - 8, now - self.t0)
        c.tag_lower("char")

        x = self.tx
        if self.phase == "in":
            p = min(1.0, (now - self.phase_start) / 0.6)
            x = self.sx + (self.tx - self.sx) * (1 - (1 - p) ** 3)
            if p >= 1:
                self.phase, self.phase_start = "hold", now
                self.draw_bubble(self.text)
        elif self.phase == "hold":
            if now - self.phase_start > (3.0 if self.args.test else HOLD_SECONDS):
                self.phase, self.phase_start = "out", now
        else:
            p = min(1.0, (now - self.phase_start) / 0.5)
            x = self.tx + (self.sx - self.tx) * (p ** 3)
            if p >= 1:
                self.win.destroy()
                self.win = self.canvas = None
                return
        self.win.geometry(f"+{int(x)}+{self.ty}")
        self.root.after(33, self.tick)

    def draw_bubble(self, text):
        c = self.canvas
        cx = W // 2
        tid = c.create_text(cx, 108, text=text, width=230, anchor="s", justify="center",
                            font=("Segoe UI", 13, "bold"), fill=INK, tags="bubble")
        x0, y0, x1, y1 = c.bbox(tid)
        pad = 12
        x0, y0, x1, y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
        c.create_polygon(*rrect_pts(x0, y0, x1, y1, 16), smooth=True, fill="white",
                         outline=INK, width=3, tags="bubble")
        c.create_polygon(cx - 12, y1 - 1, cx + 12, y1 - 1, cx + 2, y1 + 20,
                         fill="white", outline=INK, width=3, joinstyle="round", tags="bubble")
        c.create_line(cx - 10, y1 - 1, cx + 10, y1 - 1, fill="white", width=5, tags="bubble")
        c.tag_raise(tid)

    def run(self):
        self.root.mainloop()


def main():
    p = argparse.ArgumentParser(description="Posture Buddy")
    p.add_argument("--fast", action="store_true", help="appear every 10-20 seconds (for testing)")
    p.add_argument("--test", action="store_true", help="test build: appear every 5 seconds")
    p.add_argument("--now", action="store_true", help="appear right after launch")
    p.add_argument("--quiet", action="store_true", help="don't greet on launch (used for autostart)")
    args = p.parse_args()
    global APP_NAME
    if args.test:
        APP_NAME = "PostureBuddyTest"
    if not single_instance():
        return
    App(args).run()


if __name__ == "__main__":
    main()
