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
        self.root.geometry("840x620")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e1e")
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
        self.canvas_w = 800
        self.canvas_h = 450
        self.sight_color = "#00ffff" 
        self.settings_expanded = False
        
        self.color_palette = [
            ("Голубой", "#00ffff"), 
            ("Зелёный", "#1fef1f"), 
            ("Красный", "#ff1e1e"), 
            ("Белый", "#ffffff"), 
            ("Жёлтый", "#ffff00")
        ]
        self.current_color_idx = 0
        
        self.zoom_scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        self.main_frame = tk.Frame(root, bg="#1e1e1e", width=840, height=620)
        self.main_frame.pack(side="left", fill="both", expand=True)
        self.main_frame.pack_propagate(False)
        
        self.drop_label = tk.Label(
            self.main_frame, text="Перетащи сюда .blk (в JSON) или .json (в BLK)\nили кликни для выбора файла", 
            relief="flat", bg="#2d2d2d", fg="#ffffff", font=("Arial", 10, "bold"), height=3
        )
        self.drop_label.pack(fill="x", padx=20, pady=15)
        self.drop_label.bind("<Button-1>", self.handle_click)
        self.drop_label.bind("<Enter>", lambda e: self.drop_label.config(bg="#3d3d3d"))
        self.drop_label.bind("<Leave>", lambda e: self.drop_label.config(bg="#2d2d2d"))
        
        self.canvas_container = tk.Frame(self.main_frame, bg="#1e1e1e")
        self.canvas_container.pack(padx=20, pady=5)
        
        self.canvas = tk.Canvas(self.canvas_container, width=self.canvas_w, height=self.canvas_h, bg="#0b0b0b", highlightbackground="#2d2d2d", highlightthickness=1)
        self.canvas.pack()
        
        self.canvas.bind("<MouseWheel>", self.handle_zoom)
        self.canvas.bind("<ButtonPress-3>", self.start_pan)
        self.canvas.bind("<B3-Motion>", self.pan_canvas)
        self.canvas.bind("<Motion>", self.track_coordinates)
        
        self.bottom_bar = tk.Frame(self.main_frame, bg="#121212")
        self.bottom_bar.pack(fill="x", side="bottom")
        
        self.status_label = tk.Label(self.bottom_bar, text="Статус: Ожидание файла (.blk или .json)...", bd=0, relief="flat", anchor="w", bg="#121212", fg="#aaaaaa", font=("Arial", 10), padx=10)
        self.status_label.pack(side="left", fill="x", expand=True, ipady=8)
        
        self.clear_btn = tk.Button(self.bottom_bar, text="❌ Очистить", bg="#2a2a2a", fg="#ff4d4d", relief="flat", activebackground="#3a1a1a", font=("Arial", 9, "bold"), padx=10, command=self.clear_canvas)
        self.clear_btn.pack(side="right", padx=(0, 5), pady=4)
        
        self.reset_zoom_btn = tk.Button(self.bottom_bar, text="🔍 Сброс зума", bg="#2a2a2a", fg="#ffffff", relief="flat", activebackground="#3a3a3a", font=("Arial", 9, "bold"), padx=10, command=self.reset_view)
        self.reset_zoom_btn.pack(side="right", padx=(0, 5), pady=4)

        self.settings_btn = tk.Button(self.bottom_bar, text="⚙ Настройки BLK", bg="#2a2a2a", fg="#ffffff", relief="flat", activebackground="#3a3a3a", font=("Arial", 9, "bold"), padx=10, command=self.toggle_settings)
        self.settings_btn.pack(side="right", padx=10, pady=4)

        self.settings_frame = tk.Frame(root, bg="#252525", width=360, height=620)
        
        self.color_bar = tk.Frame(self.settings_frame, bg="#252525")
        self.color_bar.pack(fill="x", padx=15, pady=15)
        
        self.color_label = tk.Label(self.color_bar, text="Цвет прицела ↕:", bg="#252525", fg="#00ffff", font=("Arial", 9, "bold"), cursor="sb_v_double_arrow")
        self.color_label.pack(side="left", padx=(0, 5))
        self.color_label.bind("<MouseWheel>", self.handle_color_scroll)
        
        for name, hex_code in self.color_palette:
            btn = tk.Button(self.color_bar, text=name[:1], bg=hex_code if hex_code != "#ffffff" else "#e0e0e0", 
                            fg="#000000" if hex_code in ["#00ffff", "#1fef1f", "#ffffff", "#ffff00"] else "#ffffff",
                            relief="flat", font=("Arial", 8, "bold"), width=3, command=lambda c=hex_code: self.change_sight_color(c))
            btn.pack(side="left", padx=2)

        self.settings_title = tk.Label(self.settings_frame, text="Переменные и Шаблон заголовка BLK:", bg="#252525", fg="#888888", font=("Arial", 9, "bold"), anchor="w")
        self.settings_title.pack(fill="x", padx=15, pady=(0, 5))
        self.text_editor = tk.Text(self.settings_frame, bg="#1a1a1a", fg="#e0e0e0", insertbackground="#ffffff", selectbackground="#444444", font=("Consolas", 10), relief="flat", undo=True, maxundo=100)
        self.text_editor.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", DEFAULT_HEADER)
        self.text_editor.bind("<Key>", self.intercept_typing)
        
        self.root.bind("<F5>", lambda e: self.reload_current_file())
        
        windnd.hook_dropfiles(self.root, func=self.handle_drop)
        self.redraw_sight()

    def apply_dark_theme(self):
        try: pywinstyles.apply_style(self.root, "dark")
        except Exception: pass
        
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
            if event.keysym.lower() in ['c', 'z']: return None
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
            self.root.geometry("1200x620")
            self.settings_frame.pack(side="right", fill="both", expand=True)
            self.settings_frame.pack_propagate(False)
            self.settings_btn.config(bg="#00ffff", fg="#121212")
            self.settings_expanded = True
        else:
            self.settings_frame.pack_forget()
            self.root.geometry("840x620")
            self.settings_btn.config(bg="#2a2a2a", fg="#ffffff")
            self.settings_expanded = False
            
    def change_sight_color(self, hex_code):
        self.sight_color = hex_code
        for i, (_, h) in enumerate(self.color_palette):
            if h == hex_code:
                self.current_color_idx = i
                break
        self.redraw_sight()
        
    def handle_color_scroll(self, event):
        if event.delta > 0:
            self.current_color_idx = (self.current_color_idx - 1) % len(self.color_palette)
        else:
            self.current_color_idx = (self.current_color_idx + 1) % len(self.color_palette)
        self.sight_color = self.color_palette[self.current_color_idx][1]
        self.redraw_sight()
        
    def handle_zoom(self, event):
        mouse_x = event.x
        mouse_y = event.y
        old_scale = self.zoom_scale
        if event.delta > 0: self.zoom_scale *= 1.15
        else:
            self.zoom_scale /= 1.15
            if self.zoom_scale < 0.3: self.zoom_scale = 0.3
        factor = self.zoom_scale / old_scale
        self.offset_x = mouse_x - factor * (mouse_x - self.offset_x)
        self.offset_y = mouse_y - factor * (mouse_y - self.offset_y)
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
        self.redraw_sight()
        self.track_coordinates(event)
        
    def track_coordinates(self, event):
        center_x = self.canvas_w / 2
        center_y = self.canvas_h / 2
        wt_x = (event.x - center_x - self.offset_x) / ((self.canvas_w / 2) * self.zoom_scale)
        wt_y = (event.y - center_y - self.offset_y) / (self.canvas_h * self.zoom_scale)
        self.canvas.delete("coord_text")
        self.canvas.create_text(
            15, 15, anchor="nw", 
            text=f"X: {wt_x:+.4f}\nY: {wt_y:+.4f}", 
            fill="#aaaaaa", font=("Consolas", 10, "bold"), tags="coord_text"
        )
        
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
        self.status_label.config(text="Статус: Холст очищен. Ожидание файла...", fg="#aaaaaa")
        
    def draw_grid_and_cross(self):
        mid_x = self.canvas_w / 2 + self.offset_x
        mid_y = self.canvas_h / 2 + self.offset_y
        grid_step = 50 * self.zoom_scale
        if grid_step < 5: grid_step = 5
        x = mid_x
        while x < self.canvas_w:
            self.canvas.create_line(x, 0, x, self.canvas_h, fill="#161616", width=1)
            x += grid_step
        x = mid_x - grid_step
        while x > 0:
            self.canvas.create_line(x, 0, x, self.canvas_h, fill="#161616", width=1)
            x -= grid_step
        y = mid_y
        while y < self.canvas_h:
            self.canvas.create_line(0, y, self.canvas_w, y, fill="#161616", width=1)
            y += grid_step
        y = mid_y - grid_step
        while y > 0:
            self.canvas.create_line(0, y, self.canvas_w, y, fill="#161616", width=1)
            y -= grid_step
        self.canvas.create_line(mid_x, 0, mid_x, self.canvas_h, fill="#2a2a2a", dash=(4, 4))
        self.canvas.create_line(0, mid_y, self.canvas_w, mid_y, fill="#2a2a2a", dash=(4, 4))
        
    def to_pixels(self, val, is_y=False):
        if is_y:
            center_y = self.canvas_h / 2
            return center_y + (val * self.canvas_h) * self.zoom_scale + self.offset_y
        else:
            center_x = self.canvas_w / 2
            return center_x + (val * (self.canvas_w / 2)) * self.zoom_scale + self.offset_x
            
    def redraw_sight(self):
        self.canvas.delete("all")
        self.draw_grid_and_cross()
        if not self.current_json_data: return
        for val in self.current_json_data.values():
            if val.get("type") == "line":
                self.canvas.create_line(
                    self.to_pixels(val["start"]["x"]), self.to_pixels(val["start"]["y"], True), 
                    self.to_pixels(val["end"]["x"]), self.to_pixels(val["end"]["y"], True), 
                    fill=self.sight_color, width=1
                )
            elif val.get("type") == "quad":
                self.canvas.create_polygon(
                    self.to_pixels(val["pos1"]["x"]), self.to_pixels(val["pos1"]["y"], True), 
                    self.to_pixels(val["pos2"]["x"]), self.to_pixels(val["pos2"]["y"], True), 
                    self.to_pixels(val["pos3"]["x"]), self.to_pixels(val["pos3"]["y"], True), 
                    self.to_pixels(val["pos4"]["x"]), self.to_pixels(val["pos4"]["y"], True), 
                    outline=self.sight_color, fill=self.sight_color, width=1
                )
                
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
                if not json_data: raise Exception("В BLK не найдено элементов.")
                output_path = os.path.splitext(file_path)[0] + '.json'
                with open(output_path, 'w', encoding='utf-8') as f: json.dump(json_data, f, separators=(',', ':'), ensure_ascii=False)
                self.current_json_data = json_data
                self.current_file_path = file_path
                self.reset_view()
                self.status_label.config(text=f"[SUCCESS] Сгенерирован JSON: {os.path.basename(output_path)}", fg="#00ff66")
            except Exception as e: self.status_label.config(text=f"[ERROR] Ошибка BLK: {str(e)}", fg="#ff4d4d")
        elif ext == '.json':
            try:
                with open(file_path, 'r', encoding='utf-8') as f: json_data = json.load(f)
                self.current_json_data = json_data
                self.current_file_path = file_path
                self.reset_view()
                blk_content = pack_json_to_blk(json_data, self.text_editor.get("1.0", tk.END))
                output_path = os.path.splitext(file_path)[0] + '_packed.blk'
                with open(output_path, 'w', encoding='utf-8') as f: f.write(blk_content)
                self.status_label.config(text=f"[SUCCESS] Собрано в оригинальный BLK!", fg="#00ffff")
            except Exception as e: self.status_label.config(text=f"[ERROR] Ошибка JSON: {str(e)}", fg="#ff4d4d")
            
    def reload_current_file(self):
        if self.current_file_path and os.path.exists(self.current_file_path):
            self.process_file(self.current_file_path)
            text = self.status_label.cget("text")
            self.status_label.config(text=f"[🔄 ОБНОВЛЕНО] {text}")
            
    def handle_drop(self, files):
        if files: self.process_file(files[0])
        
    def handle_click(self, event):
        file_path = filedialog.askopenfilename(filetypes=[("WT Файлы", "*.blk;*.json")])
        if file_path: self.process_file(file_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()
