# src/data_parser.py
"""
传奇爆率文件解析器
"""

import os
import re
import logging
from fractions import Fraction
from collections import defaultdict, OrderedDict
from typing import List, Tuple, Dict, Optional

from config.constants import ENCODING, CHILD_MARKER, RANDOM_MARKER


logger = logging.getLogger(__name__)


class DropItem:
    """掉落物品类"""
    
    def __init__(self, name: str, rate: float, is_child: bool = False, child_group: Optional[str] = None):
        self.name = name
        self.rate = rate
        self.is_child = is_child
        self.child_group = child_group
        
    def __repr__(self):
        return f"DropItem({self.name}, {self.rate*100:.4f}%)"


class MonsterDropInfo:
    """怪物掉落信息类"""
    
    def __init__(self, monster_name: str):
        self.monster_name = monster_name
        self.drop_items = []  # List[DropItem]
        self.child_groups = {}  # Dict[str, List[DropItem]]
        
    def add_item(self, item: DropItem):
        self.drop_items.append(item)
        
    def add_child_group(self, group_id: str, items: List[DropItem], total_rate: float):
        for item in items:
            item.is_child = True
            item.child_group = group_id
            # 重新计算每个物品的实际爆率
            actual_rate = total_rate * (1 / len(items))
            item.rate = actual_rate
            self.drop_items.append(item)
        
        self.child_groups[group_id] = items
        
    def get_total_drop_items(self) -> int:
        return len(self.drop_items)
    
    def get_items_by_type(self, type_filter: str = None) -> List[DropItem]:
        """按物品类型过滤（需要扩展）"""
        if not type_filter:
            return self.drop_items
        
        # 这里可以添加物品类型判断逻辑
        return [item for item in self.drop_items if type_filter in item.name]


