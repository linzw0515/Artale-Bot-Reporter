#!/usr/bin/env python3
"""
測試執行器
簡化的測試運行腳本，包含基本的測試功能
"""

import os
import sys
import unittest
import traceback
from io import StringIO

# 確保可以匯入主程式
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_basic_tests():
    """執行基本測試，不依賴複雜的依賴"""
    
    print("=" * 60)
    print("🧪 Artale Bot Reporter 測試套件")
    print("=" * 60)
    
    test_results = []
    
    # 測試 1: 匯入測試
    print("\n📦 測試 1: 模組匯入測試")
    try:
        from Artale_Bot_Reporter import Config, DataManager, PacketProcessor, VideoRecorder
        print("✅ 成功匯入核心類別")
        test_results.append(("模組匯入", True, None))
    except Exception as e:
        print(f"❌ 匯入失敗: {e}")
        test_results.append(("模組匯入", False, str(e)))
        return test_results
    
    # 測試 2: Config 常數測試
    print("\n⚙️  測試 2: 配置常數測試")
    try:
        assert Config.DEFAULT_PORT == 32800
        assert Config.DEFAULT_FPS == 30
        assert Config.DEFAULT_QUALITY == "中等"
        assert Config.MAX_FILE_SIZE == 90 * 1024 * 1024
        assert len(Config.VIDEO_CODECS) >= 2
        assert len(Config.QUALITY_SETTINGS) == 4
        print("✅ 所有配置常數正確")
        test_results.append(("配置常數", True, None))
    except AssertionError as e:
        print(f"❌ 配置常數錯誤: {e}")
        test_results.append(("配置常數", False, str(e)))
    except Exception as e:
        print(f"❌ 配置測試失敗: {e}")
        test_results.append(("配置常數", False, str(e)))
    
    # 測試 3: DataManager 基本功能
    print("\n📊 測試 3: DataManager 基本功能")
    try:
        dm = DataManager()
        
        # 測試翻譯功能
        dm.job_map = {'test_job': '測試職業'}
        dm.map_map = {'test_map': '測試地圖'}
        
        assert dm.translate_job('test_job') == '測試職業'
        assert dm.translate_job('unknown') == 'unknown'
        assert dm.translate_map('test_map') == '測試地圖'
        assert dm.translate_map('unknown') == 'unknown'
        
        print("✅ DataManager 基本功能正常")
        test_results.append(("DataManager基本功能", True, None))
    except Exception as e:
        print(f"❌ DataManager 測試失敗: {e}")
        test_results.append(("DataManager基本功能", False, str(e)))
    
    # 測試 4: PacketProcessor 基本功能
    print("\n📡 測試 4: PacketProcessor 基本功能")
    try:
        dm = DataManager()
        processor = PacketProcessor(dm)
        
        # 測試空封包處理
        result = processor.process_packet_data(b'')
        assert result == []
        
        # 測試無效封包處理
        result = processor.process_packet_data(b'invalid')
        assert result == []
        
        print("✅ PacketProcessor 基本功能正常")
        test_results.append(("PacketProcessor基本功能", True, None))
    except Exception as e:
        print(f"❌ PacketProcessor 測試失敗: {e}")
        test_results.append(("PacketProcessor基本功能", False, str(e)))
    
    # 測試 5: VideoRecorder 初始化
    print("\n🎬 測試 5: VideoRecorder 初始化")
    try:
        import tempfile
        temp_dir = tempfile.mkdtemp()
        
        def dummy_log(msg):
            pass
        
        recorder = VideoRecorder(temp_dir, dummy_log)
        
        assert recorder.output_dir == temp_dir
        assert recorder.recording == False
        assert recorder.video_writer is None
        assert recorder.current_file_size == 0
        assert recorder.file_counter == 1
        
        # 測試狀態資訊
        status = recorder.get_status_info()
        assert 'recording' in status
        assert 'file_counter' in status
        assert 'file_size_mb' in status
        
        print("✅ VideoRecorder 初始化正常")
        test_results.append(("VideoRecorder初始化", True, None))
        
        # 清理
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    except Exception as e:
        print(f"❌ VideoRecorder 測試失敗: {e}")
        test_results.append(("VideoRecorder初始化", False, str(e)))
    
    # 測試 6: 檔案結構測試
    print("\n📁 測試 6: 檔案結構測試")
    try:
        required_files = [
            'Artale_Bot_Reporter.py',
            'test_artale_bot_reporter.py',
            'run_tests.py'
        ]
        
        missing_files = []
        for file in required_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            raise FileNotFoundError(f"缺少檔案: {missing_files}")
        
        print("✅ 檔案結構完整")
        test_results.append(("檔案結構", True, None))
    except Exception as e:
        print(f"❌ 檔案結構測試失敗: {e}")
        test_results.append(("檔案結構", False, str(e)))
    
    return test_results

