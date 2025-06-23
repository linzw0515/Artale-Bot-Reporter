import os
import re
import json
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox, filedialog
from scapy.all import AsyncSniffer, TCP
import cv2
import numpy as np
import pygetwindow as gw
import threading
import time
from datetime import datetime
from typing import List, Dict, Optional

# Constants
class Config:
    DEFAULT_PORT = 32800
    DEFAULT_FPS = 15
    DEFAULT_QUALITY = "低"
    DEFAULT_SCALE = "50%"
    MAX_FILE_SIZE = 90 * 1024 * 1024  # 90MB
    KOREAN_CHINESE_FILE = 'korean_chinese.json'
    USER_CONFIG_FILE = 'user_config.json'
    RECORDINGS_DIR = "recordings"
    
    # Video settings
    VIDEO_CODECS = ['avc1', 'mp4v']  # Primary and fallback codecs
    QUALITY_SETTINGS = {
        "低": {"crf": 28, "preset": "fast"},
        "中等": {"crf": 23, "preset": "medium"},
        "高": {"crf": 18, "preset": "slow"},
        "超高": {"crf": 15, "preset": "slower"}
    }

class DataManager:
    """Handles data loading, saving and translation"""
    
    def __init__(self):
        self.job_map = {}
        self.map_map = {}
        self.load_translation_data()
    
    def load_translation_data(self):
        """Load Korean-Chinese translation mappings"""
        try:
            if os.path.exists(Config.KOREAN_CHINESE_FILE):
                with open(Config.KOREAN_CHINESE_FILE, 'r', encoding='utf-8') as f:
                    mapping = json.load(f)
                    self.job_map = mapping.get('職業對照', {})
                    self.map_map = mapping.get('地圖對照', {})
            else:
                messagebox.showwarning("警告", f"找不到 {Config.KOREAN_CHINESE_FILE} 檔案，將使用原始韓文顯示")
        except Exception as e:
            print(f"載入翻譯資料失敗: {e}")
    
    def load_user_config(self) -> str:
        """Load user configuration"""
        try:
            if os.path.exists(Config.USER_CONFIG_FILE):
                with open(Config.USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('last_character_name', '')
        except Exception as e:
            print(f"載入設定失敗: {e}")
        return ''
    
    def save_user_config(self, character_name: str):
        """Save user configuration"""
        try:
            config = {'last_character_name': character_name}
            with open(Config.USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存設定失敗: {e}")
    
    def translate_job(self, korean_job: str) -> str:
        """Translate Korean job name to Chinese"""
        return self.job_map.get(korean_job, korean_job)
    
    def translate_map(self, korean_map: str) -> str:
        """Translate Korean map name to Chinese"""
        return self.map_map.get(korean_map, korean_map)

class PacketProcessor:
    """Handles network packet processing"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.data_buffer = b''
    
    def process_packet_data(self, packet_data: bytes) -> List[Dict]:
        """Process packet data and extract player information"""
        self.data_buffer += packet_data
        players = []
        
        while True:
            start = self.data_buffer.find(b'TOZ ')
            if start < 0 or len(self.data_buffer) < start + 8:
                break
            
            length = int.from_bytes(self.data_buffer[start+4:start+8], 'little')
            if len(self.data_buffer) < start + 8 + length:
                break
            
            pkt_bytes = self.data_buffer[start:start+8+length]
            self.data_buffer = self.data_buffer[start+8+length:]
            
            extracted_players = self._extract_channel_players(pkt_bytes)
            if extracted_players:
                players.extend(extracted_players)
        
        return players
    
    def _extract_channel_players(self, pkt_bytes: bytes) -> List[Dict]:
        """Extract player information from packet bytes"""
        if len(pkt_bytes) < 8:
            return []
        
        try:
            text = pkt_bytes[8:].decode('utf-8', errors='ignore')
        except:
            return []
        
        players = []
        for m in re.finditer(r'(\d{17})', text):
            rest = text[m.end(1):].lstrip('/')
            parts = rest.split('/')
            if len(parts) < 7 or '#' not in parts[2]:
                continue
            
            id1, nick2 = parts[1], parts[2]
            nick, id2 = nick2.split('#', 1)
            if id1 != id2:
                continue
            
            kr_map = parts[3].strip()
            zh_map = self.data_manager.translate_map(kr_map)
            
            kr_job = parts[6].strip()
            zh_job = self.data_manager.translate_job(kr_job)
            
            players.append({
                'nickname': nick,
                'id': id1,
                'map_zh': zh_map,
                'level': parts[5].strip(),
                'job_zh': zh_job,
            })
        
        return players

class VideoRecorder:
    """Handles video recording functionality"""
    
    def __init__(self, output_dir: str, log_callback):
        self.output_dir = output_dir
        self.log_callback = log_callback
        self.recording = False
        self.video_writer = None
        self.recording_thread = None
        self.current_file_size = 0
        self.file_counter = 1
        self.frame_count = 0
        self.current_video_path = ""
        
        # Ensure output directory exists
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def start_recording(self, window, fps: int, scale: float):
        """Start video recording"""
        if self.recording:
            return False
        
        self.recording = True
        self.file_counter = 1
        self.current_file_size = 0
        self.selected_window = window
        self.fps = fps
        self.scale = scale
        
        self.recording_thread = threading.Thread(target=self._recording_loop, daemon=True)
        self.recording_thread.start()
        
        self.log_callback(f"🎬 開始錄製視窗：{window.title}")
        return True
    
    def stop_recording(self):
        """Stop video recording"""
        self.recording = False
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        self.log_callback("⏹️ 錄影已停止")
    
    def _recording_loop(self):
        """Main recording loop"""
        try:
            frame_duration = 1.0 / self.fps
            last_frame_time = time.time()
            
            while self.recording and self.selected_window:
                if not self._is_window_valid():
                    self.log_callback("⚠️ 目標視窗已關閉，停止錄影")
                    break
                
                frame = self._capture_frame()
                if frame is not None:
                    self._write_frame(frame)
                
                # Control frame rate
                current_time = time.time()
                elapsed_time = current_time - last_frame_time
                sleep_time = frame_duration - elapsed_time
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
                last_frame_time = time.time()
                
        except Exception as e:
            self.log_callback(f"❌ 錄影循環錯誤：{e}")
        finally:
            self.recording = False
            if self.video_writer:
                self.video_writer.release()
                self.video_writer = None
    
    def _is_window_valid(self) -> bool:
        """Check if the target window is still valid"""
        if not self.selected_window:
            return False
        
        return any(w.title == self.selected_window.title for w in gw.getAllWindows())
    
    def _capture_frame(self):
        """Capture a frame from the selected window"""
        try:
            import pyautogui
            
            if self.selected_window.isMinimized:
                self.selected_window.restore()
            
            left, top = self.selected_window.left, self.selected_window.top
            width, height = self.selected_window.width, self.selected_window.height
            
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Apply scaling
            if self.scale != 1.0:
                new_width = int(width * self.scale)
                new_height = int(height * self.scale)
                frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            
            return frame
            
        except Exception as e:
            self.log_callback(f"⚠️ 截圖錯誤：{e}")
            return None
    
    def _write_frame(self, frame):
        """Write frame to video file"""
        height, width = frame.shape[:2]
        
        # Create new video file if needed
        if self.video_writer is None or self.current_file_size >= Config.MAX_FILE_SIZE:
            if self.video_writer:
                self.video_writer.release()
            
            self._create_new_video_file(width, height)
        
        # Write frame
        if self.video_writer and self.video_writer.isOpened():
            self.video_writer.write(frame)
            self.frame_count += 1
            
            # Check file size every 10 frames
            if self.frame_count % 10 == 0:
                self._update_file_size()
    
    def _create_new_video_file(self, width: int, height: int):
        """Create a new video file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}_part{self.file_counter:03d}.mp4"
        self.current_video_path = os.path.join(self.output_dir, filename)
        
        # Try primary codec first, then fallback
        for codec in Config.VIDEO_CODECS:
            fourcc = cv2.VideoWriter_fourcc(*codec)
            self.video_writer = cv2.VideoWriter(
                self.current_video_path, fourcc, self.fps, (width, height)
            )
            
            if self.video_writer.isOpened():
                break
            else:
                self.log_callback(f"⚠️ 編碼器 {codec} 失敗，嘗試下一個")
        
        self.current_file_size = 0
        self.frame_count = 0
        self.log_callback(f"📄 開始新檔案：{filename}")
    
    def _update_file_size(self):
        """Update current file size"""
        try:
            if os.path.exists(self.current_video_path):
                self.current_file_size = os.path.getsize(self.current_video_path)
                
                if self.current_file_size >= Config.MAX_FILE_SIZE:
                    self.file_counter += 1
                    size_mb = self.current_file_size / (1024 * 1024)
                    self.log_callback(f"📄 檔案達到 {size_mb:.1f}MB，準備分割")
        except Exception:
            pass  # Ignore file size check errors
    
    def get_status_info(self) -> Dict:
        """Get current recording status information"""
        info = {
            'recording': self.recording,
            'file_counter': self.file_counter,
            'file_size_mb': self.current_file_size / (1024 * 1024) if self.current_file_size else 0
        }
        return info

class PlayerMonitorTab:
    """Handles the player monitoring UI tab"""
    
    def __init__(self, parent, data_manager: DataManager, packet_processor: PacketProcessor):
        self.parent = parent
        self.data_manager = data_manager
        self.packet_processor = packet_processor
        self.my_name = ""
        self.my_current_map = ""
        self.sniffer = None
        
        # Load last character name
        self.last_character_name = self.data_manager.load_user_config()
        
        self._create_widgets()
        self._start_packet_monitoring()
    
    def _create_widgets(self):
        """Create UI widgets for player monitoring"""
        # Top control area
        top_frame = ttk.Frame(self.parent)
        top_frame.pack(fill='x', padx=10, pady=10)
        
        # User name input
        name_frame = ttk.LabelFrame(top_frame, text="設定", padding=10)
        name_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(name_frame, text="請輸入您的角色名稱：").pack(anchor='w')
        self.name_var = tk.StringVar(value=self.last_character_name)
        name_entry = ttk.Entry(name_frame, textvariable=self.name_var, font=('Arial', 12))
        name_entry.pack(fill='x', pady=(5, 10))
        
        ttk.Button(name_frame, text="🔍 開始監控", command=self._set_character_name).pack(anchor='e')
        
        # Status display
        self._create_status_display(top_frame)
        
        # Current map info
        self._create_map_info_display()
        
        # Player list
        self._create_player_list()
        
        # Log area
        self._create_log_area()
    
    def _create_status_display(self, parent):
        """Create status display widgets"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(status_frame, text="監控狀態：").pack(side='left')
        self.status_canvas = tk.Canvas(status_frame, width=20, height=20, highlightthickness=0)
        self.status_light = self.status_canvas.create_oval(2, 2, 18, 18, fill='red')
        self.status_canvas.pack(side='left', padx=(5, 10))
        
        self.status_label = ttk.Label(status_frame, text="等待設定角色名稱...", foreground='gray')
        self.status_label.pack(side='left')
    
    def _create_map_info_display(self):
        """Create map information display"""
        map_frame = ttk.LabelFrame(self.parent, text="當前地圖資訊", padding=10)
        map_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.map_info_label = ttk.Label(map_frame, text="尚未檢測到您的位置", font=('Arial', 11))
        self.map_info_label.pack(anchor='w')
    
    def _create_player_list(self):
        """Create player list table"""
        players_frame = ttk.LabelFrame(self.parent, text="同地圖玩家", padding=10)
        players_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Create table
        columns = ('暱稱', 'ID', '等級', '職業')
        self.players_tree = ttk.Treeview(players_frame, columns=columns, show='headings', height=8)
        
        # Set column headers and widths
        for col in columns:
            self.players_tree.heading(col, text=col)
        
        self.players_tree.column('暱稱', width=120, anchor='w')
        self.players_tree.column('ID', width=150, anchor='w')
        self.players_tree.column('等級', width=80, anchor='center')
        self.players_tree.column('職業', width=120, anchor='w')
        
        # Bind context menu
        self.players_tree.bind('<Button-3>', self._show_context_menu)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(players_frame, orient='vertical', command=self.players_tree.yview)
        self.players_tree.configure(yscrollcommand=scrollbar.set)
        
        self.players_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Create context menu
        self._create_context_menu()
        
        # Configure style for player's own row
        self.players_tree.tag_configure('myself', background='#E8F4FD')
    
    def _create_context_menu(self):
        """Create right-click context menu"""
        self.context_menu = tk.Menu(self.parent, tearoff=0)
        self.context_menu.add_command(label="複製暱稱", command=lambda: self._copy_cell_data('暱稱'))
        self.context_menu.add_command(label="複製玩家ID", command=lambda: self._copy_cell_data('ID'))
        self.context_menu.add_command(label="複製名稱#ID", command=self._copy_name_id_format)
        self.context_menu.add_command(label="複製等級", command=lambda: self._copy_cell_data('等級'))
        self.context_menu.add_command(label="複製職業", command=lambda: self._copy_cell_data('職業'))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="複製整列", command=self._copy_entire_row)
    
    def _create_log_area(self):
        """Create log display area"""
        log_frame = ttk.LabelFrame(self.parent, text="監控日誌", padding=5)
        log_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.log = scrolledtext.ScrolledText(log_frame, state='disabled', wrap='word', height=6)
        self.log.pack(fill='both', expand=True)
    
    def _start_packet_monitoring(self):
        """Start packet monitoring"""
        try:
            self.sniffer = AsyncSniffer(
                filter=f'tcp port {Config.DEFAULT_PORT}',
                prn=self._process_packet,
                store=False
            )
            self.sniffer.start()
            self._set_status_light(True)
            self.log_message(f"🟢 封包監控已啟動 (TCP {Config.DEFAULT_PORT})")
        except Exception as e:
            self.log_message(f"❌ 啟動監控失敗：{e}")
            messagebox.showerror("錯誤", f"無法啟動封包監控：{e}")
    
    def _process_packet(self, pkt):
        """Process incoming packet"""
        if TCP not in pkt:
            return
        
        players = self.packet_processor.process_packet_data(bytes(pkt[TCP].payload))
        if players:
            # Use after method to safely update GUI from thread
            self.parent.after(0, lambda p=players: self._update_players(p))
    
    def _set_character_name(self):
        """Set the character name to monitor"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("警告", "請輸入角色名稱")
            return
        
        self.my_name = name
        self.data_manager.save_user_config(name)
        self.status_label.config(text=f"正在監控角色：{name}", foreground='blue')
        self.log_message(f"🎯 開始監控角色：{name}")
    
    def _update_players(self, players: List[Dict]):
        """Update player list based on detected players"""
        if not self.my_name:
            return
        
        # Find player's character
        my_player = next((p for p in players if p['nickname'] == self.my_name), None)
        
        if not my_player:
            self.map_info_label.config(text=f"未找到角色 '{self.my_name}' 在頻道中")
            self._clear_players_table()
            return
        
        # Update current map info
        current_map = my_player['map_zh']
        self.my_current_map = current_map
        self.map_info_label.config(
            text=f"您目前在：{current_map} (等級: {my_player['level']}, 職業: {my_player['job_zh']})"
        )
        
        # Find all players in the same map
        same_map_players = [p for p in players if p['map_zh'] == current_map]
        
        # Update player table
        self._update_players_table(same_map_players)
        
        # Log information
        other_players = [p for p in same_map_players if p['nickname'] != self.my_name]
        if other_players:
            self.log_message(f"📍 在 {current_map} 發現 {len(other_players)} 位其他玩家")
            for player in other_players:
                self.log_message(f"   ➤ {player['nickname']} (ID: {player['id']}, {player['level']}級 {player['job_zh']})")
        else:
            self.log_message(f"📍 在 {current_map} 只有您一個人")
    
    def _update_players_table(self, players: List[Dict]):
        """Update the players table display"""
        self._clear_players_table()
        
        for player in players:
            nickname = player['nickname']
            tags = ()
            
            if nickname == self.my_name:
                nickname = f"★ {nickname} (我)"
                tags = ('myself',)
            
            item_id = self.players_tree.insert('', 'end', values=(
                nickname,
                player['id'],
                player['level'],
                player['job_zh']
            ), tags=tags)
    
    def _clear_players_table(self):
        """Clear all items from the players table"""
        for item in self.players_tree.get_children():
            self.players_tree.delete(item)
    
    def _show_context_menu(self, event):
        """Show right-click context menu"""
        item = self.players_tree.identify_row(event.y)
        if item:
            self.players_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _copy_cell_data(self, column: str):
        """Copy specific column data to clipboard"""
        selected_item = self.players_tree.selection()
        if not selected_item:
            return
        
        item = selected_item[0]
        values = self.players_tree.item(item, 'values')
        
        column_index = {'暱稱': 0, 'ID': 1, '等級': 2, '職業': 3}
        if column in column_index:
            data = values[column_index[column]]
            self.parent.clipboard_clear()
            self.parent.clipboard_append(data)
            self.log_message(f"📋 已複製 {column}：{data}")
    
    def _copy_name_id_format(self):
        """Copy name#ID format to clipboard"""
        selected_item = self.players_tree.selection()
        if not selected_item:
            return
        
        item = selected_item[0]
        values = self.players_tree.item(item, 'values')
        
        # Remove markers from nickname
        nickname = values[0]
        if nickname.startswith('★ ') and nickname.endswith(' (我)'):
            nickname = nickname[2:-4]
        
        data = f"{nickname}#{values[1]}"
        self.parent.clipboard_clear()
        self.parent.clipboard_append(data)
        self.log_message(f"📋 已複製名稱#ID：{data}")
    
    def _copy_entire_row(self):
        """Copy entire row data to clipboard"""
        selected_item = self.players_tree.selection()
        if not selected_item:
            return
        
        item = selected_item[0]
        values = self.players_tree.item(item, 'values')
        
        data = f"暱稱: {values[0]}, ID: {values[1]}, 等級: {values[2]}, 職業: {values[3]}"
        self.parent.clipboard_clear()
        self.parent.clipboard_append(data)
        self.log_message(f"📋 已複製整列：{data}")
    
    def _set_status_light(self, on: bool):
        """Set status indicator light"""
        color = 'green' if on else 'red'
        self.status_canvas.itemconfig(self.status_light, fill=color)
    
    def log_message(self, msg: str):
        """Add message to log"""
        self.log.configure(state='normal')
        self.log.insert('end', msg + '\n')
        self.log.yview('end')
        self.log.configure(state='disabled')
    
    def cleanup(self):
        """Cleanup resources"""
        if self.sniffer:
            self.sniffer.stop()

class RecordingTab:
    """Handles the video recording UI tab"""
    
    def __init__(self, parent):
        self.parent = parent
        self.recorder = VideoRecorder(Config.RECORDINGS_DIR, self._log_message)
        self.available_windows = []
        self.update_timer = None
        
        self._create_widgets()
        self._refresh_windows()
    
    def _create_widgets(self):
        """Create UI widgets for video recording"""
        # Window selection
        self._create_window_selection()
        
        # Recording controls
        self._create_recording_controls()
        
        # Recording info
        self._create_recording_info()
        
        # Recording log
        self._create_recording_log()
    
    def _create_window_selection(self):
        """Create window selection widgets"""
        window_frame = ttk.LabelFrame(self.parent, text="視窗選擇", padding=10)
        window_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(window_frame, text="選擇要錄製的視窗：").pack(anchor='w')
        
        window_select_frame = ttk.Frame(window_frame)
        window_select_frame.pack(fill='x', pady=(5, 0))
        
        self.window_var = tk.StringVar()
        self.window_combo = ttk.Combobox(window_select_frame, textvariable=self.window_var, state='readonly')
        self.window_combo.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        ttk.Button(window_select_frame, text="🔄 重新掃描", command=self._refresh_windows).pack(side='right')
    
    def _create_recording_controls(self):
        """Create recording control widgets"""
        control_frame = ttk.LabelFrame(self.parent, text="錄影控制", padding=10)
        control_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Output path
        self._create_path_selection(control_frame)
        
        # Quality settings
        self._create_quality_settings(control_frame)
        
        # Recording button
        self._create_recording_button(control_frame)
    
    def _create_path_selection(self, parent):
        """Create output path selection widgets"""
        path_frame = ttk.Frame(parent)
        path_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(path_frame, text="儲存路徑：").pack(anchor='w')
        path_display_frame = ttk.Frame(path_frame)
        path_display_frame.pack(fill='x', pady=(5, 0))
        
        self.path_var = tk.StringVar(value=os.path.abspath(Config.RECORDINGS_DIR))
        ttk.Entry(path_display_frame, textvariable=self.path_var, state='readonly').pack(
            side='left', fill='x', expand=True, padx=(0, 5))
        ttk.Button(path_display_frame, text="📁 選擇", command=self._select_output_dir).pack(side='right')
    
    def _create_quality_settings(self, parent):
        """Create quality settings widgets"""
        quality_frame = ttk.Frame(parent)
        quality_frame.pack(fill='x', pady=(0, 10))
        
        # First row: FPS and quality
        quality_row1 = ttk.Frame(quality_frame)
        quality_row1.pack(fill='x', pady=(0, 5))
        
        ttk.Label(quality_row1, text="FPS：").pack(side='left')
        self.fps_var = tk.StringVar(value=str(Config.DEFAULT_FPS))
        fps_combo = ttk.Combobox(quality_row1, textvariable=self.fps_var, 
                                values=["15", "20", "25", "30"], width=5, state='readonly')
        fps_combo.pack(side='left', padx=(5, 20))
        
        ttk.Label(quality_row1, text="品質：").pack(side='left')
        self.quality_var = tk.StringVar(value=Config.DEFAULT_QUALITY)
        quality_combo = ttk.Combobox(quality_row1, textvariable=self.quality_var, 
                                   values=["低", "中等", "高", "超高"], width=8, state='readonly')
        quality_combo.pack(side='left', padx=(5, 0))
        
        # Second row: Resolution scaling
        quality_row2 = ttk.Frame(quality_frame)
        quality_row2.pack(fill='x')
        
        ttk.Label(quality_row2, text="解析度：").pack(side='left')
        self.scale_var = tk.StringVar(value=Config.DEFAULT_SCALE)
        scale_combo = ttk.Combobox(quality_row2, textvariable=self.scale_var, 
                                 values=["50%", "60%", "75%", "85%", "100%"], width=8, state='readonly')
        scale_combo.pack(side='left', padx=(5, 20))
        
        ttk.Label(quality_row2, text="檔案大小：90MB", foreground='gray').pack(side='left')
    
    def _create_recording_button(self, parent):
        """Create recording control button"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=(10, 0))
        
        self.record_button = ttk.Button(button_frame, text="🔴 開始錄影", command=self._toggle_recording)
        self.record_button.pack(side='left', padx=(0, 10))
        
        self.record_status_label = ttk.Label(button_frame, text="就緒", foreground='gray')
        self.record_status_label.pack(side='left')
    
    def _create_recording_info(self):
        """Create recording information display"""
        info_frame = ttk.LabelFrame(self.parent, text="錄影資訊", padding=10)
        info_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.record_info_text = tk.Text(info_frame, height=4, state='disabled', wrap='word')
        self.record_info_text.pack(fill='x')
    
    def _create_recording_log(self):
        """Create recording log display"""
        record_log_frame = ttk.LabelFrame(self.parent, text="錄影日誌", padding=5)
        record_log_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.record_log = scrolledtext.ScrolledText(record_log_frame, state='disabled', wrap='word', height=8)
        self.record_log.pack(fill='both', expand=True)
    
    def _refresh_windows(self):
        """Refresh available windows list"""
        try:
            windows = gw.getAllWindows()
            valid_windows = [w for w in windows 
                           if w.title.strip() and not w.isMinimized and w.width > 100 and w.height > 100]
            
            window_titles = [w.title for w in valid_windows]
            self.window_combo['values'] = window_titles
            self.available_windows = valid_windows
            
            if window_titles:
                self.window_combo.set(window_titles[0])
            
            self._log_message(f"📋 發現 {len(window_titles)} 個可錄製視窗")
            
        except Exception as e:
            self._log_message(f"❌ 掃描視窗失敗：{e}")
    
    def _select_output_dir(self):
        """Select output directory"""
        dir_path = filedialog.askdirectory(initialdir=self.recorder.output_dir)
        if dir_path:
            self.recorder.output_dir = dir_path
            self.path_var.set(os.path.abspath(dir_path))
            self._log_message(f"📁 輸出目錄已設定為：{dir_path}")
    
    def _toggle_recording(self):
        """Toggle recording state"""
        if not self.recorder.recording:
            self._start_recording()
        else:
            self._stop_recording()
    
    def _start_recording(self):
        """Start video recording"""
        if not self.window_var.get():
            messagebox.showwarning("警告", "請先選擇要錄製的視窗")
            return
        
        # Find selected window
        selected_title = self.window_var.get()
        selected_window = next((w for w in self.available_windows if w.title == selected_title), None)
        
        if not selected_window:
            messagebox.showerror("錯誤", "找不到選中的視窗")
            return
        
        try:
            fps = int(self.fps_var.get())
            scale = int(self.scale_var.get().replace('%', '')) / 100.0
            
            if self.recorder.start_recording(selected_window, fps, scale):
                self.record_button.config(text="⏹️ 停止錄影")
                self.record_status_label.config(text="錄影中...", foreground='red')
                self._schedule_info_update()
            else:
                messagebox.showerror("錯誤", "無法開始錄影")
                
        except Exception as e:
            messagebox.showerror("錯誤", f"無法開始錄影：{e}")
            self._log_message(f"❌ 錄影啟動失敗：{e}")
    
    def _stop_recording(self):
        """Stop video recording"""
        self.recorder.stop_recording()
        self.record_button.config(text="🔴 開始錄影")
        self.record_status_label.config(text="已停止", foreground='gray')
        
        if self.update_timer:
            self.parent.after_cancel(self.update_timer)
            self.update_timer = None
        
        self._update_record_info()
    
    def _schedule_info_update(self):
        """Schedule periodic info updates"""
        if self.recorder.recording:
            self._update_record_info()
            self.update_timer = self.parent.after(2000, self._schedule_info_update)
    
    def _update_record_info(self):
        """Update recording information display"""
        status = self.recorder.get_status_info()
        
        info_text = f"檔案分割大小：90MB\n"
        info_text += f"當前檔案編號：{status['file_counter']}\n"
        info_text += f"FPS：{self.fps_var.get()} | 品質：{self.quality_var.get()} | 解析度：{self.scale_var.get()}\n"
        info_text += f"輸出目錄：{self.recorder.output_dir}\n"
        
        if status['recording']:
            info_text += f"當前檔案大小：{status['file_size_mb']:.1f} MB"
        
        self.record_info_text.config(state='normal')
        self.record_info_text.delete(1.0, tk.END)
        self.record_info_text.insert(1.0, info_text)
        self.record_info_text.config(state='disabled')
    
    def _log_message(self, msg: str):
        """Add message to recording log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {msg}"
        self.record_log.configure(state='normal')
        self.record_log.insert('end', full_msg + '\n')
        self.record_log.yview('end')
        self.record_log.configure(state='disabled')
    
    def cleanup(self):
        """Cleanup resources"""
        if self.recorder.recording:
            self.recorder.stop_recording()
        
        if self.update_timer:
            self.parent.after_cancel(self.update_timer)

class Artale_Bot_Reporter(tk.Tk):
    """Main application class"""
    
    def __init__(self):
        super().__init__()
        self.title("同地圖玩家查找器 + 視窗錄影")
        self.geometry("900x700")
        
        # Initialize components
        self.data_manager = DataManager()
        self.packet_processor = PacketProcessor(self.data_manager)
        
        # Create UI
        self._create_widgets()
    
    def _create_widgets(self):
        """Create main UI widgets"""
        # Create notebook (tabs)
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Player monitoring tab
        player_frame = ttk.Frame(notebook)
        notebook.add(player_frame, text="🎯 玩家監控")
        self.player_tab = PlayerMonitorTab(player_frame, self.data_manager, self.packet_processor)
        
        # Video recording tab
        record_frame = ttk.Frame(notebook)
        notebook.add(record_frame, text="🎬 視窗錄影")
        self.recording_tab = RecordingTab(record_frame)
    
    def on_closing(self):
        """Handle application closing"""
        self.player_tab.cleanup()
        self.recording_tab.cleanup()
        self.destroy()

if __name__ == '__main__':
    app = Artale_Bot_Reporter()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop() 