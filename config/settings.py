# config/settings.py
"""
应用设置
"""

import os
import json
from config.constants import *


class Settings:
    """设置管理器"""
    
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".legenddroptool")
        self.config_file = os.path.join(self.config_dir, "settings.json")
        
        # 默认设置
        self.default_settings = {
            'window_size': [APP_WIDTH, APP_HEIGHT],
            'window_position': [100, 100],
            'data_path': os.path.join(os.getcwd(), "data", "MonItems"),
            'show_rate_as_percent': True,
            'show_rate_as_fraction': True,
            'auto_refresh': False,
            'theme': 'default',
            'recent_files': [],
            'max_recent_files': 10,
            'encoding': ENCODING,
            'show_toolbar': True,
            'show_statusbar': True,
        }
        
        self.settings = {}
        self.load_settings()
    
    def load_settings(self):
        """加载设置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
                # 确保所有设置项都存在
                for key, value in self.default_settings.items():
                    if key not in self.settings:
                        self.settings[key] = value
            else:
                self.settings = self.default_settings.copy()
        except Exception as e:
            print(f"加载设置失败: {e}")
            self.settings = self.default_settings.copy()
    
    def save_settings(self):
        """保存设置"""
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    def get(self, key, default=None):
        """获取设置值"""
        return self.settings.get(key, default)
    
    def set(self, key, value):
        """设置值"""
        self.settings[key] = value
    
    def add_recent_file(self, filepath):
        """添加最近打开的文件"""
        recent = self.get('recent_files', [])
        
        # 如果已存在，先移除
        if filepath in recent:
            recent.remove(filepath)
        
        # 添加到开头
        recent.insert(0, filepath)
        
        # 限制数量
        max_files = self.get('max_recent_files', 10)
        if len(recent) > max_files:
            recent = recent[:max_files]
        
        self.set('recent_files', recent)
        self.save_settings()