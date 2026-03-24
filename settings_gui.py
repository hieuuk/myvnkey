"""Tkinter settings window for managing per-app Vietnamese mode rules."""

import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import config
from app_monitor import get_foreground_info


def open_settings():
    """Open the settings window in its own thread."""
    t = threading.Thread(target=_run_settings_window, daemon=True)
    t.start()


def _run_settings_window():
    root = tk.Tk()
    root.title('MyVNKey Settings')
    root.geometry('560x560')
    root.resizable(False, False)

    # ── General settings ─────────────────────────────────────────────────

    frame_general = ttk.LabelFrame(root, text='General', padding=8)
    frame_general.pack(fill='x', padx=10, pady=(10, 5))

    # Switch key
    key_frame = ttk.Frame(frame_general)
    key_frame.pack(fill='x', pady=(0, 4))

    ttk.Label(key_frame, text='Switch key:').pack(side='left', padx=(0, 5))

    sk = config.switch_key
    mod_var = tk.StringVar(value=sk.get('modifier', 'alt').replace('+', '+').title()
                           .replace('alt', 'Alt').replace('ctrl', 'Ctrl')
                           .replace('shift', 'Shift'))
    # Normalize display
    _mod_display = {'alt': 'Alt', 'ctrl': 'Ctrl', 'ctrl+alt': 'Ctrl+Alt', 'ctrl+shift': 'Ctrl+Shift'}
    mod_var.set(_mod_display.get(sk.get('modifier', 'alt').lower(), 'Alt'))

    mod_combo = ttk.Combobox(key_frame, textvariable=mod_var,
                             values=config.MODIFIER_OPTIONS,
                             state='readonly', width=12)
    mod_combo.pack(side='left', padx=(0, 3))

    ttk.Label(key_frame, text='+').pack(side='left', padx=(0, 3))

    key_var = tk.StringVar(value=sk.get('key', 'z').upper())
    key_combo = ttk.Combobox(key_frame, textvariable=key_var,
                             values=config.KEY_OPTIONS,
                             state='readonly', width=4)
    key_combo.pack(side='left')

    # Checkboxes
    beep_var = tk.BooleanVar(value=config.beep_on_switch)
    ttk.Checkbutton(frame_general, text='Beep on language switch',
                    variable=beep_var).pack(anchor='w')

    autorun_var = tk.BooleanVar(value=config.autorun)
    ttk.Checkbutton(frame_general, text='Auto-run at startup',
                    variable=autorun_var).pack(anchor='w')

    # ── App rules list ───────────────────────────────────────────────────

    frame_list = ttk.LabelFrame(root, text='Per-App Rules', padding=10)
    frame_list.pack(fill='both', expand=True, padx=10, pady=(0, 5))

    columns = ('match', 'pattern', 'mode')
    tree = ttk.Treeview(frame_list, columns=columns, show='headings', height=8)
    tree.heading('match', text='Match By')
    tree.heading('pattern', text='Pattern')
    tree.heading('mode', text='Mode')
    tree.column('match', width=100)
    tree.column('pattern', width=250)
    tree.column('mode', width=120)
    tree.pack(side='left', fill='both', expand=True)

    scrollbar = ttk.Scrollbar(frame_list, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side='right', fill='y')

    _MATCH_LABELS = {'process': 'Process Name', 'title': 'Window Title', 'regex': 'Regex (Title)'}

    def refresh_list():
        tree.delete(*tree.get_children())
        for rule in config.app_rules:
            match_type = rule.get('match', 'process')
            match_label = _MATCH_LABELS.get(match_type, match_type)
            pattern = rule.get('pattern', '')
            mode_text = 'Vietnamese' if rule.get('vietnamese') else 'English'
            tree.insert('', 'end', values=(match_label, pattern, mode_text))

    refresh_list()

    # ── Add rule section ─────────────────────────────────────────────────

    frame_add = ttk.LabelFrame(root, text='Add Rule', padding=8)
    frame_add.pack(fill='x', padx=10, pady=(0, 5))

    row1 = ttk.Frame(frame_add)
    row1.pack(fill='x', pady=(0, 4))

    match_var = tk.StringVar(value='Process Name')
    match_combo = ttk.Combobox(row1, textvariable=match_var,
                               values=['Process Name', 'Window Title', 'Regex (Title)'],
                               state='readonly', width=14)
    match_combo.pack(side='left', padx=(0, 5))

    entry_var = tk.StringVar()
    entry = ttk.Entry(row1, textvariable=entry_var, width=30)
    entry.pack(side='left', padx=(0, 5), fill='x', expand=True)

    def detect_app():
        root.after(3000, _do_detect)

    def _do_detect():
        proc, title = get_foreground_info()
        mt = match_var.get()
        if mt in ('Window Title', 'Regex (Title)'):
            if title:
                entry_var.set(title)
            else:
                messagebox.showwarning('Detection Failed',
                                       'Could not detect the window title.')
        else:
            if proc:
                entry_var.set(proc)
            else:
                messagebox.showwarning('Detection Failed',
                                       'Could not detect the foreground application.')
        root.lift()
        root.focus_force()

    ttk.Button(row1, text='Detect (3s)', command=detect_app).pack(side='left')

    row2 = ttk.Frame(frame_add)
    row2.pack(fill='x')

    mode_var = tk.StringVar(value='Vietnamese')
    mode_combo = ttk.Combobox(row2, textvariable=mode_var,
                              values=['Vietnamese', 'English'],
                              state='readonly', width=14)
    mode_combo.pack(side='left', padx=(0, 5))

    def add_rule():
        pattern = entry_var.get().strip()
        if not pattern:
            return
        match_map = {'Window Title': 'title', 'Regex (Title)': 'regex'}
        match_type = match_map.get(match_var.get(), 'process')
        vn = mode_var.get() == 'Vietnamese'
        config.app_rules.append({
            'pattern': pattern,
            'match': match_type,
            'vietnamese': vn,
        })
        entry_var.set('')
        refresh_list()

    ttk.Button(row2, text='Add', command=add_rule).pack(side='left')

    # ── Action buttons ───────────────────────────────────────────────────

    frame_actions = ttk.Frame(root, padding=(10, 5))
    frame_actions.pack(fill='x')

    def _get_selected_index():
        sel = tree.selection()
        if not sel:
            return None
        return tree.index(sel[0])

    def toggle_selected():
        idx = _get_selected_index()
        if idx is not None and idx < len(config.app_rules):
            config.app_rules[idx]['vietnamese'] = not config.app_rules[idx]['vietnamese']
            refresh_list()

    def remove_selected():
        idx = _get_selected_index()
        if idx is not None and idx < len(config.app_rules):
            config.app_rules.pop(idx)
            refresh_list()

    def save_and_close():
        # Save general settings
        config.beep_on_switch = beep_var.get()
        config.switch_key = {
            'modifier': mod_var.get().lower(),
            'key': key_var.get().lower(),
        }
        # Handle autorun
        new_autorun = autorun_var.get()
        if new_autorun != config.autorun:
            config.set_autorun(new_autorun)
        config.save_config()
        root.destroy()

    def export_config():
        path = filedialog.asksaveasfilename(
            parent=root,
            title='Export Config',
            defaultextension='.json',
            filetypes=[('JSON files', '*.json'), ('All files', '*.*')],
            initialfile='myvnkey-config.json',
        )
        if path:
            try:
                config.export_config(path)
                messagebox.showinfo('Export', f'Config exported to:\n{path}', parent=root)
            except OSError as e:
                messagebox.showerror('Export Failed', str(e), parent=root)

    ttk.Button(frame_actions, text='Toggle Mode', command=toggle_selected).pack(side='left', padx=(0, 5))
    ttk.Button(frame_actions, text='Remove', command=remove_selected).pack(side='left', padx=(0, 5))
    ttk.Button(frame_actions, text='Export Config', command=export_config).pack(side='left', padx=(0, 5))
    ttk.Button(frame_actions, text='Save && Close', command=save_and_close).pack(side='right')

    root.mainloop()
