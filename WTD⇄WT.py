import sys
import subprocess
import os

REQUIRED_LIBRARIES = {"windnd": "windnd", "pywinstyles": "pywinstyles"}

def install_missing_libraries():
    import importlib.util
    for module_name, pip_name in REQUIRED_LIBRARIES.items():
        if importlib.util.find_spec(module_name) is None:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name], 
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception: pass

install_missing_libraries()

import json
import re
import tkinter as tk
from tkinter import filedialog
import windnd
import pywinstyles

DEFAULT_HEADER = (
    "rangefinderProgressBarColor1:c = 0, 255, 0, 64\n"
    "rangefinderProgressBarColor2:c = 255, 255, 255, 64\n"
    "rangefinderTextScale:r = 0.7\n"
    "rangefinderVerticalOffset:r = 18\n"
    "rangefinderHorizontalOffset:r = 5\n"
    "fontSizeMult:r = 1\n"
    "lineSizeMult:r = 1\n"
    "drawCentralLineVert:b = yes\n"
    "drawCentralLineHorz:b = yes\n"
    "crosshairColor:c = 31, 239, 31, 255\n"
    "crosshairLightColor:c = 255, 30, 30, 255\n"
    "crosshairDistHorSizeMain:p2 = 0.03, 0.02\n"
    "crosshairDistHorSizeAdditional:p2 = 0.005, 0.003\n"
    "distanceCorrectionPos:p2 = 0.02, -0.005\n"
    "drawDistanceCorrection:b = yes\n"
    "useSmoothEdge:b = no\n"
    "rangefinderUseThousandth:b = yes\n"
    "detectAllyTextScale:r = 0.7\n"
    "detectAllyOffset:p2 = 4, 0.025\n\n"
    "crosshair_distances{\n"
    "  distance:p3=200, 0, 0\n"
    "  distance:p3=400, 4, 0\n"
    "  distance:p3=600, 0, 0\n"
    "  distance:p3=800, 8, 0\n"
    "  distance:p3=1000, 0, 0\n"
    "  distance:p3=1200, 12, 0\n"
    "  distance:p3=1400, 0, 0\n"
    "  distance:p3=1600, 16, 0\n"
    "  distance:p3=1800, 0, 0\n"
    "  distance:p3=2000, 20, 0\n"
    "  distance:p3=2200, 0, 0\n"
    "  distance:p3=2400, 24, 0\n"
    "  distance:p3=2600, 0, 0\n"
    "  distance:p3=2800, 28, 0\n"
    "  distance:p3=3000, 0, 0\n"
    "  distance:p3=3200, 32, 0\n"
    "  distance:p3=3400, 0, 0\n"
    "  distance:p3=3600, 36, 0\n"
    "  distance:p3=3800, 0, 0\n"
    "  distance:p3=4000, 40, 0\n"
    "  distance:p3=4200, 0, 0\n"
    "  distance:p3=4400, 44, 0\n"
    "  distance:p3=4600, 0, 0\n"
    "  distance:p3=4800, 48, 0\n"
    "  distance:p3=5000, 0, 0\n"
    "  distance:p3=5200, 52, 0\n"
    "  distance:p3=5400, 0, 0\n"
    "  distance:p3=5600, 56, 0\n"
    "  distance:p3=5800, 0, 0\n"
    "  distance:p3=6000, 60, 0\n"
    "}\n\n"
    "crosshair_hor_ranges{\n"
    "}\n\n"
    "matchExpClass {\n"
    "  exp_tank:b = yes\n"
    "  exp_heavy_tank:b = yes\n"
    "  exp_tank_destroyer:b = yes\n"
    "  exp_SPAA:b = yes\n"
    "}\n"
)

saved_blk_header = ""

def extract_block(text, block_name):
    pattern = re.compile(rf'{block_name}\s*{{', re.MULTILINE)
    match = pattern.search(text)
    if not match: return ""
    start = match.end()
    depth = 1
    i = start
    while i < len(text):
        if text[i] == '{': depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0: return text[start:i]
        i += 1
    return ""

def extract_header_and_lines(blk_text):
    global saved_blk_header
    match = re.search(r'((drawLines|drawQuads)\s*\{)', blk_text)
    if match: saved_blk_header = blk_text[:match.start()].strip() + "\n\n"
    else: saved_blk_header = ""

