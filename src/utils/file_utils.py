# src/utils/file_utils.py
"""
文件操作工具
"""

import os
import shutil
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def ensure_directory(directory: str) -> bool:
    """确保目录存在，如果不存在则创建"""
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
        return True
    except Exception as e:
        logger.error(f"创建目录失败 {directory}: {e}")
        return False


def find_txt_files(directory: str) -> List[str]:
    """查找目录下的所有txt文件"""
    if not os.path.exists(directory):
        return []
    
    txt_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.txt'):
                txt_files.append(os.path.join(root, file))
    
    return txt_files


def detect_file_encoding(filepath: str, sample_size: int = 1024) -> str:
    """检测文件编码"""
    try:
        import chardet
        
        with open(filepath, 'rb') as f:
            raw_data = f.read(sample_size)
            
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        
        if encoding is None:
            encoding = 'gbk'  # 默认使用GBK
        
        return encoding.lower()
        
    except ImportError:
        logger.warning("chardet未安装，使用默认编码gbk")
        return 'gbk'
    except Exception as e:
        logger.error(f"检测文件编码失败 {filepath}: {e}")
        return 'gbk'


def backup_file(filepath: str, backup_dir: str = "backup") -> bool:
    """备份文件"""
    try:
        if not os.path.exists(filepath):
            return False
        
        ensure_directory(backup_dir)
        
        filename = os.path.basename(filepath)
        timestamp = os.path.getmtime(filepath)
        import datetime
        dt = datetime.datetime.fromtimestamp(timestamp)
        backup_name = f"{filename}.{dt.strftime('%Y%m%d_%H%M%S')}.bak"
        backup_path = os.path.join(backup_dir, backup_name)
        
        shutil.copy2(filepath, backup_path)
        logger.info(f"文件已备份: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"备份文件失败 {filepath}: {e}")
        return False


def count_lines_in_file(filepath: str) -> int:
    """统计文件行数"""
    try:
        with open(filepath, 'r', encoding='gbk') as f:
            return sum(1 for _ in f)
    except Exception as e:
        logger.error(f"统计文件行数失败 {filepath}: {e}")
        return 0


def format_rate_display(rate: float) -> str:
    """格式化爆率显示"""
    if rate <= 0:
        return "0%"
    elif rate >= 1:
        return "100%"
    elif rate >= 0.01:  # 大于1%
        return f"{rate*100:.2f}%"
    else:  # 小于1%
        return f"{rate*100:.6f}%"