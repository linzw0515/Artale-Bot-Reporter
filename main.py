"""
主程式入口檔案
同地圖玩家查找器 + 視窗錄影工具
"""

import tkinter as tk
from tkinter import ttk
from config import Config
from data_manager import DataManager
from packet_processor import PacketProcessor
from ui import PlayerMonitorTab, RecordingTab


class ArtaleApplication(tk.Tk):
    """主應用程式類別"""
    
    def __init__(self):
        super().__init__()
        self.title(Config.WINDOW_TITLE)
        self.geometry(Config.WINDOW_SIZE)
        
        # 初始化核心元件
        self.data_manager = DataManager()
        self.packet_processor = PacketProcessor(self.data_manager)
        
        # 創建UI
        self._create_widgets()
    
    def _create_widgets(self):
        """創建主UI元件"""
        # 創建分頁控制器
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 玩家監控頁籤
        player_frame = ttk.Frame(notebook)
        notebook.add(player_frame, text=Config.PLAYER_TAB_TITLE)
        self.player_tab = PlayerMonitorTab(player_frame, self.data_manager, self.packet_processor)
        
        # 視頻錄製頁籤
        record_frame = ttk.Frame(notebook)
        notebook.add(record_frame, text=Config.RECORDING_TAB_TITLE)
        self.recording_tab = RecordingTab(record_frame)
    
    def on_closing(self):
        """處理應用程式關閉"""
        self.player_tab.cleanup()
        self.recording_tab.cleanup()
        self.destroy()


def main():
    """主函數"""
    app = ArtaleApplication()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == '__main__':
    main() 