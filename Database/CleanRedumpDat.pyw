import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

# ── Filter patterns ────────────────────────────────────────────────────────────
FILTER_PATTERNS = {
    "demo":        re.compile(r'\(Demo(?:\s+\d+)?\)', re.IGNORECASE),
    "prototype":   re.compile(r'\(Proto(?:type)?(?:\s+\d+)?\)', re.IGNORECASE),
    "beta":        re.compile(r'\(Beta(?:\s+\d+)?\)', re.IGNORECASE),
    "unlicensed":  re.compile(r'\(Unl\)', re.IGNORECASE),
}

def should_exclude(desc, filters):
    """Return True if the description matches any active filter."""
    for key, pattern in FILTER_PATTERNS.items():
        if filters.get(key, False) and pattern.search(desc):
            return True
    return False

def clean_dat_file(dat_file, filters):
    """Extract, filter, fix encoding, sort and return (descriptions, removed_count)."""
    with open(dat_file, 'r', encoding='utf-8') as f:
        content = f.read()

    descriptions = re.findall(r'<description>(.*?)</description>', content)
    descriptions = [d.replace('&amp;', '&') for d in descriptions]

    kept   = [d for d in descriptions if not should_exclude(d, filters)]
    removed = len(descriptions) - len(kept)

    kept.sort()
    return kept, removed

def process_files(dat_files, filters, log_widget, btn_run, progress_var):
    total   = len(dat_files)
    results = []

    for i, dat_file in enumerate(dat_files, 1):
        try:
            kept, removed = clean_dat_file(dat_file, filters)
            txt_file = os.path.splitext(dat_file)[0] + '.txt'
            with open(txt_file, 'w', encoding='utf-8') as f:
                for desc in kept:
                    f.write(desc + '\n')

            msg = f"[✓] {os.path.basename(dat_file)}  →  {len(kept)} entries kept, {removed} filtered out"
            results.append(msg)
        except Exception as e:
            results.append(f"[✗] {os.path.basename(dat_file)}  →  ERROR: {e}")

        progress_var.set(int(i / total * 100))
        log_widget.after(0, lambda m=msg: _append_log(log_widget, m))

    summary = f"\nDone — processed {total} file(s)."
    log_widget.after(0, lambda: _append_log(log_widget, summary))
    log_widget.after(0, lambda: btn_run.config(state='normal'))


def _append_log(widget, text):
    widget.config(state='normal')
    widget.insert('end', text + '\n')
    widget.see('end')
    widget.config(state='disabled')


# ── GUI ────────────────────────────────────────────────────────────────────────
_BaseClass = TkinterDnD.Tk if DND_AVAILABLE else tk.Tk