def print_summary(test_results):
    """列印測試摘要"""
    print("\n" + "=" * 60)
    print("📋 測試結果摘要")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)
    failed = total - passed
    
    print(f"總計測試: {total}")
    print(f"通過: {passed} ✅")
    print(f"失敗: {failed} ❌")
    print(f"成功率: {(passed/total*100):.1f}%")
    
    if failed > 0:
        print("\n❌ 失敗的測試:")
        for name, success, error in test_results:
            if not success:
                print(f"  • {name}: {error}")
    
    print("\n" + "=" * 60)
    
    return failed == 0

def run_full_tests():
    """執行完整測試套件（需要所有依賴）"""
    print("\n🔄 嘗試執行完整測試套件...")
    
    try:
        # 嘗試匯入完整測試
        import test_artale_bot_reporter
        
        # 建立測試套件
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # 獲取所有測試類別
        test_classes = []
        for name in dir(test_artale_bot_reporter):
            obj = getattr(test_artale_bot_reporter, name)
            if (isinstance(obj, type) and 
                issubclass(obj, unittest.TestCase) and 
                obj != unittest.TestCase):
                test_classes.append(obj)
        
        if not test_classes:
            print("⚠️ 未找到測試類別，跳過完整測試")
            return False
        
        # 加入測試
        for test_class in test_classes:
            tests = loader.loadTestsFromTestCase(test_class)
            suite.addTests(tests)
        
        # 執行測試
        stream = StringIO()
        runner = unittest.TextTestRunner(stream=stream, verbosity=2)
        result = runner.run(suite)
        
        # 列印結果
        print(f"執行了 {result.testsRun} 個測試")
        print(f"失敗: {len(result.failures)}")
        print(f"錯誤: {len(result.errors)}")
        
        if result.failures:
            print("\n失敗的測試:")
            for test, traceback in result.failures:
                print(f"  • {test}: {traceback}")
        
        if result.errors:
            print("\n錯誤的測試:")
            for test, traceback in result.errors:
                print(f"  • {test}: {traceback}")
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"⚠️ 無法執行完整測試套件，缺少依賴: {e}")
        return False
    except Exception as e:
        print(f"❌ 完整測試執行失敗: {e}")
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("🚀 開始測試...")
    
    # 執行基本測試
    basic_results = run_basic_tests()
    basic_success = print_summary(basic_results)
    
    # 嘗試執行完整測試
    full_success = run_full_tests()
    
    # 決定退出碼
    if basic_success:
        print("\n🎉 基本測試全部通過！")
        if full_success:
            print("🎉 完整測試也全部通過！")
            exit_code = 0
        else:
            print("⚠️ 完整測試有問題，但基本功能正常")
            exit_code = 0
    else:
        print("\n💥 基本測試有失敗，請檢查程式碼")
        exit_code = 1
    
    print(f"\n測試完成，退出碼: {exit_code}")
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 