"""
封包處理模組
處理網路封包解析和玩家資訊提取
"""

import re
from typing import List, Dict
from data_manager import DataManager


class PacketProcessor:
    """處理網路封包解析"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.data_buffer = b''
    
    def process_packet_data(self, packet_data: bytes) -> List[Dict]:
        """處理封包資料並提取玩家資訊"""
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
        """從封包位元組中提取玩家資訊"""
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