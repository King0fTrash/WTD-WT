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

def extract_header_and_lines(blk_text):
    global saved_blk_header
    match = re.search(r'(drawLines\s*\{)', blk_text)
    if match: saved_blk_header = blk_text[:match.start()].strip() + "\n\n"
    else: saved_blk_header = ""

def parse_blk_to_json(blk_text):
    result = {}
    element_id = 0
    for block in re.findall(r'line\s*\{[^}]+\}', blk_text):
        p4_match = re.search(r'line:p4\s*=\s*([^;}\s]+)', block)
        if p4_match:
            try:
                coords = [float(x) for x in p4_match.group(1).split(',')]
                if len(coords) == 4:
                    result[str(element_id)] = {
                        "name": f"Линия{element_id}", "type": "line",
                        "start": {"x": coords[0], "y": coords[1]}, "end": {"x": coords[2], "y": coords[3]},
                        "selected": False
                    }
                    element_id += 1
            except ValueError: continue
            
    for block in re.findall(r'quad\s*\{[^}]+\}', blk_text):
        tl = re.search(r'tl:p2\s*=\s*([^;}\s]+)', block)
        tr = re.search(r'tr:p2\s*=\s*([^;}\s]+)', block)
        br = re.search(r'br:p2\s*=\s*([^;}\s]+)', block)
        bl = re.search(r'bl:p2\s*=\s*([^;}\s]+)', block)
        if tl and tr and br and bl:
            try:
                result[str(element_id)] = {
                    "name": f"Четырёхугольник{element_id}", "type": "quad",
                    "pos1": {"x": float(tl.group(1).split(',')[0]), "y": float(tl.group(1).split(',')[1])},
                    "pos2": {"x": float(tr.group(1).split(',')[0]), "y": float(tr.group(1).split(',')[1])},
                    "pos3": {"x": float(br.group(1).split(',')[0]), "y": float(br.group(1).split(',')[1])},
                    "pos4": {"x": float(bl.group(1).split(',')[0]), "y": float(bl.group(1).split(',')[1])},
                    "selected": False
                }
                element_id += 1
            except ValueError: continue
    return result

def pack_json_to_blk(json_data, current_editor_text):
    blk_elements = []
    for key in sorted(json_data.keys(), key=lambda x: int(x) if x.isdigit() else x):
        el = json_data[key]
        if el.get("type") == "line":
            blk_elements.append(f"  line {{line:p4={el['start']['x']},{el['start']['y']},{el['end']['x']},{el['end']['y']}; move:b=false;}}\n")
        elif el.get("type") == "quad":
            blk_elements.append(f"  quad {{tl:p2={el['pos1']['x']},{el['pos1']['y']}; tr:p2={el['pos2']['x']},{el['pos2']['y']}; br:p2={el['pos3']['x']},{el['pos3']['y']}; bl:p2={el['pos4']['x']},{el['pos4']['y']};}}\n")
    return (current_editor_text.strip() + "\n\n" if current_editor_text.strip() else DEFAULT_HEADER) + f"drawLines{{\n{''.join(blk_elements)}}}"

class ConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("WTDraw ⇄ War Thunder BLK")
        self.root.geometry("840x620")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e1e")
        self.root.after(100, self.apply_dark_theme)
        
        # --- Настройка иконки для окна и таскбара ---
        icon_name = "ico.ico"
        if getattr(sys, 'frozen', False):
            icon_path = os.path.join(sys._MEIPASS, icon_name)
        else:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), icon_name)

        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
                import ctypes
                myappid = 'wtdraw.converter.blkjson.v1'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception:
                pass
        # ---------------------------------------------
        
        self.current_json_data = {}
        self.canvas_w = 800
        self.canvas_h = 450
        self.sight_color = "#00ffff" 
        self.settings_expanded = False
        
        self.main_frame = tk.Frame(root, bg="#1e1e1e", width=840, height=620)
        self.main_frame.pack(side="left", fill="both", expand=True)
        self.main_frame.pack_propagate(False)
        
        self.drop_label = tk.Label(
            self.main_frame, 
            text="Перетащи сюда .blk (в JSON) или .json (в BLK)\nили кликни для выбора файла", 
            relief="flat", bg="#2d2d2d", fg="#ffffff", font=("Arial", 10, "bold"), height=3
        )
        self.drop_label.pack(fill="x", padx=20, pady=15)
        self.drop_label.bind("<Button-1>", self.handle_click)
        self.drop_label.bind("<Enter>", lambda e: self.drop_label.config(bg="#3d3d3d"))
        self.drop_label.bind("<Leave>", lambda e: self.drop_label.config(bg="#2d2d2d"))
        
        self.canvas = tk.Canvas(self.main_frame, width=self.canvas_w, height=self.canvas_h, bg="#0b0b0b", highlightbackground="#2d2d2d", highlightthickness=1)
        self.canvas.pack(padx=20, pady=5)
        self.draw_center_cross()
        
        self.bottom_bar = tk.Frame(self.main_frame, bg="#121212")
        self.bottom_bar.pack(fill="x", side="bottom")
        
        self.status_label = tk.Label(self.bottom_bar, text="Статус: Ожидание файла (.blk или .json)...", bd=0, relief="flat", anchor="w", bg="#121212", fg="#aaaaaa", font=("Arial", 10), padx=10)
        self.status_label.pack(side="left", fill="x", expand=True, ipady=8)
        
        self.settings_btn = tk.Button(self.bottom_bar, text="⚙ Настройки BLK", bg="#2a2a2a", fg="#ffffff", relief="flat", activebackground="#3a3a3a", font=("Arial", 9, "bold"), padx=10, command=self.toggle_settings)
        self.settings_btn.pack(side="right", padx=10, pady=4)

        self.settings_frame = tk.Frame(root, bg="#252525", width=360, height=620)
        self.settings_title = tk.Label(self.settings_frame, text="Переменные и Шаблон заголовка BLK:", bg="#252525", fg="#00ffff", font=("Arial", 10, "bold"), anchor="w")
        self.settings_title.pack(fill="x", padx=15, pady=(15, 5))
        
        self.text_editor = tk.Text(self.settings_frame, bg="#1a1a1a", fg="#e0e0e0", insertbackground="#ffffff", selectbackground="#444444", font=("Consolas", 10), relief="flat", undo=True, maxundo=100)
        self.text_editor.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", DEFAULT_HEADER)
        
        self.text_editor.bind("<Key>", self.intercept_typing)
        windnd.hook_dropfiles(self.root, func=self.handle_drop)

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
                if close_brace != -1:
                    ranges.append((open_brace, close_brace))
        return ranges

    def is_pos_editable(self, pos, content):
        for start, end in self.get_editable_ranges():
            if start <= pos <= end:
                return True
        
        try:
            idx_str = self.text_editor.index(f"1.0 + {pos} chars")
            curr_line_idx = idx_str.split('.')[0]
            line_content = self.text_editor.get(f"{curr_line_idx}.0", f"{curr_line_idx}.end")
            if "=" in line_content:
                eq_char_offset = line_content.find("=")
                allowed_start_pos = self.text_editor.count("1.0", f"{curr_line_idx}.{eq_char_offset}", "chars")[0] + 2
                if pos >= allowed_start_pos:
                    return True
        except Exception: pass
        return False

    def intercept_typing(self, event):
        if event.state & 4:
            if event.keysym.lower() in ['c', 'z']:
                return None

        if event.keysym in ["Up", "Down", "Left", "Right", "Home", "End", "Prior", "Next"]:
            return None

        content = self.text_editor.get("1.0", tk.END)
        
        if self.text_editor.tag_ranges("sel"):
            try:
                sel_start = self.text_editor.count("1.0", "sel.first", "chars")[0]
                sel_end = self.text_editor.count("1.0", "sel.last", "chars")[0]
            except Exception:
                sel_start, sel_end = 0, 0
                
            if event.keysym not in ["BackSpace", "Delete"] and event.char == "":
                return None
                
            for p in range(sel_start, sel_end):
                if not self.is_pos_editable(p, content):
                    return "break"
            return None

        try:
            insert_pos = self.text_editor.count("1.0", "insert", "chars")[0]
        except Exception:
            insert_pos = 0

        for start, end in self.get_editable_ranges():
            if start <= insert_pos <= end:
                if event.keysym == "BackSpace" and insert_pos == start:
                    return "break"
                if event.keysym == "Delete" and insert_pos == end:
                    return "break"
                return None

        curr_line_idx = self.text_editor.index("insert").split('.')[0]
        line_content = self.text_editor.get(f"{curr_line_idx}.0", f"{curr_line_idx}.end")
        
        if "=" in line_content:
            eq_char_offset = line_content.find("=")
            allowed_start_pos = self.text_editor.count("1.0", f"{curr_line_idx}.{eq_char_offset}", "chars")[0] + 2
            
            if event.keysym == "BackSpace":
                if insert_pos <= allowed_start_pos:
                    return "break"
            elif event.keysym == "Delete":
                if insert_pos < allowed_start_pos:
                    return "break"
            else:
                if insert_pos < allowed_start_pos:
                    return "break"
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

    def draw_center_cross(self):
        mid_x, mid_y = self.canvas_w / 2, self.canvas_h / 2
        self.canvas.create_line(mid_x, 0, mid_x, self.canvas_h, fill="#252525", dash=(4, 4))
        self.canvas.create_line(0, mid_y, self.canvas_w, mid_y, fill="#252525", dash=(4, 4))

    def to_pixels(self, val, is_y=False):
        return (self.canvas_h / 2 + (val * self.canvas_h)) if is_y else (self.canvas_w / 2 + (val * (self.canvas_w / 2)))

    def redraw_sight(self):
        self.canvas.delete("all")
        self.draw_center_cross()
        if not self.current_json_data: return
        for val in self.current_json_data.values():
            if val.get("type") == "line":
                self.canvas.create_line(self.to_pixels(val["start"]["x"]), self.to_pixels(val["start"]["y"], True), self.to_pixels(val["end"]["x"]), self.to_pixels(val["end"]["y"], True), fill=self.sight_color, width=1.2)
            elif val.get("type") == "quad":
                self.canvas.create_polygon(self.to_pixels(val["pos1"]["x"]), self.to_pixels(val["pos1"]["y"], True), self.to_pixels(val["pos2"]["x"]), self.to_pixels(val["pos2"]["y"], True), self.to_pixels(val["pos3"]["x"]), self.to_pixels(val["pos3"]["y"], True), self.to_pixels(val["pos4"]["x"]), self.to_pixels(val["pos4"]["y"], True), outline=self.sight_color, fill="", width=1.2)

    def process_file(self, file_path):
        if isinstance(file_path, bytes): file_path = file_path.decode('utf-8')
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
                
                # --- ТУТ ИСПРАВЛЕНО (Добавлен ensure_ascii=False как в старой версии) ---
                with open(output_path, 'w', encoding='utf-8') as f: 
                    json.dump(json_data, f, separators=(',', ':'), ensure_ascii=False)
                
                self.current_json_data = json_data
                self.redraw_sight()
                self.status_label.config(text=f"[SUCCESS] Сгенерирован JSON: {os.path.basename(output_path)}", fg="#00ff66")
            except Exception as e: self.status_label.config(text=f"[ERROR] Ошибка BLK: {str(e)}", fg="#ff4d4d")
        elif ext == '.json':
            try:
                with open(file_path, 'r', encoding='utf-8') as f: json_data = json.load(f)
                self.current_json_data = json_data
                self.redraw_sight()
                blk_content = pack_json_to_blk(json_data, self.text_editor.get("1.0", tk.END))
                output_path = os.path.splitext(file_path)[0] + '_packed.blk'
                with open(output_path, 'w', encoding='utf-8') as f: f.write(blk_content)
                self.status_label.config(text=f"[SUCCESS] Собрано в оригинальный BLK!", fg="#00ffff")
            except Exception as e: self.status_label.config(text=f"[ERROR] Ошибка JSON: {str(e)}", fg="#ff4d4d")

    def handle_drop(self, files):
        if files: self.process_file(files[0])

    def handle_click(self, event):
        file_path = filedialog.askopenfilename(filetypes=[("WT Файлы", "*.blk;*.json")])
        if file_path: self.process_file(file_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = ConverterApp(root)
    root.mainloop()