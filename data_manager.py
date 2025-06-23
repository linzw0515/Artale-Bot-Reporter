"""
資料管理模組
處理資料載入、儲存和翻譯功能
"""

import os
import json
import tkinter.messagebox as messagebox
from config import Config


class DataManager:
    """處理資料載入、儲存和翻譯"""
    
    def __init__(self):
        self.job_map = {}
        self.map_map = {}
        self.load_translation_data()
    
    def load_translation_data(self):
        """載入韓文-中文翻譯對照表"""
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
        """載入使用者配置"""
        try:
            if os.path.exists(Config.USER_CONFIG_FILE):
                with open(Config.USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('last_character_name', '')
        except Exception as e:
            print(f"載入設定失敗: {e}")
        return ''
    
    def save_user_config(self, character_name: str):
        """儲存使用者配置"""
        try:
            config = {'last_character_name': character_name}
            with open(Config.USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"儲存設定失敗: {e}")
    
    def translate_job(self, korean_job: str) -> str:
        """翻譯韓文職業名稱為中文"""
        return self.job_map.get(korean_job, korean_job)
    
    def translate_map(self, korean_map: str) -> str:
        """翻譯韓文地圖名稱為中文"""
        return self.map_map.get(korean_map, korean_map) 