def parse_blk_to_json(blk_text):
    result = {}
    element_id = 0
    lines_block = extract_block(blk_text, "drawLines")
    quads_block = extract_block(blk_text, "drawQuads")
    if lines_block:
        line_pattern = re.compile(
            r'line\s*{line:p4\s*=\s*([^;}\s]+);\s*move:b\s*=\s*(true|false);(?:\s*thousandth:b\s*=\s*(true|false);)?}', 
            re.IGNORECASE
        )
        for match in line_pattern.finditer(lines_block):
            try:
                coords = [float(x) for x in match.group(1).split(',')]
                if len(coords) == 4:
                    move_val = match.group(2).lower() == "true"
                    has_thousandth = match.group(3) is not None and match.group(3).lower() == "true"
                    result[str(element_id)] = {
                        "name": f"Линия{element_id}", "type": "line",
                        "start": {"x": coords[0], "y": coords[1]}, "end": {"x": coords[2], "y": coords[3]},
                        "move": move_val, "thousandth": has_thousandth, "selected": False
                    }
                    element_id += 1
            except ValueError: continue
    if quads_block:
        quad_pattern = re.compile(
            r'quad\s*{tl:p2\s*=\s*([^;}\s]+);\s*tr:p2\s*=\s*([^;}\s]+);\s*br:p2\s*=\s*([^;}\s]+);\s*bl:p2\s*=\s*([^;}\s]+);}', 
            re.IGNORECASE
        )
        for match in quad_pattern.finditer(quads_block):
            try:
                tl_coords = [float(x) for x in match.group(1).split(',')]
                tr_coords = [float(x) for x in match.group(2).split(',')]
                br_coords = [float(x) for x in match.group(3).split(',')]
                bl_coords = [float(x) for x in match.group(4).split(',')]
                result[str(element_id)] = {
                    "name": f"Четырёхугольник{element_id}", "type": "quad",
                    "pos1": {"x": tl_coords[0], "y": tl_coords[1]}, "pos2": {"x": tr_coords[0], "y": tr_coords[1]},
                    "pos3": {"x": br_coords[0], "y": br_coords[1]}, "pos4": {"x": bl_coords[0], "y": bl_coords[1]},
                    "selected": False
                }
                element_id += 1
            except ValueError: continue
    return result

def pack_json_to_blk(json_data, current_editor_text):
    lines_content = []
    quads_content = []
    for key in sorted(json_data.keys(), key=lambda x: int(x) if x.isdigit() else x):
        el = json_data[key]
        if el.get("type") == "line":
            move_str = "true" if el.get("move", False) else "false"
            thousandth_str = " thousandth:b=true;" if el.get("thousandth") is True else ""
            lines_content.append(f"  line {{line:p4={el['start']['x']},{el['start']['y']},{el['end']['x']},{el['end']['y']}; move:b={move_str};{thousandth_str}}}\n")
        elif el.get("type") == "quad":
            quads_content.append(f"  quad {{tl:p2={el['pos1']['x']},{el['pos1']['y']}; tr:p2={el['pos2']['x']},{el['pos2']['y']}; br:p2={el['pos3']['x']},{el['pos3']['y']}; bl:p2={el['pos4']['x']},{el['pos4']['y']};}}\n")
    geom_blocks = ""
    if lines_content: geom_blocks += f"drawLines{{\n{''.join(lines_content)}}}\n\n"
    if quads_content: geom_blocks += f"drawQuads{{\n{''.join(quads_content)}}}\n"
    header = current_editor_text.strip() + "\n\n" if current_editor_text.strip() else DEFAULT_HEADER
    return header + geom_blocks

class ConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WTDraw ⇄ War Thunder BLK")
        self.root.geometry("1100x580") 
        self.root.resizable(False, False)
        
        self.bg_canvas = "#0b0b0b"       
        self.bg_main = "#1a1a1a"         
        self.bg_sidebar = "#222222"      
        self.bg_widgets = "#2c2c2c"      
        self.bg_hover = "#3a3a3a"        
        self.bg_hover_green = "#1a3d1a"  
        self.fg_primary = "#e0e0e0"      
        self.fg_muted = "#888888"        
        self.fg_accent = "#1fef1f"       
        
        self.root.configure(bg=self.bg_main)
        self.root.after(100, self.apply_dark_theme)
        
        icon_name = "ico.ico"
        if getattr(sys, 'frozen', False): icon_path = os.path.join(sys._MEIPASS, icon_name)
        else: icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), icon_name)
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
                import ctypes
                myappid = 'wtdraw.converter.blkjson.v1'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception: pass
        
        self.current_file_path = None
        self.current_json_data = {}
        
        self.canvas_w = 740
        self.canvas_h = 410
        self.sight_color = "#ffffff"
        
        self.settings_expanded = True
        
        self.color_palette = [
            ("Белый", "#ffffff"),
            ("Зелёный", "#1fef1f"),
            ("Голубой", "#00ffff"),
            ("Красный", "#ff1e1e"),
            ("Жёлтый", "#ffff00")
        ]
        self.current_color_idx = 0
        
        self.zoom_scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0  
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        self.last_mouse_x = self.canvas_w / 2
        self.last_mouse_y = self.canvas_h / 2
        
        self.main_container = tk.Frame(root, bg=self.bg_main)
        self.main_container.pack(fill="both", expand=True)
        
        self.left_frame = tk.Frame(self.main_container, bg=self.bg_main, width=770, height=540)
        self.left_frame.pack(side="left", fill="both", expand=True)
        self.left_frame.pack_propagate(False)
        
        self.drop_label = tk.Label(
            self.left_frame, text="Перетащите сюда файл .blk / .json или кликните для выбора",
            relief="flat", bg=self.bg_widgets, fg=self.fg_primary, font=("Segoe UI", 9, "bold"), height=2
        )
        self.drop_label.pack(fill="x", padx=15, pady=(15, 5))
        self.drop_label.bind("<Button-1>", self.handle_click)
        self.drop_label.bind("<Enter>", lambda e: self.drop_label.config(bg=self.bg_hover))
        self.drop_label.bind("<Leave>", lambda e: self.drop_label.config(bg=self.bg_widgets))
        
        self.canvas_container = tk.Frame(self.left_frame, bg=self.bg_main)
        self.canvas_container.pack(padx=15, pady=5)
        
        self.canvas = tk.Canvas(self.canvas_container, width=self.canvas_w, height=self.canvas_h, bg=self.bg_canvas, highlightbackground=self.bg_widgets, highlightthickness=1)
        self.canvas.pack()
        
        self.canvas.bind("<MouseWheel>", self.handle_zoom)
        self.canvas.bind("<ButtonPress-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.pan_canvas)
        self.canvas.bind("<Motion>", self.track_coordinates)
        
        self.hint_panel = tk.Frame(self.left_frame, bg=self.bg_widgets)
        self.hint_panel.pack(fill="x", padx=15, pady=(11, 10))
        
        try: pywinstyles.apply_style(self.hint_panel, "dark")
        except Exception: pass
        
        real_hint_text = (
            "Перемещение: [ПКМ] + movement мыши      •      Масштаб: [Колёсико мыши]\n"
            "Перезагрузить файл: [F5]      •      Сохранить / Конвертировать: [Ctrl + S]"
        )
        
        self.hint_text_lbl = tk.Label(
            self.hint_panel, text=real_hint_text, bg=self.bg_widgets, fg=self.fg_primary, 
            font=("Segoe UI", 9), justify="center", pady=6, wraplength=650
        )
        self.hint_text_lbl.pack(side="left", fill="x", expand=True, padx=(30, 0))
        
        self.close_hint_btn = tk.Button(
            self.hint_panel, text="✖", bg=self.bg_widgets, fg=self.fg_muted, relief="flat",
            activebackground=self.bg_hover, activeforeground=self.fg_primary, font=("Segoe UI", 9, "bold"),
            command=self.hide_hint_panel, cursor="hand2", bd=0, padx=12
        )
        self.close_hint_btn.pack(side="right", fill="y")
        self.close_hint_btn.bind("<Enter>", lambda e: self.close_hint_btn.config(fg=self.fg_primary))
        self.close_hint_btn.bind("<Leave>", lambda e: self.close_hint_btn.config(fg=self.fg_muted))
        
        self.sidebar = tk.Frame(self.main_container, bg=self.bg_sidebar, width=330, height=540)
        self.sidebar.pack(side="right", fill="both")
        self.sidebar.pack_propagate(False)
        
        self.sidebar_title = tk.Label(self.sidebar, text="УПРАВЛЕНИЕ", bg=self.bg_sidebar, fg=self.fg_muted, font=("Segoe UI", 9, "bold"))
        self.sidebar_title.pack(fill="x", pady=(18, 10))
        
        self.convert_btn = tk.Button(
            self.sidebar, text="🚀  Конвертировать файл", bg=self.bg_widgets, fg=self.fg_primary, relief="flat", 
            activebackground=self.bg_hover_green, activeforeground=self.fg_primary, font=("Segoe UI", 10, "bold"), height=2, command=self.trigger_conversion, cursor="hand2"
        )
        self.convert_btn.pack(fill="x", padx=18, pady=5)
        self.convert_btn.bind("<Enter>", lambda e: self.convert_btn.config(bg=self.bg_hover_green, fg=self.fg_primary))
        self.convert_btn.bind("<Leave>", lambda e: self.convert_btn.config(bg=self.bg_widgets, fg=self.fg_primary))
        
        self.btn_grid = tk.Frame(self.sidebar, bg=self.bg_sidebar)
        self.btn_grid.pack(fill="x", padx=18, pady=5)
        
        self.reset_zoom_btn = tk.Button(
            self.btn_grid, text="🔍 Сбросить вид", bg=self.bg_widgets, fg=self.fg_primary, relief="flat",
            activebackground=self.bg_hover, activeforeground=self.fg_primary, font=("Segoe UI", 9, "bold"), width=13, pady=6, command=self.reset_view, cursor="hand2"
        )
        self.reset_zoom_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.reset_zoom_btn.bind("<Enter>", lambda e: self.reset_zoom_btn.config(bg=self.bg_hover))
        self.reset_zoom_btn.bind("<Leave>", lambda e: self.reset_zoom_btn.config(bg=self.bg_widgets))
        
        self.clear_btn = tk.Button(
            self.btn_grid, text="❌ Очистить всё", bg=self.bg_widgets, fg="#ff4d4d", relief="flat",
            activebackground="#3d2222", activeforeground="#ff4d4d", font=("Segoe UI", 9, "bold"), width=13, pady=6, command=self.clear_canvas, cursor="hand2"
        )
        self.clear_btn.pack(side="right", expand=True, fill="x", padx=(4, 0))
        self.clear_btn.bind("<Enter>", lambda e: self.clear_btn.config(bg="#3a2727"))
        self.clear_btn.bind("<Leave>", lambda e: self.clear_btn.config(bg=self.bg_widgets))
        
        self.settings_btn = tk.Button(
            self.sidebar, text="⚙  Настройки blk", bg=self.bg_widgets, fg=self.fg_primary, relief="flat",
            activebackground=self.bg_hover, font=("Segoe UI", 9, "bold"), pady=7, command=self.toggle_settings, cursor="hand2"
        )
        self.settings_btn.pack(fill="x", padx=18, pady=(15, 5))
        self.settings_btn.bind("<Enter>", lambda e: self.settings_btn.config(bg=self.bg_hover))
        self.settings_btn.bind("<Leave>", lambda e: self.settings_btn.config(bg=self.bg_widgets))
        
        self.settings_subframe = tk.Frame(self.sidebar, bg=self.bg_sidebar)
        self.settings_subframe.pack(fill="both", expand=True, padx=18)
        
        self.color_bar = tk.Frame(self.settings_subframe, bg=self.bg_sidebar)
        self.color_bar.pack(fill="x", pady=(5, 10))
        
        self.color_label = tk.Label(self.color_bar, text="Цвет сетки:", bg=self.bg_sidebar, fg=self.fg_primary, font=("Segoe UI", 9, "bold"))
        self.color_label.pack(side="left", padx=(0, 10))
        
        for name, hex_code in self.color_palette:
            btn = tk.Button(self.color_bar, text="■", bg=self.bg_sidebar, fg=hex_code,
                            relief="flat", font=("Segoe UI", 12), width=2, activebackground=self.bg_sidebar, activeforeground=hex_code,
                            command=lambda c=hex_code: self.change_sight_color(c), cursor="hand2", bd=0)
            btn.pack(side="left", padx=1)
            
        self.text_editor = tk.Text(
            self.settings_subframe, bg=self.bg_canvas, fg=self.fg_primary, insertbackground=self.fg_primary,
            selectbackground=self.bg_hover, font=("Consolas", 9), relief="flat", undo=True, maxundo=100
        )
        self.text_editor.pack(fill="both", expand=True, pady=(0, 15))
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", DEFAULT_HEADER)
        self.text_editor.bind("<Key>", self.intercept_typing)
        
        self.bottom_bar = tk.Frame(root, bg=self.bg_canvas, height=30)
        self.bottom_bar.pack(fill="x", side="bottom")
        
        self.status_label = tk.Label(
            self.bottom_bar, text="Статус: Ожидание импорта чертежа (.blk / .json)",
            bd=0, relief="flat", anchor="w", bg=self.bg_canvas, fg=self.fg_muted, font=("Segoe UI", 9), padx=15
        )
        self.status_label.pack(side="left", fill="x", expand=True, ipady=6)
        
        self.show_hint_btn = tk.Button(
            self.bottom_bar, text="📋 Показать подсказку", bg=self.bg_canvas, fg=self.fg_primary,
            relief="flat", activebackground=self.bg_widgets, activeforeground=self.fg_primary, font=("Segoe UI", 9, "underline"), 
            command=self.show_hint_panel, cursor="hand2", bd=0
        )
        self.show_hint_btn.pack_forget()
        
        self.root.bind("<F5>", lambda e: self.reload_current_file())
        self.root.bind("<Control-s>", lambda e: self.trigger_conversion_hotkey())
        
        windnd.hook_dropfiles(self.root, func=self.handle_drop)
        
        self.grid_line_ids = []
        self.axis_line_ids = []
        self.frame_line_ids = []
        self.sight_element_ids = []
        
        self.init_canvas_objects()
        self.redraw_sight()

    def apply_dark_theme(self):
        try: pywinstyles.apply_style(self.root, "dark")
        except Exception: pass

    def hide_hint_panel(self):
        self.hint_panel.pack_forget()
        self.show_hint_btn.pack(side="right", padx=15, ipady=3)
        
    def show_hint_panel(self):
        self.show_hint_btn.pack_forget()
        self.hint_panel.pack(fill="x", padx=15, pady=(11, 10))
        
    def log_message(self, message, color=None):
        if color is None: color = self.fg_muted
        self.status_label.config(text=message, fg=color)
        
    def get_editable_ranges(self):
        content = self.text_editor.get("1.0", tk.END)
        ranges = []
        for block_name in ["crosshair_distances{", "crosshair_hor_ranges{"]:
            start_idx = content.find(block_name)
            if start_idx != -1:
                open_brace = start_idx + len(block_name)
                close_brace = content.find("}", open_brace)
                if close_brace != -1: ranges.append((open_brace, close_brace))
        return ranges
        
    def is_pos_editable(self, pos, content):
        for start, end in self.get_editable_ranges():
            if start <= pos <= end: return True
        try:
            idx_str = self.text_editor.index(f"1.0 + {pos} chars")
            curr_line_idx = idx_str.split('.')[0]
            line_content = self.text_editor.get(f"{curr_line_idx}.0", f"{curr_line_idx}.end")
            if "=" in line_content:
                eq_char_offset = line_content.find("=")
                allowed_start_pos = self.text_editor.count("1.0", f"{curr_line_idx}.{eq_char_offset}", "chars")[0] + 2
                if pos >= allowed_start_pos: return True
        except Exception: pass
        return False
        
    def intercept_typing(self, event):
        if event.state & 4:
            if event.keysym.lower() in ['c', 'z', 's']: return None
        if event.keysym in ["Up", "Down", "Left", "Right", "Home", "End", "Prior", "Next"]: return None
        content = self.text_editor.get("1.0", tk.END)
        if self.text_editor.tag_ranges("sel"):
            try:
                sel_start = self.text_editor.count("1.0", "sel.first", "chars")[0]
                sel_end = self.text_editor.count("1.0", "sel.last", "chars")[0]
            except Exception: sel_start, sel_end = 0, 0
            if event.keysym not in ["BackSpace", "Delete"] and event.char == "": return None
            for p in range(sel_start, sel_end):
                if not self.is_pos_editable(p, content): return "break"
            return None
        try: insert_pos = self.text_editor.count("1.0", "insert", "chars")[0]
        except Exception: insert_pos = 0
        for start, end in self.get_editable_ranges():
            if start <= insert_pos <= end:
                if event.keysym == "BackSpace" and insert_pos == start: return "break"
                if event.keysym == "Delete" and insert_pos == end: return "break"
                return None
        curr_line_idx = self.text_editor.index("insert").split('.')[0]
        line_content = self.text_editor.get(f"{curr_line_idx}.0", f"{curr_line_idx}.end")
        if "=" in line_content:
            eq_char_offset = line_content.find("=")
            allowed_start_pos = self.text_editor.count("1.0", f"{curr_line_idx}.{eq_char_offset}", "chars")[0] + 2
            if event.keysym == "BackSpace":
                if insert_pos <= allowed_start_pos: return "break"
            elif event.keysym == "Delete":
                if insert_pos < allowed_start_pos: return "break"
            else:
                if insert_pos < allowed_start_pos: return "break"
            return None
        return "break"
        
    def toggle_settings(self):
        if not self.settings_expanded:
            self.settings_subframe.pack(fill="both", expand=True, padx=18)
            self.settings_btn.config(bg=self.bg_widgets, fg=self.fg_primary)
            self.settings_expanded = True
        else:
            self.settings_subframe.pack_forget()
            self.settings_btn.config(bg=self.bg_main, fg=self.fg_muted)
            self.settings_expanded = False
            
    def change_sight_color(self, hex_code):
        self.sight_color = hex_code
        for i, (_, h) in enumerate(self.color_palette):
            if h == hex_code:
                self.current_color_idx = i
                break
        self.redraw_sight()
        
    def handle_zoom(self, event):
        mouse_x = event.x
        mouse_y = event.y
        center_x = self.canvas_w / 2
        center_y = self.canvas_h / 2
        orig_x = (mouse_x - center_x - self.offset_x) / self.zoom_scale
        orig_y = (mouse_y - center_y - self.offset_y) / self.zoom_scale
        if event.delta > 0: self.zoom_scale *= 1.15
        else:
            self.zoom_scale /= 1.15
            if self.zoom_scale < 0.3: self.zoom_scale = 0.3
        self.offset_x = mouse_x - center_x - (orig_x * self.zoom_scale)
        self.offset_y = mouse_y - center_y - (orig_y * self.zoom_scale)
        self.redraw_sight()
        self.track_coordinates(event)
        
    def start_pan(self, event):
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
    def pan_canvas(self, event):
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        self.offset_x += dx
        self.offset_y += dy
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        self.update_canvas_positions()
        self.track_coordinates(event)
        
    def track_coordinates(self, event):
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        center_x = self.canvas_w / 2
        center_y = self.canvas_h / 2
        
        wt_x = (event.x - center_x - self.offset_x) / ((self.canvas_w / 2.0) * self.zoom_scale)
        wt_y = (event.y - center_y - self.offset_y) / (self.canvas_h * self.zoom_scale)
        
        if self.zoom_scale == 1.0 and self.offset_x == 0.0 and self.offset_y == 0.0:
            if event.x <= 0: wt_x = -1.0
            elif event.x >= self.canvas_w - 1: wt_x = 1.0
            if event.y <= 0: wt_y = -0.5
            elif event.y >= self.canvas_h - 1: wt_y = 0.5
            
        self.canvas.coords(self.coord_text_id, 15, 15)
        self.canvas.itemconfig(self.coord_text_id, text=f"X: {wt_x:+.4f}\nY: {wt_y:+.4f}")
        
    def reset_view(self):
        self.zoom_scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0 
        self.redraw_sight()
        
    def clear_canvas(self):
        self.current_file_path = None
        self.current_json_data = {}
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", DEFAULT_HEADER)
        self.reset_view()
        self.log_message("Статус: Рабочая среда успешно очищена", self.fg_muted)

    def init_canvas_objects(self):
        for _ in range(120):
            self.grid_line_ids.append(self.canvas.create_line(0, 0, 0, 0, fill="#131313", width=1))
        
        self.axis_line_ids.append(self.canvas.create_line(0, 0, 0, 0, fill="#222222", dash=(4, 4)))
        self.axis_line_ids.append(self.canvas.create_line(0, 0, 0, 0, fill="#222222", dash=(4, 4)))
        
        for _ in range(4):
            self.frame_line_ids.append(self.canvas.create_line(0, 0, 0, 0, fill="#2a2a2a", dash=(4, 4), width=1))
            
        self.coord_text_id = self.canvas.create_text(15, 15, anchor="nw", text="", fill=self.fg_muted, font=("Consolas", 10, "bold"))

    def to_pixels(self, val, is_y=False):
        if is_y:
            center_y = self.canvas_h / 2
            return center_y + (val * self.canvas_h) * self.zoom_scale + self.offset_y
        else:
            center_x = self.canvas_w / 2
            return center_x + (val * (self.canvas_w / 2.0)) * self.zoom_scale + self.offset_x

    def update_canvas_positions(self):
        mid_x = self.canvas_w / 2 + self.offset_x
        mid_y = self.canvas_h / 2 + self.offset_y
        grid_step = 40 * self.zoom_scale 
        if grid_step < 5: grid_step = 5
        
        line_idx = 0
        max_lines = len(self.grid_line_ids)
        
        x = mid_x
        while x < self.canvas_w and line_idx < max_lines:
            self.canvas.coords(self.grid_line_ids[line_idx], x, 0, x, self.canvas_h)
            x += grid_step
            line_idx += 1
        x = mid_x - grid_step
        while x > 0 and line_idx < max_lines:
            self.canvas.coords(self.grid_line_ids[line_idx], x, 0, x, self.canvas_h)
            x -= grid_step
            line_idx += 1
        y = mid_y
        while y < self.canvas_h and line_idx < max_lines:
            self.canvas.coords(self.grid_line_ids[line_idx], 0, y, self.canvas_w, y)
            y += grid_step
            line_idx += 1
        y = mid_y - grid_step
        while y > 0 and line_idx < max_lines:
            self.canvas.coords(self.grid_line_ids[line_idx], 0, y, self.canvas_w, y)
            y -= grid_step
            line_idx += 1
            
        while line_idx < max_lines:
            self.canvas.coords(self.grid_line_ids[line_idx], -10, -10, -10, -10)
            line_idx += 1
            
        self.canvas.coords(self.axis_line_ids[0], mid_x, 0, mid_x, self.canvas_h)
        self.canvas.coords(self.axis_line_ids[1], 0, mid_y, self.canvas_w, mid_y)
        
        x_min = self.to_pixels(-1.0)
        x_max = self.to_pixels(1.0)
        y_min = self.to_pixels(-0.5, True)
        y_max = self.to_pixels(0.5, True)
        
        self.canvas.coords(self.frame_line_ids[0], x_min + 1, y_min + 1, x_max - 2, y_min + 1)
        self.canvas.coords(self.frame_line_ids[1], x_max - 2, y_min + 1, x_max - 2, y_max)
        self.canvas.coords(self.frame_line_ids[2], x_max - 2, y_max, x_min + 1, y_max)
        self.canvas.coords(self.frame_line_ids[3], x_min + 1, y_max, x_min + 1, y_min + 1)
        
        if self.current_json_data and len(self.sight_element_ids) == len(self.current_json_data):
            for obj_id, val in zip(self.sight_element_ids, self.current_json_data.values()):
                if val.get("type") == "line":
                    self.canvas.coords(
                        obj_id,
                        self.to_pixels(val["start"]["x"]), self.to_pixels(val["start"]["y"], True),
                        self.to_pixels(val["end"]["x"]), self.to_pixels(val["end"]["y"], True)
                    )
                elif val.get("type") == "quad":
                    self.canvas.coords(
                        obj_id,
                        self.to_pixels(val["pos1"]["x"]), self.to_pixels(val["pos1"]["y"], True),
                        self.to_pixels(val["pos2"]["x"]), self.to_pixels(val["pos2"]["y"], True),
                        self.to_pixels(val["pos3"]["x"]), self.to_pixels(val["pos3"]["y"], True),
                        self.to_pixels(val["pos4"]["x"]), self.to_pixels(val["pos4"]["y"], True)
                    )

    def redraw_sight(self):
        if self.sight_element_ids:
            for el_id in self.sight_element_ids:
                self.canvas.delete(el_id)
            self.sight_element_ids.clear()
            
        if not self.current_json_data:
            self.update_canvas_positions()
            return
            
        for val in self.current_json_data.values():
            if val.get("type") == "line":
                line_id = self.canvas.create_line(0, 0, 0, 0, fill=self.sight_color, width=1)
                self.sight_element_ids.append(line_id)
            elif val.get("type") == "quad":
                quad_id = self.canvas.create_polygon(0, 0, 0, 0, 0, 0, 0, 0, outline=self.sight_color, fill=self.sight_color, width=1, smooth=True)
                self.sight_element_ids.append(quad_id)
                
        self.update_canvas_positions()
                
    def process_file(self, file_path):
        if isinstance(file_path, bytes): 
            try: file_path = file_path.decode('cp1251')
            except UnicodeDecodeError: file_path = file_path.decode('utf-8', errors='ignore')
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.blk':
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: content = f.read()
                extract_header_and_lines(content)
                if saved_blk_header.strip():
                    self.text_editor.delete("1.0", tk.END)
                    self.text_editor.insert("1.0", saved_blk_header)
                json_data = parse_blk_to_json(content)
                if not json_data: raise Exception("В файле BLK не найдено подходящих элементов.")
                self.current_json_data = json_data
                self.current_file_path = file_path
                self.redraw_sight()
                self.log_message(f"Статус: Импортирован файл {os.path.basename(file_path)}. Готов к конвертации.", self.fg_accent)
            except Exception as e: self.log_message(f"Ошибка: {str(e)}", "#ff4d4d")
        elif ext == '.json':
            try:
                with open(file_path, 'r', encoding='utf-8') as f: json_data = json.load(f)
                self.current_json_data = json_data
                self.current_file_path = file_path
                self.redraw_sight()
                self.log_message(f"Статус: Загружен JSON {os.path.basename(file_path)}. Готов к сборке в BLK.", self.fg_accent)
            except Exception as e: self.log_message(f"Ошибка: {str(e)}", "#ff4d4d")

    def trigger_conversion_hotkey(self):
        self.trigger_conversion()
        return "break"

    def trigger_conversion(self):
        if not self.current_file_path:
            self.log_message("Ошибка: Сначала импортируйте исходный файл!", "#ff4d4d")
            return
            
        ext = os.path.splitext(self.current_file_path)[1].lower()
        if ext == '.blk':
            try:
                output_path = os.path.splitext(self.current_file_path)[0] + '.json'
                with open(output_path, 'w', encoding='utf-8') as f: 
                    json.dump(self.current_json_data, f, separators=(',', ':'), ensure_ascii=False)
                self.log_message(f"Успешно: Файл JSON сгенерирован -> {os.path.basename(output_path)}", self.fg_accent)
            except Exception as e: 
                self.log_message(f"Ошибка сохранения JSON: {str(e)}", "#ff4d4d")
        elif ext == '.json':
            try:
                blk_content = pack_json_to_blk(self.current_json_data, self.text_editor.get("1.0", tk.END))
                output_path = os.path.splitext(self.current_file_path)[0] + '_packed.blk'
                with open(output_path, 'w', encoding='utf-8') as f: 
                    f.write(blk_content)
                self.log_message(f"Успешно: Файл BLK собран -> {os.path.basename(output_path)}", self.fg_accent)
            except Exception as e: 
                self.log_message(f"Ошибка сборки BLK: {str(e)}", "#ff4d4d")
            
    def reload_current_file(self):
        if self.current_file_path and os.path.exists(self.current_file_path):
            self.process_file(self.current_file_path)
            text = self.status_label.cget("text")
            if not text.startswith("Обновлено:"):
                self.status_label.config(text=f"Обновлено: {text}")
            
    def handle_drop(self, files):
        if files: self.process_file(files[0])
        
    def handle_click(self, event):
        file_path = filedialog.askopenfilename(filetypes=[("WT Файлы", "*.blk;*.json")])
        if file_path: self.process_file(file_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()
