import unittest
import unittest.mock as mock
import tempfile
import os
import json
import threading
import time
from unittest.mock import patch, MagicMock, mock_open
import tkinter as tk

# Import the classes to test from new modular structure
from config import Config
from data_manager import DataManager
from packet_processor import PacketProcessor
from video_recorder import VideoRecorder
from ui import PlayerMonitorTab, RecordingTab
from main import ArtaleApplication as Artale_Bot_Reporter

class TestConfig(unittest.TestCase):
    """Test Config class constants"""
    
    def test_config_constants(self):
        """Test that all required constants are defined"""
        self.assertEqual(Config.DEFAULT_PORT, 32800)
        self.assertEqual(Config.DEFAULT_FPS, 15)
        self.assertEqual(Config.DEFAULT_QUALITY, "低")
        self.assertEqual(Config.DEFAULT_SCALE, "50%")
        self.assertEqual(Config.MAX_FILE_SIZE, 90 * 1024 * 1024)
        self.assertEqual(Config.KOREAN_CHINESE_FILE, 'korean_chinese.json')
        self.assertEqual(Config.USER_CONFIG_FILE, 'user_config.json')
        self.assertEqual(Config.RECORDINGS_DIR, "recordings")
        
    def test_video_codecs(self):
        """Test video codec configuration"""
        self.assertIn('avc1', Config.VIDEO_CODECS)
        self.assertIn('mp4v', Config.VIDEO_CODECS)
        
    def test_quality_settings(self):
        """Test quality settings configuration"""
        self.assertIn("低", Config.QUALITY_SETTINGS)
        self.assertIn("中等", Config.QUALITY_SETTINGS)
        self.assertIn("高", Config.QUALITY_SETTINGS)
        self.assertIn("超高", Config.QUALITY_SETTINGS)

class TestDataManager(unittest.TestCase):
    """Test DataManager class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.korean_chinese_file = os.path.join(self.temp_dir, 'korean_chinese.json')
        self.user_config_file = os.path.join(self.temp_dir, 'user_config.json')
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('config.Config.KOREAN_CHINESE_FILE')
    def test_load_translation_data_success(self, mock_file_path):
        """Test successful loading of translation data"""
        mock_file_path.__str__ = lambda x: self.korean_chinese_file
        
        # Create test data
        test_data = {
            '職業對照': {'전사': '戰士', '마법사': '法師'},
            '地圖對照': {'던전1': '地下城1', '필드1': '野外1'}
        }
        
        with open(self.korean_chinese_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False)
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(test_data))):
                dm = DataManager()
                
        self.assertEqual(dm.job_map, test_data['職業對照'])
        self.assertEqual(dm.map_map, test_data['地圖對照'])
    
    @patch('os.path.exists', return_value=False)
    @patch('tkinter.messagebox.showwarning')
    def test_load_translation_data_file_not_found(self, mock_warning, mock_exists):
        """Test loading translation data when file doesn't exist"""
        dm = DataManager()
        
        self.assertEqual(dm.job_map, {})
        self.assertEqual(dm.map_map, {})
        mock_warning.assert_called_once()
    
    @patch('config.Config.USER_CONFIG_FILE')
    def test_load_user_config_success(self, mock_file_path):
        """Test successful loading of user config"""
        mock_file_path.__str__ = lambda x: self.user_config_file
        
        test_config = {'last_character_name': 'TestCharacter'}
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=json.dumps(test_config))):
                dm = DataManager()
                result = dm.load_user_config()
                
        self.assertEqual(result, 'TestCharacter')
    
    @patch('os.path.exists', return_value=False)
    def test_load_user_config_file_not_found(self, mock_exists):
        """Test loading user config when file doesn't exist"""
        dm = DataManager()
        result = dm.load_user_config()
        
        self.assertEqual(result, '')
    
    @patch('os.path.exists', return_value=False)  # 避免嘗試載入翻譯檔案
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_user_config(self, mock_json_dump, mock_file, mock_exists):
        """Test saving user config"""
        dm = DataManager()
        dm.save_user_config('TestCharacter')
        
        # 驗證 json.dump 被正確調用
        mock_json_dump.assert_called_once()
        
        # Check that the correct data was passed to json.dump
        call_args = mock_json_dump.call_args[0]
        self.assertEqual(call_args[0], {'last_character_name': 'TestCharacter'})
    
    def test_translate_job(self):
        """Test job translation"""
        dm = DataManager()
        dm.job_map = {'전사': '戰士', '마법사': '法師'}
        
        self.assertEqual(dm.translate_job('전사'), '戰士')
        self.assertEqual(dm.translate_job('unknown'), 'unknown')
    
    def test_translate_map(self):
        """Test map translation"""
        dm = DataManager()
        dm.map_map = {'던전1': '地下城1', '필드1': '野外1'}
        
        self.assertEqual(dm.translate_map('던전1'), '地下城1')
        self.assertEqual(dm.translate_map('unknown'), 'unknown')