class LegendDropParser:
    """传奇爆率文件解析器"""
    
    def __init__(self, encoding: str = ENCODING):
        self.encoding = encoding
        self.drop_data = OrderedDict()  # {怪物名: MonsterDropInfo}
        self.item_index = defaultdict(list)  # {物品名: [(怪物名, 爆率)]}
        self.monster_stats = {}  # 怪物统计信息
        
    def parse_fraction(self, fraction_str: str) -> float:
        """解析分数字符串为浮点数"""
        try:
            # 移除可能的空格
            fraction_str = fraction_str.strip()
            
            # 处理特殊情况
            if fraction_str == '0':
                return 0.0
            if '/' not in fraction_str:
                # 尝试直接转换
                return float(fraction_str)
            
            # 使用Fraction确保精度
            return float(Fraction(fraction_str))
            
        except (ValueError, ZeroDivisionError) as e:
            logger.warning(f"无法解析分数 '{fraction_str}': {e}")
            return 0.0
    
    def clean_item_name(self, name: str) -> str:
        """清理物品名称"""
        # 移除可能的注释标记
        name = name.strip()
        
        # 移除开头的#号
        if name.startswith('#'):
            name = name[1:].strip()
            
        return name
    
    def parse_monster_file(self, filepath: str) -> Optional[MonsterDropInfo]:
        """解析单个怪物爆率文件"""
        try:
            monster_name = os.path.splitext(os.path.basename(filepath))[0]
            monster_info = MonsterDropInfo(monster_name)
            
            with open(filepath, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            lines = content.split('\n')
            i = 0
            
            while i < len(lines):
                line = lines[i].strip()
                
                # 跳过空行和注释行（以#开头但不是#CHILD）
                if not line or (line.startswith('#') and not line.startswith(CHILD_MARKER)):
                    i += 1
                    continue
                
                # 处理#CHILD结构
                if line.startswith(CHILD_MARKER):
                    parts = line.split()
                    if len(parts) >= 3 and parts[2] == RANDOM_MARKER:
                        # 解析子爆率
                        child_rate_str = parts[1]
                        child_rate = self.parse_fraction(child_rate_str)
                        
                        # 查找括号开始
                        bracket_start = i
                        while bracket_start < len(lines) and lines[bracket_start].strip() != '(':
                            bracket_start += 1
                        
                        if bracket_start < len(lines):
                            # 查找括号结束
                            bracket_end = bracket_start
                            while bracket_end < len(lines) and lines[bracket_end].strip() != ')':
                                bracket_end += 1
                            
                            if bracket_end < len(lines):
                                # 解析括号内的物品
                                child_items = []
                                for j in range(bracket_start + 1, bracket_end):
                                    item_line = lines[j].strip()
                                    if item_line:
                                        item_parts = item_line.split()
                                        if len(item_parts) >= 2:
                                            # 括号内的1/1只是占位符，实际爆率由#CHILD控制
                                            item_name = self.clean_item_name(' '.join(item_parts[1:]))
                                            child_items.append(DropItem(item_name, 0.0))
                                
                                if child_items:
                                    group_id = f"child_group_{len(monster_info.child_groups)}"
                                    monster_info.add_child_group(group_id, child_items, child_rate)
                                
                                # 跳过已处理的括号内容
                                i = bracket_end + 1
                                continue
                
                # 普通爆率行
                parts = line.split()
                if len(parts) >= 2:
                    rate_str = parts[0]
                    item_name = self.clean_item_name(' '.join(parts[1:]))
                    
                    # 解析爆率
                    rate = self.parse_fraction(rate_str)
                    
                    # 跳过爆率为0的物品（如果有的话）
                    if rate > 0:
                        item = DropItem(item_name, rate)
                        monster_info.add_item(item)
                
                i += 1
            
            return monster_info
            
        except Exception as e:
            logger.error(f"解析文件 {filepath} 失败: {e}")
            return None
    
    def parse_directory(self, directory: str) -> bool:
        """解析指定目录下的所有爆率文件"""
        if not os.path.exists(directory):
            logger.error(f"目录不存在: {directory}")
            return False
        
        self.drop_data.clear()
        self.item_index.clear()
        
        files_parsed = 0
        total_items = 0
        
        for filename in os.listdir(directory):
            if filename.lower().endswith('.txt'):
                filepath = os.path.join(directory, filename)
                monster_info = self.parse_monster_file(filepath)
                
                if monster_info:
                    monster_name = monster_info.monster_name
                    self.drop_data[monster_name] = monster_info
                    
                    # 添加到物品索引
                    for item in monster_info.drop_items:
                        self.item_index[item.name].append((monster_name, item.rate))
                    
                    files_parsed += 1
                    total_items += monster_info.get_total_drop_items()
        
        # 生成统计信息
        self.monster_stats = {
            'total_monsters': files_parsed,
            'total_items': total_items,
            'unique_items': len(self.item_index),
            'directory': directory,
            'parse_time': None,  # 可以在调用时设置
        }
        
        logger.info(f"解析完成: {files_parsed} 个怪物文件, {total_items} 个掉落项, {len(self.item_index)} 个唯一物品")
        return files_parsed > 0
    
    def build_item_index(self) -> Dict[str, List[Tuple[str, float]]]:
        """构建物品到怪物的反向索引（已优化版本）"""
        # 已经在上面的parse_directory中构建了，这里可以直接返回
        return self.item_index
    
    def search_items(self, keyword: str) -> List[str]:
        """搜索物品（支持模糊搜索）"""
        keyword = keyword.lower().strip()
        if not keyword:
            return list(self.item_index.keys())
        
        results = []
        for item_name in self.item_index.keys():
            if keyword in item_name.lower():
                results.append(item_name)
        
        return results
    
    def search_monsters(self, keyword: str) -> List[str]:
        """搜索怪物"""
        keyword = keyword.lower().strip()
        if not keyword:
            return list(self.drop_data.keys())
        
        results = []
        for monster_name in self.drop_data.keys():
            if keyword in monster_name.lower():
                results.append(monster_name)
        
        return results
    
    def get_monster_drops(self, monster_name: str) -> List[Tuple[str, float]]:
        """获取指定怪物的所有掉落"""
        if monster_name in self.drop_data:
            monster_info = self.drop_data[monster_name]
            return [(item.name, item.rate) for item in monster_info.drop_items]
        return []
    
    def get_item_drops(self, item_name: str) -> List[Tuple[str, float]]:
        """获取指定物品的所有掉落来源"""
        return self.item_index.get(item_name, [])
    
    def export_to_csv(self, output_path: str) -> bool:
        """导出数据到CSV文件"""
        try:
            import csv
            
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['怪物名称', '物品名称', '爆率', '爆率百分比', '备注'])
                
                for monster_name, monster_info in self.drop_data.items():
                    for item in monster_info.drop_items:
                        rate_percent = item.rate * 100
                        note = "子掉落" if item.is_child else ""
                        writer.writerow([
                            monster_name,
                            item.name,
                            f"1/{int(1/item.rate) if item.rate > 0 else '∞'}",
                            f"{rate_percent:.6f}%",
                            note
                        ])
            
            logger.info(f"数据已导出到: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            return False