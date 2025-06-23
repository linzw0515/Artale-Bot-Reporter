"""
視頻錄製模組
處理視窗錄製功能
"""

import os
import cv2
import numpy as np
import pygetwindow as gw
import threading
import time
from datetime import datetime
from typing import Dict, Callable
from config import Config


class VideoRecorder:
    """處理視頻錄製功能"""
    
    def __init__(self, output_dir: str, log_callback: Callable[[str], None]):
        self.output_dir = output_dir
        self.log_callback = log_callback
        self.recording = False
        self.video_writer = None
        self.recording_thread = None
        self.current_file_size = 0
        self.file_counter = 1
        self.frame_count = 0
        self.current_video_path = ""
        
        # 確保輸出目錄存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def start_recording(self, window, fps: int, scale: float) -> bool:
        """開始視頻錄製"""
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
        """停止視頻錄製"""
        self.recording = False
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        self.log_callback("⏹️ 錄影已停止")
    
    def _recording_loop(self):
        """主錄製循環"""
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
                
                # 控制幀率
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
        """檢查目標視窗是否仍然有效"""
        if not self.selected_window:
            return False
        
        return any(w.title == self.selected_window.title for w in gw.getAllWindows())
    
    def _capture_frame(self):
        """從選定視窗捕獲一幀"""
        try:
            import pyautogui
            
            if self.selected_window.isMinimized:
                self.selected_window.restore()
            
            left, top = self.selected_window.left, self.selected_window.top
            width, height = self.selected_window.width, self.selected_window.height
            
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # 應用縮放
            if self.scale != 1.0:
                new_width = int(width * self.scale)
                new_height = int(height * self.scale)
                frame = cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            
            return frame
            
        except Exception as e:
            self.log_callback(f"⚠️ 截圖錯誤：{e}")
            return None
    
    def _write_frame(self, frame):
        """將幀寫入視頻檔案"""
        height, width = frame.shape[:2]
        
        # 如需要，創建新的視頻檔案
        if self.video_writer is None or self.current_file_size >= Config.MAX_FILE_SIZE:
            if self.video_writer:
                self.video_writer.release()
            
            self._create_new_video_file(width, height)
        
        # 寫入幀
        if self.video_writer and self.video_writer.isOpened():
            self.video_writer.write(frame)
            self.frame_count += 1
            
            # 每10幀檢查一次檔案大小
            if self.frame_count % 10 == 0:
                self._update_file_size()
    
    def _create_new_video_file(self, width: int, height: int):
        """創建新的視頻檔案"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{timestamp}_part{self.file_counter:03d}.mp4"
        self.current_video_path = os.path.join(self.output_dir, filename)
        
        # 首先嘗試主要編碼器，然後回退
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
        """更新當前檔案大小"""
        try:
            if os.path.exists(self.current_video_path):
                self.current_file_size = os.path.getsize(self.current_video_path)
                
                if self.current_file_size >= Config.MAX_FILE_SIZE:
                    self.file_counter += 1
                    size_mb = self.current_file_size / (1024 * 1024)
                    self.log_callback(f"📄 檔案達到 {size_mb:.1f}MB，準備分割")
        except Exception:
            pass  # 忽略檔案大小檢查錯誤
    
    def get_status_info(self) -> Dict:
        """獲取當前錄製狀態資訊"""
        info = {
            'recording': self.recording,
            'file_counter': self.file_counter,
            'file_size_mb': self.current_file_size / (1024 * 1024) if self.current_file_size else 0
        }
        return info 