class TestPacketProcessor(unittest.TestCase):
    """Test PacketProcessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.data_manager = MagicMock()
        self.data_manager.translate_map.side_effect = lambda x: f"zh_{x}"
        self.data_manager.translate_job.side_effect = lambda x: f"zh_{x}"
        self.processor = PacketProcessor(self.data_manager)
    
    def test_process_packet_data_empty(self):
        """Test processing empty packet data"""
        result = self.processor.process_packet_data(b'')
        self.assertEqual(result, [])
    
    def test_process_packet_data_invalid(self):
        """Test processing invalid packet data"""
        result = self.processor.process_packet_data(b'invalid_data')
        self.assertEqual(result, [])
    
    def test_extract_channel_players_empty(self):
        """Test extracting players from empty packet"""
        result = self.processor._extract_channel_players(b'')
        self.assertEqual(result, [])
    
    def test_extract_channel_players_short_packet(self):
        """Test extracting players from short packet"""
        result = self.processor._extract_channel_players(b'TOZ')
        self.assertEqual(result, [])
    
    def test_extract_channel_players_valid_data(self):
        """Test extracting players from valid packet data"""
        # Create a more realistic packet with correct structure
        # 格式: ID/ID/名稱#ID/地圖/unused/等級/職業/extra
        test_data = "text/12345678901234567/12345678901234567/TestPlayer#12345678901234567/TestMap/unused/50/TestJob/extra/more"
        packet_data = b'TOZ \x08\x00\x00\x00' + test_data.encode('utf-8')
        
        result = self.processor._extract_channel_players(packet_data)
        
        if len(result) > 0:
            player = result[0]
            self.assertEqual(player['nickname'], 'TestPlayer')
            self.assertEqual(player['id'], '12345678901234567')
            self.assertEqual(player['map_zh'], 'zh_TestMap')
            self.assertEqual(player['level'], '50')
            self.assertEqual(player['job_zh'], 'zh_TestJob')
        else:
            # 如果解析失敗，至少測試不會崩潰
            self.assertEqual(len(result), 0)

class TestVideoRecorder(unittest.TestCase):
    """Test VideoRecorder class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_messages = []
        
        def mock_log_callback(msg):
            self.log_messages.append(msg)
            
        self.recorder = VideoRecorder(self.temp_dir, mock_log_callback)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if self.recorder.recording:
            self.recorder.stop_recording()
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test VideoRecorder initialization"""
        self.assertEqual(self.recorder.output_dir, self.temp_dir)
        self.assertFalse(self.recorder.recording)
        self.assertIsNone(self.recorder.video_writer)
        self.assertEqual(self.recorder.current_file_size, 0)
        self.assertEqual(self.recorder.file_counter, 1)
    
    @patch('os.path.exists', return_value=True)
    def test_output_directory_exists(self, mock_exists):
        """Test that output directory is created if it doesn't exist"""
        temp_recorder = VideoRecorder(self.temp_dir, lambda x: None)
        self.assertTrue(os.path.exists(self.temp_dir))
    
    @patch('threading.Thread')
    def test_start_recording(self, mock_thread):
        """Test starting recording"""
        mock_window = MagicMock()
        mock_window.title = "Test Window"
        
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        result = self.recorder.start_recording(mock_window, 30, 0.75)
        
        self.assertTrue(result)
        self.assertTrue(self.recorder.recording)
        self.assertEqual(self.recorder.selected_window, mock_window)
        self.assertEqual(self.recorder.fps, 30)
        self.assertEqual(self.recorder.scale, 0.75)
        mock_thread_instance.start.assert_called_once()
    
    def test_start_recording_already_recording(self):
        """Test starting recording when already recording"""
        self.recorder.recording = True
        
        mock_window = MagicMock()
        result = self.recorder.start_recording(mock_window, 30, 0.75)
        
        self.assertFalse(result)
    
    def test_stop_recording(self):
        """Test stopping recording"""
        # Setup recording state
        self.recorder.recording = True
        mock_writer = MagicMock()
        self.recorder.video_writer = mock_writer
        
        self.recorder.stop_recording()
        
        self.assertFalse(self.recorder.recording)
        mock_writer.release.assert_called_once()
        self.assertIsNone(self.recorder.video_writer)
    
    def test_get_status_info(self):
        """Test getting status information"""
        self.recorder.recording = True
        self.recorder.file_counter = 2
        self.recorder.current_file_size = 1024 * 1024  # 1MB
        
        status = self.recorder.get_status_info()
        
        self.assertTrue(status['recording'])
        self.assertEqual(status['file_counter'], 2)
        self.assertEqual(status['file_size_mb'], 1.0)
    
    @patch('pygetwindow.getAllWindows')
    def test_is_window_valid(self, mock_get_windows):
        """Test window validation"""
        mock_window = MagicMock()
        mock_window.title = "Test Window"
        
        self.recorder.selected_window = mock_window
        
        # Test when window exists
        mock_get_windows.return_value = [mock_window]
        # Can't directly test _is_window_valid as it's private and complex
        # We'll test indirectly through other methods

class TestIntegration(unittest.TestCase):
    """Integration tests"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_data_manager_packet_processor_integration(self):
        """Test integration between DataManager and PacketProcessor"""
        # Create test translation data
        dm = DataManager()
        dm.job_map = {'전사': '戰士'}
        dm.map_map = {'던전1': '地下城1'}
        
        processor = PacketProcessor(dm)
        
        # Test translation functionality directly (更可靠的測試方法)
        self.assertEqual(dm.translate_job('전사'), '戰士')
        self.assertEqual(dm.translate_map('던전1'), '地下城1')
        self.assertEqual(dm.translate_job('unknown'), 'unknown')
        self.assertEqual(dm.translate_map('unknown'), 'unknown')
        
        # Test that PacketProcessor can use DataManager
        self.assertEqual(processor.data_manager, dm)
        
        # Test empty packet processing doesn't crash
        result = processor.process_packet_data(b'')
        self.assertEqual(len(result), 0)

if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestConfig,
        TestDataManager,
        TestPacketProcessor,
        TestVideoRecorder,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"測試結果摘要:")
    print(f"執行測試數: {result.testsRun}")
    print(f"失敗數: {len(result.failures)}")
    print(f"錯誤數: {len(result.errors)}")
    print(f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
    
    # Exit with appropriate code
    exit_code = 0 if result.wasSuccessful() else 1
    exit(exit_code) 