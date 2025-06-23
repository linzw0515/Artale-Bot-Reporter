"""
錄影UI模組
處理視頻錄製相關的使用者介面
"""

import os
import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog
import pygetwindow as gw
from datetime import datetime
from config import Config
from video_recorder import VideoRecorder


class RecordingTab:
    """處理視頻錄製UI頁籤"""
    
    def __init__(self, parent):
        self.parent = parent
        self.recorder = VideoRecorder(Config.RECORDINGS_DIR, self._log_message)
        self.available_windows = []
        self.update_timer = None
        
        self._create_widgets()
        self._refresh_windows()
    
    def _create_widgets(self):
        """創建視頻錄製UI元件"""
        # 視窗選擇
        self._create_window_selection()
        
        # 錄製控制
        self._create_recording_controls()
        
        # 錄製資訊
        self._create_recording_info()
        
        # 錄製日誌
        self._create_recording_log()
    
    def _create_window_selection(self):
        """創建視窗選擇元件"""
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
        """創建錄製控制元件"""
        control_frame = ttk.LabelFrame(self.parent, text="錄影控制", padding=10)
        control_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # 輸出路徑
        self._create_path_selection(control_frame)
        
        # 品質設定
        self._create_quality_settings(control_frame)
        
        # 錄製按鈕
        self._create_recording_button(control_frame)
    
    def _create_path_selection(self, parent):
        """創建輸出路徑選擇元件"""
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
        """創建品質設定元件"""
        quality_frame = ttk.Frame(parent)
        quality_frame.pack(fill='x', pady=(0, 10))
        
        # 第一行：FPS 和品質
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
        
        # 第二行：解析度縮放
        quality_row2 = ttk.Frame(quality_frame)
        quality_row2.pack(fill='x')
        
        ttk.Label(quality_row2, text="解析度：").pack(side='left')
        self.scale_var = tk.StringVar(value=Config.DEFAULT_SCALE)
        scale_combo = ttk.Combobox(quality_row2, textvariable=self.scale_var, 
                                 values=["50%", "60%", "75%", "85%", "100%"], width=8, state='readonly')
        scale_combo.pack(side='left', padx=(5, 20))
        
        ttk.Label(quality_row2, text="檔案大小：90MB", foreground='gray').pack(side='left')
    
    def _create_recording_button(self, parent):
        """創建錄製控制按鈕"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill='x', pady=(10, 0))
        
        self.record_button = ttk.Button(button_frame, text="🔴 開始錄影", command=self._toggle_recording)
        self.record_button.pack(side='left', padx=(0, 10))
        
        self.record_status_label = ttk.Label(button_frame, text="就緒", foreground='gray')
        self.record_status_label.pack(side='left')
    
    def _create_recording_info(self):
        """創建錄製資訊顯示"""
        info_frame = ttk.LabelFrame(self.parent, text="錄影資訊", padding=10)
        info_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.record_info_text = tk.Text(info_frame, height=4, state='disabled', wrap='word')
        self.record_info_text.pack(fill='x')
    
    def _create_recording_log(self):
        """創建錄製日誌顯示"""
        record_log_frame = ttk.LabelFrame(self.parent, text="錄影日誌", padding=5)
        record_log_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.record_log = scrolledtext.ScrolledText(record_log_frame, state='disabled', wrap='word', height=8)
        self.record_log.pack(fill='both', expand=True)
    
    def _refresh_windows(self):
        """重新整理可用視窗列表"""
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
        """選擇輸出目錄"""
        dir_path = filedialog.askdirectory(initialdir=self.recorder.output_dir)
        if dir_path:
            self.recorder.output_dir = dir_path
            self.path_var.set(os.path.abspath(dir_path))
            self._log_message(f"📁 輸出目錄已設定為：{dir_path}")
    
    def _toggle_recording(self):
        """切換錄製狀態"""
        if not self.recorder.recording:
            self._start_recording()
        else:
            self._stop_recording()
    
    def _start_recording(self):
        """開始視頻錄製"""
        if not self.window_var.get():
            tk.messagebox.showwarning("警告", "請先選擇要錄製的視窗")
            return
        
        # 找到選中的視窗
        selected_title = self.window_var.get()
        selected_window = next((w for w in self.available_windows if w.title == selected_title), None)
        
        if not selected_window:
            tk.messagebox.showerror("錯誤", "找不到選中的視窗")
            return
        
        try:
            fps = int(self.fps_var.get())
            scale = int(self.scale_var.get().replace('%', '')) / 100.0
            
            if self.recorder.start_recording(selected_window, fps, scale):
                self.record_button.config(text="⏹️ 停止錄影")
                self.record_status_label.config(text="錄影中...", foreground='red')
                self._schedule_info_update()
            else:
                tk.messagebox.showerror("錯誤", "無法開始錄影")
                
        except Exception as e:
            tk.messagebox.showerror("錯誤", f"無法開始錄影：{e}")
            self._log_message(f"❌ 錄影啟動失敗：{e}")
    
    def _stop_recording(self):
        """停止視頻錄製"""
        self.recorder.stop_recording()
        self.record_button.config(text="🔴 開始錄影")
        self.record_status_label.config(text="已停止", foreground='gray')
        
        if self.update_timer:
            self.parent.after_cancel(self.update_timer)
            self.update_timer = None
        
        self._update_record_info()
    
    def _schedule_info_update(self):
        """排程定期資訊更新"""
        if self.recorder.recording:
            self._update_record_info()
            self.update_timer = self.parent.after(2000, self._schedule_info_update)
    
    def _update_record_info(self):
        """更新錄製資訊顯示"""
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
        """添加訊息到錄製日誌"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {msg}"
        self.record_log.configure(state='normal')
        self.record_log.insert('end', full_msg + '\n')
        self.record_log.yview('end')
        self.record_log.configure(state='disabled')
    
    def cleanup(self):
        """清理資源"""
        if self.recorder.recording:
            self.recorder.stop_recording()
        
        if self.update_timer:
            self.parent.after_cancel(self.update_timer) 