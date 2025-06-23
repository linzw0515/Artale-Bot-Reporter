"""
配置模組
包含所有應用程式的配置常數
"""

class Config:
    """應用程式配置常數"""
    
    # 網路設定
    DEFAULT_PORT = 32800
    
    # 視頻錄製設定
    DEFAULT_FPS = 15
    DEFAULT_QUALITY = "低"
    DEFAULT_SCALE = "50%"
    MAX_FILE_SIZE = 90 * 1024 * 1024  # 90MB
    
    # 檔案路徑
    KOREAN_CHINESE_FILE = 'korean_chinese.json'
    USER_CONFIG_FILE = 'user_config.json'
    RECORDINGS_DIR = "recordings"
    
    # 視頻編碼設定
    VIDEO_CODECS = ['avc1', 'mp4v']  # Primary and fallback codecs
    QUALITY_SETTINGS = {
        "低": {"crf": 28, "preset": "fast"},
        "中等": {"crf": 23, "preset": "medium"},
        "高": {"crf": 18, "preset": "slow"},
        "超高": {"crf": 15, "preset": "slower"}
    }
    
    # UI 設定
    WINDOW_TITLE = "同地圖玩家查找器 + 視窗錄影"
    WINDOW_SIZE = "900x700"
    PLAYER_TAB_TITLE = "🎯 玩家監控"
    RECORDING_TAB_TITLE = "🎬 視窗錄影" 