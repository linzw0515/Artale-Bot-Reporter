# 🎮 Artale Bot Reporter

一款專為 Artale 遊戲開發的玩家監控與視頻錄製工具，提供同地圖玩家查找和視窗錄影功能。

## ✨ 主要功能

### 🔍 玩家監控
- **網路封包監聽**: 即時監控網路封包，提取玩家資訊
- **同地圖玩家檢測**: 自動識別同地圖的其他玩家
- **韓中文翻譯**: 內建韓文玩家名稱轉中文功能
- **可疑行為標記**: 自動標記可能的機器人玩家

### 📹 視頻錄製
- **視窗錄製**: 支援指定視窗錄製，不影響其他程式
- **自動分割**: 長時間錄製自動分割檔案，避免檔案過大
- **多格式支援**: 支援 MP4、AVI 等多種視頻格式
- **高效壓縮**: 優化的編碼設定，平衡檔案大小與畫質

## 🚀 快速開始

### 環境需求
- Windows 10/11
- Python 3.8+
- 網路權限（監聽封包需要）

### 安裝方式

#### 方法一：下載執行檔 (推薦)
1. 從 [Releases](../../releases) 下載最新版本的 `Artale_Bot_Reporter.exe`
2. 確保 `korean_chinese.json` 和 `watched_maps.json` 與 exe 在同一目錄
3. 雙擊執行檔即可使用

#### 方法二：從源碼運行
```bash
# 克隆項目
git clone https://github.com/yourusername/Artale_Bot_Reporter_PY.git
cd Artale_Bot_Reporter_PY

# 安裝依賴
pip install -r requirements_full.txt

# 運行程式
python main.py
```

## 📁 項目結構

```
Artale_Bot_Reporter_PY/
├── main.py                    # 程式入口
├── config.py                  # 配置管理
├── data_manager.py           # 資料處理
├── packet_processor.py       # 封包解析
├── video_recorder.py         # 視頻錄製
├── ui/                       # UI 模組
│   ├── player_monitor.py     # 玩家監控介面
│   └── recording_tab.py      # 錄影介面
├── korean_chinese.json       # 韓中文對照表
├── watched_maps.json         # 地圖監控設定
└── requirements_full.txt     # 專案依賴
```

## 🛠️ 技術架構

### 核心技術
- **GUI**: Tkinter
- **網路監聽**: Scapy
- **視頻處理**: OpenCV
- **圖像處理**: PIL/Pillow, NumPy
- **視窗控制**: PyGetWindow, PyAutoGUI

### 模組化設計
本項目採用模組化架構，將不同功能分離到獨立模組中：
- 提高程式碼可維護性
- 便於單元測試
- 支援功能擴展
- 降低模組間耦合

## 🧪 測試

### 執行測試
```bash
# 快速測試
python run_tests.py

# 完整測試
pip install -r requirements_test.txt
pytest test_artale_bot_reporter.py -v
```

### 測試覆蓋範圍
- **Config**: 100%
- **DataManager**: ~85%
- **PacketProcessor**: ~80%
- **VideoRecorder**: ~75%

## 📦 打包與發布

### 建立執行檔
```bash
# 使用建構腳本
python build_exe.py

# 或使用批次檔
build.bat
```

### 打包結果
- `dist/Artale_Bot_Reporter.exe` (64.8 MB)
- 包含所有依賴，可獨立運行
- 無需安裝 Python 環境

## ⚙️ 配置說明

### 使用者配置 (`user_config.json`)
```json
{
  "language": "zh_TW",
  "auto_start": false
}
```

### 監控地圖設定 (`watched_maps.json`)
```json
{
  "enabled_maps": []
}
```

## 🤝 貢獻指南

我們歡迎任何形式的貢獻！

### 如何貢獻
1. Fork 本項目
2. 創建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

### 開發環境設置
```bash
# 安裝開發依賴
pip install -r requirements_test.txt

# 執行測試
python run_tests.py

# 檢查程式碼風格
flake8 *.py
```

## 📋 更新日誌

### [1.0.0] - 2024-XX-XX
- 初始版本發布
- 玩家監控功能
- 視頻錄製功能
- 模組化架構重構

## ⚠️ 注意事項

1. **權限需求**: 監聽網路封包可能需要管理員權限
2. **防毒軟體**: 某些防毒軟體可能誤報 exe 檔案
3. **網路環境**: 需要穩定的網路連接進行封包監聽
4. **遊戲相容性**: 目前僅支援 Artale 遊戲

## 📄 授權條款

本項目採用 [MIT License](LICENSE) 授權條款。

## 📞 聯絡方式

- 項目問題: [Issues](../../issues)
- 功能建議: [Discussions](../../discussions)

---

**免責聲明**: 本工具僅供學習和研究使用，請遵守遊戲服務條款和相關法律法規。 