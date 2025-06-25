"""
玩家監控UI模組
處理玩家監控相關的使用者介面
"""

import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
from scapy.all import AsyncSniffer, TCP, get_working_ifaces
from typing import List, Dict
from config import Config
from data_manager import DataManager
from packet_processor import PacketProcessor



class PlayerMonitorTab:
    """處理玩家監控UI頁籤"""
    
    def __init__(self, parent, data_manager: DataManager, packet_processor: PacketProcessor):
        self.parent = parent
        self.data_manager = data_manager
        self.packet_processor = packet_processor
        self.my_name = ""
        self.my_current_map = ""
        self.sniffer = None
        self.iface_map = {}
        self.iface_displayname = []
        self.iface_list = self._create_iface_list()
        
        # 載入上次的角色名稱
        self.last_character_name = self.data_manager.load_user_config()
        
        self._create_widgets()
    
    def _create_widgets(self):
        """創建玩家監控UI元件"""
        # 頂部控制區域
        top_frame = ttk.Frame(self.parent)
        top_frame.pack(fill='x', padx=10, pady=10)
        
        # 使用者名稱輸入
        name_frame = ttk.LabelFrame(top_frame, text="設定", padding=10)
        name_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(name_frame, text="請輸入您的角色名稱：").pack(anchor='w')
        self.name_var = tk.StringVar(value=self.last_character_name)
        name_entry = ttk.Entry(name_frame, textvariable=self.name_var, font=('Arial', 12))
        name_entry.pack(fill='x', pady=(5, 10))
        # 👉 加入：網卡選擇下拉選單
        ttk.Label(name_frame, text="請選擇網卡介面：").pack(anchor='w')
        self.iface_var = tk.StringVar()
        self.iface_combo = ttk.Combobox(name_frame, textvariable=self.iface_var,values=self.iface_displayname, state='readonly')
        self.iface_combo.pack(fill='x', pady=(5, 10))
        if self.iface_displayname:
            #預設抓第一個
            self.iface_combo.current(0)
        ttk.Button(name_frame, text="🔍 開始監控", command=self._set_character_name).pack(anchor='e')
        
        # 狀態顯示
        self._create_status_display(top_frame)
        
        # 當前地圖資訊
        self._create_map_info_display()
        
        # 玩家列表
        self._create_player_list()
        
        # 日誌區域
        self._create_log_area()
    
    def _create_status_display(self, parent):
        """創建狀態顯示元件"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(status_frame, text="監控狀態：").pack(side='left')
        self.status_canvas = tk.Canvas(status_frame, width=20, height=20, highlightthickness=0)
        self.status_light = self.status_canvas.create_oval(2, 2, 18, 18, fill='red')
        self.status_canvas.pack(side='left', padx=(5, 10))
        
        self.status_label = ttk.Label(status_frame, text="等待設定角色名稱...", foreground='gray')
        self.status_label.pack(side='left')
    
    def _create_map_info_display(self):
        """創建地圖資訊顯示"""
        map_frame = ttk.LabelFrame(self.parent, text="當前地圖資訊", padding=10)
        map_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        self.map_info_label = ttk.Label(map_frame, text="尚未檢測到您的位置", font=('Arial', 11))
        self.map_info_label.pack(anchor='w')
    
    def _create_player_list(self):
        """創建玩家列表表格"""
        players_frame = ttk.LabelFrame(self.parent, text="同地圖玩家", padding=10)
        players_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # 創建表格
        columns = ('暱稱', 'ID', '等級', '職業')
        self.players_tree = ttk.Treeview(players_frame, columns=columns, show='headings', height=8)
        
        # 設定欄位標題和寬度
        for col in columns:
            self.players_tree.heading(col, text=col)
        
        self.players_tree.column('暱稱', width=120, anchor='w')
        self.players_tree.column('ID', width=150, anchor='w')
        self.players_tree.column('等級', width=80, anchor='center')
        self.players_tree.column('職業', width=120, anchor='w')
        
        # 綁定右鍵選單
        self.players_tree.bind('<Button-3>', self._show_context_menu)
        
        # 加入捲軸
        scrollbar = ttk.Scrollbar(players_frame, orient='vertical', command=self.players_tree.yview)
        self.players_tree.configure(yscrollcommand=scrollbar.set)
        
        self.players_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 創建右鍵選單
        self._create_context_menu()
        
        # 配置玩家自己的行樣式
        self.players_tree.tag_configure('myself', background='#E8F4FD')
    
    def _create_context_menu(self):
        """創建右鍵選單"""
        self.context_menu = tk.Menu(self.parent, tearoff=0)
        self.context_menu.add_command(label="複製暱稱", command=lambda: self._copy_cell_data('暱稱'))
        self.context_menu.add_command(label="複製玩家ID", command=lambda: self._copy_cell_data('ID'))
        self.context_menu.add_command(label="複製名稱#ID", command=self._copy_name_id_format)
        self.context_menu.add_command(label="複製等級", command=lambda: self._copy_cell_data('等級'))
        self.context_menu.add_command(label="複製職業", command=lambda: self._copy_cell_data('職業'))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="複製整列", command=self._copy_entire_row)
    
    def _create_log_area(self):
        """創建日誌顯示區域"""
        log_frame = ttk.LabelFrame(self.parent, text="監控日誌", padding=5)
        log_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        self.log = scrolledtext.ScrolledText(log_frame, state='disabled', wrap='word', height=6)
        self.log.pack(fill='both', expand=True)
        
    def _create_iface_list(self):
        """取得所有網卡並加入下拉選單"""
        iface_names = []
        for iface in get_working_ifaces():
            iface_names.append(iface.name)
            print(f"{iface.name} | {iface.description} | {iface.guid}")
            self.iface_map[iface.name] = "\\Device\\NPF_"+iface.guid
        self.iface_displayname = iface_names
    
    def _start_packet_monitoring(self):
        """開始封包監控"""
        selected_iface_name = self.iface_var.get()
        iface_guid = self.iface_map.get(selected_iface_name)
        if self.sniffer and self.sniffer.thread and self.sniffer.thread.is_alive():
            self.log_message(f"已停止 封包監控 監控網卡:{selected_iface_name}|{iface_guid}")
            self.sniffer.stop()
        try:
            self.sniffer = AsyncSniffer(
                iface=iface_guid,
                filter=f'tcp port {Config.DEFAULT_PORT}',
                prn=self._process_packet,
                store=False
            )
            self.sniffer.start()
            self._set_status_light(True)
            self.log_message(f"🟢 封包監控已啟動 (TCP {Config.DEFAULT_PORT}) 監控網卡:{selected_iface_name}|{iface_guid}")
        except Exception as e:
            self.log_message(f"❌ 啟動監控失敗：{e}")
            messagebox.showerror("錯誤", f"無法啟動封包監控：{e}")
    
    def _process_packet(self, pkt):
        """處理傳入的封包"""
        if TCP not in pkt:
            return
        
        players = self.packet_processor.process_packet_data(bytes(pkt[TCP].payload))
        if players:
            # 使用 after 方法安全地從線程更新GUI
            self.parent.after(0, lambda p=players: self._update_players(p))
    
    def _set_character_name(self):
        """設定要監控的角色名稱"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showwarning("警告", "請輸入角色名稱")
            return
        
        self._start_packet_monitoring()
        self.my_name = name
        self.data_manager.save_user_config(name)
        self.status_label.config(text=f"正在監控角色：{name}", foreground='blue')
        self.log_message(f"🎯 開始監控角色：{name}")
    
    def _update_players(self, players: List[Dict]):
        """根據檢測到的玩家更新玩家列表"""
        if not self.my_name:
            return
        
        # 找到玩家的角色
        my_player = next((p for p in players if p['nickname'] == self.my_name), None)
        
        if not my_player:
            self.map_info_label.config(text=f"未找到角色 '{self.my_name}' 在頻道中")
            self._clear_players_table()
            return
        
        # 更新當前地圖資訊
        current_map = my_player['map_zh']
        self.my_current_map = current_map
        self.map_info_label.config(
            text=f"您目前在：{current_map} (等級: {my_player['level']}, 職業: {my_player['job_zh']})"
        )
        
        # 找到所有在同一地圖的玩家
        same_map_players = [p for p in players if p['map_zh'] == current_map]
        
        # 更新玩家表格
        self._update_players_table(same_map_players)
        
        # 記錄日誌資訊
        other_players = [p for p in same_map_players if p['nickname'] != self.my_name]
        if other_players:
            self.log_message(f"📍 在 {current_map} 發現 {len(other_players)} 位其他玩家")
            for player in other_players:
                self.log_message(f"   ➤ {player['nickname']} (ID: {player['id']}, {player['level']}級 {player['job_zh']})")
        else:
            self.log_message(f"📍 在 {current_map} 只有您一個人")
    
    def _update_players_table(self, players: List[Dict]):
        """更新玩家表格顯示"""
        self._clear_players_table()
        
        for player in players:
            nickname = player['nickname']
            tags = ()
            
            if nickname == self.my_name:
                nickname = f"★ {nickname} (我)"
                tags = ('myself',)
            
            self.players_tree.insert('', 'end', values=(
                nickname,
                player['id'],
                player['level'],
                player['job_zh']
            ), tags=tags)
    
    def _clear_players_table(self):
        """清空玩家表格中的所有項目"""
        for item in self.players_tree.get_children():
            self.players_tree.delete(item)
    
    def _show_context_menu(self, event):
        """顯示右鍵選單"""
        item = self.players_tree.identify_row(event.y)
        if item:
            self.players_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def _copy_cell_data(self, column: str):
        """複製特定欄位資料到剪貼簿"""
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
        """複製名稱#ID格式到剪貼簿"""
        selected_item = self.players_tree.selection()
        if not selected_item:
            return
        
        item = selected_item[0]
        values = self.players_tree.item(item, 'values')
        
        # 從暱稱中移除標記
        nickname = values[0]
        if nickname.startswith('★ ') and nickname.endswith(' (我)'):
            nickname = nickname[2:-4]
        
        data = f"{nickname}#{values[1]}"
        self.parent.clipboard_clear()
        self.parent.clipboard_append(data)
        self.log_message(f"📋 已複製名稱#ID：{data}")
    
    def _copy_entire_row(self):
        """複製整列資料到剪貼簿"""
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
        """設定狀態指示燈"""
        color = 'green' if on else 'red'
        self.status_canvas.itemconfig(self.status_light, fill=color)
    
    def log_message(self, msg: str):
        """添加訊息到日誌"""
        self.log.configure(state='normal')
        self.log.insert('end', msg + '\n')
        self.log.yview('end')
        self.log.configure(state='disabled')
    
    def cleanup(self):
        """清理資源"""
        if self.sniffer:
            self.sniffer.stop() 