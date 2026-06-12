"""
Local Swagger UI Viewer
Pure stdlib — requires only Python 3.10+ (tkinter is bundled with CPython).
"""

import os
import shutil
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

BASE_DIR = Path(__file__).parent

# ── colours ──────────────────────────────────────────────────────────────────
BG       = "#121212"
SURFACE  = "#1e1e1e"
TEXT     = "#e0e0e0"
MUTED    = "#888888"
BLUE     = "#1f6feb"
BLUE_HVR = "#388bfd"
RED      = "#d73a49"
RED_HVR  = "#f85149"
BORDER   = "#333333"


# ── server ────────────────────────────────────────────────────────────────────
class SwaggerServer:
    """Tiny HTTP server that serves BASE_DIR so Swagger UI can load its assets."""

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self._httpd: TCPServer | None = None

    # serve files from BASE_DIR regardless of the working directory
    def _make_handler(self):
        base = str(BASE_DIR)

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=base, **kwargs)

            # silence request log in the terminal
            def log_message(self, fmt, *args):  # noqa: D102
                pass

        return Handler

    def start(self):
        TCPServer.allow_reuse_address = True
        self._httpd = TCPServer((self.host, self.port), self._make_handler())
        threading.Thread(target=self._httpd.serve_forever, daemon=True).start()

    def stop(self):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None


# ── GUI ───────────────────────────────────────────────────────────────────────
class App:
    def __init__(self):
        self.yaml_path: Path | None = None
        self.server:    SwaggerServer | None = None
        self.running = False

        self.root = tk.Tk()
        self.root.title("swagger-local-viewer")
        self.root.geometry("440x230")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self._build_ui()

    # ── widget helpers ────────────────────────────────────────────────────────
    def _label(self, parent, text="", fg=TEXT, **kw) -> tk.Label:
        return tk.Label(parent, text=text, bg=BG, fg=fg,
                        font=("Segoe UI", 10), **kw)

    def _entry(self, parent, textvariable, width=14) -> tk.Entry:
        return tk.Entry(parent, textvariable=textvariable, width=width,
                        bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                        relief="flat", highlightthickness=1,
                        highlightbackground=BORDER, highlightcolor=BLUE)

    def _spinbox(self, parent, textvariable, from_, to, width=8) -> tk.Spinbox:
        return tk.Spinbox(parent, textvariable=textvariable,
                          from_=from_, to=to, width=width,
                          bg=SURFACE, fg=TEXT, insertbackground=TEXT,
                          buttonbackground=SURFACE, relief="flat",
                          highlightthickness=1, highlightbackground=BORDER,
                          highlightcolor=BLUE)

    def _button(self, parent, text, command, bg=BLUE, hover=BLUE_HVR,
                width=14) -> tk.Button:
        btn = tk.Button(parent, text=text, command=command,
                        bg=bg, fg="white", activebackground=hover,
                        activeforeground="white", relief="flat",
                        font=("Segoe UI", 10, "bold"), width=width,
                        cursor="hand2", bd=0)
        btn.bind("<Enter>", lambda _: btn.configure(bg=hover))
        btn.bind("<Leave>", lambda _: btn.configure(bg=btn._bg_normal))
        btn._bg_normal = bg
        return btn

    # ── layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        pad = {"padx": 20}

        # status bar at the top
        self.status_var = tk.StringVar(value="Select an OpenAPI YAML / JSON file")
        self._label(self.root, textvariable=self.status_var,  # type: ignore[arg-type]
                    fg=MUTED, wraplength=400).pack(pady=(18, 4), **pad)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill="x", padx=20, pady=4)

        # IP + Port row
        row1 = tk.Frame(self.root, bg=BG)
        row1.pack(pady=8, **pad)

        self._label(row1, "Host:").pack(side="left")
        self.ip_var = tk.StringVar(value="127.0.0.1")
        self._entry(row1, self.ip_var, width=15).pack(side="left", padx=(4, 16))

        self._label(row1, "Port:").pack(side="left")
        self.port_var = tk.IntVar(value=8000)
        self._spinbox(row1, self.port_var, 1024, 65535).pack(side="left", padx=(4, 0))

        # Buttons row
        row2 = tk.Frame(self.root, bg=BG)
        row2.pack(pady=14, **pad)

        self.pick_btn = self._button(row2, "📂  Select File",
                                     self.pick_file, width=16)
        self.pick_btn.pack(side="left", padx=(0, 10))

        self.toggle_btn = self._button(row2, "▶  Start",
                                       self.toggle_server, width=16)
        self.toggle_btn.pack(side="left")

    # ── actions ───────────────────────────────────────────────────────────────
    def pick_file(self):
        path = filedialog.askopenfilename(
            title="Select OpenAPI file",
            filetypes=[
                ("OpenAPI files", "*.yaml *.yml *.json"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self.yaml_path = Path(path)
            self.status_var.set(f"📄  {self.yaml_path.name}")

    def toggle_server(self):
        if self.running:
            self._stop()
        else:
            self._start()

    def _start(self):
        if not self.yaml_path:
            messagebox.showwarning("No file selected",
                                   "Please select an OpenAPI YAML/JSON file first.")
            return

        host = self.ip_var.get().strip()
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Invalid port", "Port must be a number.")
            return

        try:
            # copy spec into BASE_DIR so the server can always find it as /openapi.yaml
            dest = BASE_DIR / "openapi.yaml"
            if self.yaml_path.resolve() != dest.resolve():
                shutil.copy(self.yaml_path, dest)

            self.server = SwaggerServer(host, port)
            self.server.start()
        except OSError as exc:
            messagebox.showerror("Server error", str(exc))
            self.status_var.set(f"❌  {exc}")
            return

        url = f"http://{host}:{port}"
        webbrowser.open(url)

        self.running = True
        self.pick_btn.configure(state="disabled", bg=BORDER)
        self.pick_btn._bg_normal = BORDER
        self._set_stop_style()
        self.status_var.set(f"🟢  Running →  {url}")

    def _stop(self):
        if self.server:
            self.server.stop()
            self.server = None

        self.running = False
        self.pick_btn.configure(state="normal", bg=BLUE)
        self.pick_btn._bg_normal = BLUE
        self._set_start_style()
        self.status_var.set("🔴  Server stopped")

    def _set_stop_style(self):
        self.toggle_btn.configure(text="■  Stop", bg=RED, activebackground=RED_HVR)
        self.toggle_btn._bg_normal = RED

    def _set_start_style(self):
        self.toggle_btn.configure(text="▶  Start", bg=BLUE, activebackground=BLUE_HVR)
        self.toggle_btn._bg_normal = BLUE

    # ── run ───────────────────────────────────────────────────────────────────
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