class App(_BaseClass):
    def __init__(self):
        super().__init__()
        self.title("Redump DAT Cleaner")
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")

        self._build_styles()
        self._build_ui()

    # ── styles ──────────────────────────────────────────────────────────────
    def _build_styles(self):
        self.BG       = "#1a1a2e"
        self.PANEL    = "#16213e"
        self.ACCENT   = "#e94560"
        self.ACCENT2  = "#0f3460"
        self.FG       = "#eaeaea"
        self.FG_DIM   = "#8892a4"
        self.MONO     = ("Consolas", 9)
        self.SANS     = ("Segoe UI", 10)
        self.SANS_B   = ("Segoe UI", 10, "bold")

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TProgressbar",
                         troughcolor=self.PANEL,
                         background=self.ACCENT,
                         bordercolor=self.PANEL,
                         lightcolor=self.ACCENT,
                         darkcolor=self.ACCENT)

    # ── main layout ─────────────────────────────────────────────────────────
    def _build_ui(self):
        pad = dict(padx=18, pady=10)

        # ── title ──
        hdr = tk.Frame(self, bg=self.BG)
        hdr.pack(fill='x', padx=18, pady=(18, 4))
        tk.Label(hdr, text="REDUMP", font=("Segoe UI", 22, "bold"),
                 fg=self.ACCENT, bg=self.BG).pack(side='left')
        tk.Label(hdr, text=" DAT Cleaner", font=("Segoe UI", 22),
                 fg=self.FG, bg=self.BG).pack(side='left')

        tk.Label(self, text="Strip unwanted entries and sort your DAT files.",
                 font=("Segoe UI", 9), fg=self.FG_DIM, bg=self.BG).pack(anchor='w', padx=18)

        self._divider()

        # ── filter toggles ──
        tk.Label(self, text="FILTERS", font=("Segoe UI", 8, "bold"),
                 fg=self.FG_DIM, bg=self.BG).pack(anchor='w', padx=18, pady=(10, 4))

        filters_frame = tk.Frame(self, bg=self.PANEL, bd=0, highlightthickness=1,
                                  highlightbackground=self.ACCENT2)
        filters_frame.pack(fill='x', padx=18, pady=(0, 10))

        self.filter_vars = {}
        filter_defs = [
            ("demo",       "Demo",        "(Demo) / (Demo #)",            True),
            ("prototype",  "Prototype",   "(Proto) / (Proto #) / (Prototype)", True),
            ("beta",       "Beta",        "(Beta) / (Beta #)",            True),
            ("unlicensed", "Unlicensed",  "(Unl)",                        True),
        ]

        for col, (key, label, hint, default) in enumerate(filter_defs):
            var = tk.BooleanVar(value=default)
            self.filter_vars[key] = var
            cell = tk.Frame(filters_frame, bg=self.PANEL)
            cell.grid(row=0, column=col, sticky='nsew', padx=1, pady=1)
            filters_frame.columnconfigure(col, weight=1)

            cb = tk.Checkbutton(cell, variable=var,
                                 font=self.SANS_B, text=label,
                                 fg=self.FG, bg=self.PANEL,
                                 activeforeground=self.ACCENT,
                                 activebackground=self.PANEL,
                                 selectcolor=self.ACCENT2,
                                 relief='flat', bd=0,
                                 cursor='hand2')
            cb.pack(pady=(10, 2))
            tk.Label(cell, text=hint, font=("Segoe UI", 7),
                     fg=self.FG_DIM, bg=self.PANEL, wraplength=120).pack(pady=(0, 10))

        self._divider()

        # ── file list ──
        tk.Label(self, text="DAT FILES", font=("Segoe UI", 8, "bold"),
                 fg=self.FG_DIM, bg=self.BG).pack(anchor='w', padx=18, pady=(10, 4))

        list_frame = tk.Frame(self, bg=self.PANEL, highlightthickness=1,
                               highlightbackground=self.ACCENT2)
        list_frame.pack(fill='x', padx=18)

        self.file_listbox = tk.Listbox(list_frame,
                                        bg=self.PANEL, fg=self.FG,
                                        selectbackground=self.ACCENT2,
                                        font=self.MONO,
                                        relief='flat', bd=0,
                                        height=6,
                                        activestyle='none')
        self.file_listbox.pack(side='left', fill='both', expand=True, padx=6, pady=6)

        sb = tk.Scrollbar(list_frame, orient='vertical',
                           command=self.file_listbox.yview,
                           bg=self.BG, troughcolor=self.PANEL,
                           relief='flat')
        sb.pack(side='right', fill='y')
        self.file_listbox.config(yscrollcommand=sb.set)

        # Drag-and-drop hint label
        hint_text = "drag & drop .dat files or folders here  •  " if DND_AVAILABLE else ""
        self.drop_hint = tk.Label(list_frame,
                                   text=f"{hint_text}or use buttons below",
                                   font=("Segoe UI", 7), fg=self.FG_DIM,
                                   bg=self.PANEL)
        self.drop_hint.place(relx=0.5, rely=0.92, anchor='center')

        # Register DnD if available
        if DND_AVAILABLE:
            self.file_listbox.drop_target_register(DND_FILES)
            self.file_listbox.dnd_bind('<<Drop>>', self._on_drop)
            self.file_listbox.dnd_bind('<<DragEnter>>', self._on_drag_enter)
            self.file_listbox.dnd_bind('<<DragLeave>>', self._on_drag_leave)

        btn_row = tk.Frame(self, bg=self.BG)
        btn_row.pack(fill='x', padx=18, pady=6)

        self._btn(btn_row, "＋ Add Files",   self._add_files).pack(side='left', padx=(0,6))
        self._btn(btn_row, "＋ Add Folder",  self._add_folder).pack(side='left', padx=(0,6))
        self._btn(btn_row, "✕ Remove Selected", self._remove_selected, secondary=True).pack(side='left')
        self._btn(btn_row, "✕ Clear All",    self._clear_all, secondary=True).pack(side='left', padx=6)

        self._divider()

        # ── progress + run ──
        self.progress_var = tk.IntVar(value=0)
        prog = ttk.Progressbar(self, variable=self.progress_var,
                                maximum=100, style="TProgressbar")
        prog.pack(fill='x', padx=18, pady=(10, 6))

        self.btn_run = self._btn(self, "▶  RUN CLEANER", self._run, accent=True)
        self.btn_run.pack(fill='x', padx=18, pady=(0, 10))

        self._divider()

        # ── log ──
        tk.Label(self, text="LOG", font=("Segoe UI", 8, "bold"),
                 fg=self.FG_DIM, bg=self.BG).pack(anchor='w', padx=18, pady=(10, 4))

        log_frame = tk.Frame(self, bg=self.PANEL, highlightthickness=1,
                              highlightbackground=self.ACCENT2)
        log_frame.pack(fill='both', expand=True, padx=18, pady=(0, 18))

        self.log = tk.Text(log_frame, state='disabled',
                            bg=self.PANEL, fg="#a8c7a0",
                            font=self.MONO, relief='flat', bd=0,
                            height=8, wrap='none')
        self.log.pack(fill='both', expand=True, padx=6, pady=6)

        self.geometry("700x720")

    # ── helpers ─────────────────────────────────────────────────────────────
    def _divider(self):
        tk.Frame(self, bg=self.ACCENT2, height=1).pack(fill='x', padx=18, pady=2)

    def _btn(self, parent, text, cmd, accent=False, secondary=False):
        bg = self.ACCENT if accent else (self.ACCENT2 if not secondary else "#2a2a4a")
        fg = "#ffffff"
        return tk.Button(parent, text=text, command=cmd,
                          bg=bg, fg=fg, activebackground=self.ACCENT,
                          activeforeground='white',
                          font=self.SANS_B if accent else self.SANS,
                          relief='flat', bd=0,
                          padx=12, pady=8,
                          cursor='hand2')

    def _on_drop(self, event):
        # tkinterdnd2 returns paths as a Tcl list string; parse it properly
        raw = event.data
        # Paths with spaces are wrapped in {braces} by Tcl
        paths = []
        i = 0
        while i < len(raw):
            if raw[i] == '{':
                end = raw.index('}', i)
                paths.append(raw[i+1:end])
                i = end + 2
            else:
                end = raw.find(' ', i)
                if end == -1:
                    paths.append(raw[i:])
                    break
                paths.append(raw[i:end])
                i = end + 1

        for path in paths:
            path = path.strip()
            if not path:
                continue
            if os.path.isdir(path):
                for fname in os.listdir(path):
                    if fname.lower().endswith('.dat'):
                        full = os.path.join(path, fname)
                        if full not in self.file_listbox.get(0, 'end'):
                            self.file_listbox.insert('end', full)
            elif path.lower().endswith('.dat'):
                if path not in self.file_listbox.get(0, 'end'):
                    self.file_listbox.insert('end', path)

        self._on_drag_leave(event)

    def _on_drag_enter(self, event):
        self.file_listbox.config(highlightthickness=2,
                                  highlightbackground=self.ACCENT,
                                  highlightcolor=self.ACCENT)

    def _on_drag_leave(self, event):
        self.file_listbox.config(highlightthickness=0)

    def _add_files(self):
        files = filedialog.askopenfilenames(
            title="Select DAT files",
            filetypes=[("DAT files", "*.dat"), ("All files", "*.*")])
        for f in files:
            if f not in self.file_listbox.get(0, 'end'):
                self.file_listbox.insert('end', f)

    def _add_folder(self):
        folder = filedialog.askdirectory(title="Select folder containing DAT files")
        if folder:
            for fname in os.listdir(folder):
                if fname.lower().endswith('.dat'):
                    full = os.path.join(folder, fname)
                    if full not in self.file_listbox.get(0, 'end'):
                        self.file_listbox.insert('end', full)

    def _remove_selected(self):
        for idx in reversed(self.file_listbox.curselection()):
            self.file_listbox.delete(idx)

    def _clear_all(self):
        self.file_listbox.delete(0, 'end')

    def _run(self):
        dat_files = list(self.file_listbox.get(0, 'end'))
        if not dat_files:
            messagebox.showwarning("No files", "Please add at least one .dat file.")
            return

        filters = {k: v.get() for k, v in self.filter_vars.items()}

        self.progress_var.set(0)
        self.log.config(state='normal')
        self.log.delete('1.0', 'end')
        self.log.config(state='disabled')
        self.btn_run.config(state='disabled')

        t = threading.Thread(target=process_files,
                              args=(dat_files, filters, self.log,
                                    self.btn_run, self.progress_var),
                              daemon=True)
        t.start()


if __name__ == '__main__':
    if not DND_AVAILABLE:
        print("Note: drag-and-drop disabled. Install tkinterdnd2 to enable it:")
        print("  pip install tkinterdnd2")
    app = App()
    app.mainloop()
