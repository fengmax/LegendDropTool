#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
传奇掉落查询工具 - 完整修复版本
支持标准传奇爆率文件格式，包括#CHILD结构
"""

import sys
import os
import re
from fractions import Fraction
from collections import defaultdict
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# settings persistence
from config.settings import Settings


class DropDataParser:
    """爆率数据解析器"""
    
    def __init__(self, data_dir="data/MonItems"):
        self.data_dir = data_dir
        self.drop_data = defaultdict(list)  # {怪物名: [(物品名, 爆率)]}
        self.item_index = defaultdict(list)  # {物品名: [(怪物名, 爆率)]}
    
    def parse_file(self, filepath):
        """解析单个爆率文件"""
        monster_name = os.path.splitext(os.path.basename(filepath))[0]
        drops = []
        
        try:
            with open(filepath, 'r', encoding='gbk', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            i = 0
            
            while i < len(lines):
                line = lines[i].strip()
                
                # 跳过空行和注释
                if not line or (line.startswith('#') and not line.startswith('#CHILD')):
                    i += 1
                    continue
                
                # 处理#CHILD结构
                if line.startswith('#CHILD'):
                    parts = line.split()
                    if len(parts) >= 3:
                        child_rate_str = parts[1]
                        child_rate = float(Fraction(child_rate_str))
                        
                        # 查找括号开始
                        while i < len(lines) and lines[i].strip() != '(':
                            i += 1
                        
                        if i < len(lines):
                            i += 1  # 跳过'('
                            child_items = []
                            
                            # 收集括号内的物品
                            while i < len(lines) and lines[i].strip() != ')':
                                item_line = lines[i].strip()
                                if item_line:
                                    item_parts = item_line.split()
                                    if len(item_parts) >= 2:
                                        item_name = ' '.join(item_parts[1:])
                                        child_items.append(item_name)
                                i += 1
                            
                            # 为每个物品计算实际爆率
                            if child_items:
                                actual_rate = child_rate * (1 / len(child_items))
                                for item in child_items:
                                    drops.append((item, actual_rate))
                    
                    i += 1
                    continue
                
                # 普通爆率行
                parts = line.split()
                if len(parts) >= 2:
                    rate_str = parts[0]
                    item_name = ' '.join(parts[1:])
                    
                    try:
                        rate = float(Fraction(rate_str))
                        if rate > 0:
                            drops.append((item_name, rate))
                    except:
                        pass
                
                i += 1
            
            self.drop_data[monster_name] = drops
            
            # 更新物品索引
            for item_name, rate in drops:
                self.item_index[item_name].append((monster_name, rate))
                
            return True
            
        except Exception as e:
            print(f"解析文件 {filepath} 失败: {e}")
            return False
    
    def load_all(self):
        """加载所有爆率文件"""
        if not os.path.exists(self.data_dir):
            print(f"数据目录不存在: {self.data_dir}")
            return False
        
        count = 0
        for filename in os.listdir(self.data_dir):
            if filename.endswith('.txt'):
                filepath = os.path.join(self.data_dir, filename)
                if self.parse_file(filepath):
                    count += 1
        
        print(f"成功加载 {count} 个怪物文件")
        return count > 0


class LegendDropApp(QMainWindow):
    """主应用程序窗口"""
    
    def __init__(self):
        super().__init__()
        self.parser = DropDataParser()
        self.current_item = None
        self.init_ui()
        
        # 加载数据
        QTimer.singleShot(100, self.load_data)
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("传奇掉落查询工具 v1.0")
        self.setGeometry(100, 100, 1200, 700)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧面板 - 物品搜索
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # 搜索框
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 搜索物品...")
        self.search_box.textChanged.connect(self.filter_items)
        search_layout.addWidget(self.search_box)
        
        self.search_btn = QPushButton("搜索")
        self.search_btn.clicked.connect(self.filter_items)
        search_layout.addWidget(self.search_btn)
        left_layout.addLayout(search_layout)
        
        # 物品列表
        left_layout.addWidget(QLabel("物品列表:"))
        self.item_list = QListWidget()
        self.item_list.itemClicked.connect(self.on_item_selected)
        left_layout.addWidget(self.item_list)
        
        # 中间面板 - 怪物列表
        middle_panel = QWidget()
        middle_layout = QVBoxLayout(middle_panel)
        middle_layout.addWidget(QLabel("掉落怪物:"))
        
        self.monster_list = QListWidget()
        self.monster_list.itemClicked.connect(self.on_monster_selected)
        middle_layout.addWidget(self.monster_list)
        
        # 右侧面板 - 详情
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(QLabel("爆率详情:"))
        
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        right_layout.addWidget(self.detail_text)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("刷新数据")
        self.refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(self.refresh_btn)
        
        self.export_btn = QPushButton("导出数据")
        self.export_btn.clicked.connect(self.export_data)
        btn_layout.addWidget(self.export_btn)
        
        right_layout.addLayout(btn_layout)
        
        # 添加到主布局
        main_layout.addWidget(left_panel, 2)
        main_layout.addWidget(middle_panel, 2)
        main_layout.addWidget(right_panel, 3)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.status_bar = self.statusBar()
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        open_action = QAction("打开数据目录", self)
        open_action.triggered.connect(self.open_data_directory)
        file_menu.addAction(open_action)
        
        # 新增：手动选择数据目录
        import_dir_action = QAction("导入数据目录", self)
        import_dir_action.triggered.connect(self.choose_data_directory)
        file_menu.addAction(import_dir_action)
        
        reload_action = QAction("重新加载数据", self)
        reload_action.triggered.connect(self.load_data)
        reload_action.setShortcut("F5")
        file_menu.addAction(reload_action)
        
        # 自定义字体族
        font_family_action = QAction("设置字体", self)
        font_family_action.triggered.connect(self.choose_font)
        file_menu.addAction(font_family_action)
        
        file_menu.addSeparator()
        
        # 修正：使用正确的方法名
        export_action = QAction("导出数据", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Ctrl+Q")
        file_menu.addAction(exit_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def load_data(self):
        """加载数据"""
        self.status_label.setText("正在加载数据...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        try:
            success = self.parser.load_all()
            
            if success:
                # 更新物品列表
                self.refresh_item_list()
                self.status_label.setText(f"加载完成: {len(self.parser.item_index)} 个物品")
            else:
                self.status_label.setText("加载失败，请检查数据目录")
                QMessageBox.warning(self, "加载失败", "未找到有效的爆率文件")
                
        except Exception as e:
            self.status_label.setText("加载出错")
            QMessageBox.critical(self, "错误", f"加载数据时出错:\n{str(e)}")
        finally:
            QApplication.restoreOverrideCursor()
    
    def refresh_item_list(self):
        """刷新物品列表"""
        self.item_list.clear()
        
        if not self.parser.item_index:
            return
        
        # 获取所有物品并排序
        items = sorted(self.parser.item_index.keys())
        self.item_list.addItems(items)
    
    def filter_items(self):
        """过滤物品列表"""
        keyword = self.search_box.text().strip().lower()
        
        if not keyword:
            self.refresh_item_list()
            return
        
        self.item_list.clear()
        
        # 搜索物品
        for item_name in self.parser.item_index.keys():
            if keyword in item_name.lower():
                self.item_list.addItem(item_name)
    
    def on_item_selected(self, item):
        """选择物品"""
        item_name = item.text()
        self.current_item = item_name
        
        if item_name in self.parser.item_index:
            drops = self.parser.item_index[item_name]
            
            # 去重怪物名并选取最高爆率
            unique = {}
            for monster, rate in drops:
                if monster not in unique or rate > unique[monster]:
                    unique[monster] = rate
            # 重新构建列表
            drops = [(m, r) for m, r in unique.items()]
            
            # 按爆率排序
            drops.sort(key=lambda x: x[1], reverse=True)
            
            # 更新怪物列表
            self.monster_list.clear()
            for monster_name, rate in drops:
                # 格式化显示
                if rate >= 0.01:
                    rate_str = f"{rate*100:.2f}%"
                else:
                    rate_str = f"{rate*100:.6f}%"
                
                list_item = QListWidgetItem(f"{monster_name} ({rate_str})")
                list_item.setData(Qt.UserRole, (monster_name, rate))
                self.monster_list.addItem(list_item)
            
            # 清空详情
            self.detail_text.clear()
    
    def on_monster_selected(self, item):
        """选择怪物"""
        if not self.current_item:
            return
        
        monster_name, rate = item.data(Qt.UserRole)
        item_name = self.current_item
        
        # 构建详情
        if rate >= 0.01:
            rate_str = f"{rate*100:.2f}%"
        else:
            rate_str = f"{rate*100:.6f}%"
        
        details = f"""
        <h3>爆率详情</h3>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr>
                <td style="padding: 5px; width: 30%;"><b>物品名称:</b></td>
                <td style="padding: 5px;">{item_name}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>怪物名称:</b></td>
                <td style="padding: 5px;">{monster_name}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>爆率:</b></td>
                <td style="padding: 5px; color: red; font-weight: bold;">{rate_str}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>分数形式:</b></td>
                <td style="padding: 5px;">约 1/{int(1/rate) if rate > 0 else "∞"}</td>
            </tr>
            <tr>
                <td style="padding: 5px;"><b>期望击杀数:</b></td>
                <td style="padding: 5px;">{int(1/rate) if rate > 0 else "∞"} 只</td>
            </tr>
        </table>
        
        <h4>该怪物其他掉落:</h4>
        <div style="max-height:200px; overflow:auto; border:1px solid #ccc; padding:5px;">
        <ul>
        """
        
        # 获取该怪物的其他掉落
        if monster_name in self.parser.drop_data:
            other_drops = [(item, r) for item, r in self.parser.drop_data[monster_name] 
                          if item != item_name]
            other_drops.sort(key=lambda x: x[1], reverse=True)
            
            for other_item, other_rate in other_drops:  # 显示全部
                if other_rate >= 0.01:
                    other_rate_str = f"{other_rate*100:.2f}%"
                else:
                    other_rate_str = f"{other_rate*100:.6f}%"
                
                details += f"<li>{other_item}: {other_rate_str}</li>"
        
        details += "</ul></div>"
        self.detail_text.setHtml(details)
    
    def open_data_directory(self):
        """打开数据目录"""
        data_dir = self.parser.data_dir
        
        if os.path.exists(data_dir):
            try:
                if sys.platform == 'win32':
                    os.startfile(data_dir)
                else:
                    QMessageBox.information(self, "打开目录", 
                                          f"数据目录位置:\n{os.path.abspath(data_dir)}")
                self.status_label.setText("已打开数据目录")
            except:
                QMessageBox.information(self, "打开目录", 
                                      f"数据目录位置:\n{os.path.abspath(data_dir)}")
        else:
            QMessageBox.warning(self, "目录不存在", 
                              f"数据目录不存在:\n{os.path.abspath(data_dir)}")

    def choose_data_directory(self):
        """让用户选择数据目录，复制内容到 data/MonItems 并重新加载"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择数据目录", self.parser.data_dir)
        if dir_path:
            # 将选定目录中的 txt 文件复制到工作目录的 data/MonItems
            target_dir = os.path.join(os.getcwd(), "data", "MonItems")
            os.makedirs(target_dir, exist_ok=True)
            copied = 0
            for fname in os.listdir(dir_path):
                if fname.lower().endswith('.txt'):
                    src = os.path.join(dir_path, fname)
                    dst = os.path.join(target_dir, fname)
                    try:
                        import shutil
                        shutil.copy2(src, dst)
                        copied += 1
                    except Exception:
                        pass
            # 更新解析器路径指向 data/MonItems
            self.parser.data_dir = target_dir
            self.status_label.setText(f"已从{dir_path}导入{copied}个文件到{target_dir}")
            self.load_data()

    def choose_font(self):
        """弹出字体对话框选择字体族和大小"""
        current_font = QApplication.font()
        font, ok = QFontDialog.getFont(current_font, self, "选择字体")
        if ok:
            QApplication.setFont(font)
            self.status_label.setText(f"字体设置为 {font.family()} {font.pointSize()}")
            # 保存到设置
            try:
                settings = Settings()
                settings.set('font_family', font.family())
                settings.set('font_size', font.pointSize())
                settings.save_settings()
            except Exception:
                pass
    
    def export_data(self):
        """导出数据"""
        if not self.parser.drop_data:
            QMessageBox.warning(self, "没有数据", "请先加载数据")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出数据", "传奇掉落数据.csv", "CSV文件 (*.csv)"
        )
        
        if file_path:
            try:
                import csv
                
                with open(file_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['怪物名称', '物品名称', '爆率', '爆率百分比'])
                    
                    for monster_name, drops in self.parser.drop_data.items():
                        for item_name, rate in drops:
                            writer.writerow([
                                monster_name,
                                item_name,
                                f"1/{int(1/rate) if rate > 0 else '∞'}",
                                f"{rate*100:.6f}%"
                            ])
                
                QMessageBox.information(self, "导出成功", f"数据已导出到:\n{file_path}")
                self.status_label.setText(f"数据已导出到: {os.path.basename(file_path)}")
                
            except Exception as e:
                QMessageBox.critical(self, "导出失败", f"导出时出错:\n{str(e)}")
    
    def show_about(self):
        """显示关于对话框"""
        about_text = """
        <h2>传奇掉落查询工具 v1.0</h2>
        <p>一个用于解析传奇游戏爆率文件的工具</p>
        <p>支持格式:</p>
        <ul>
            <li>标准爆率行: 1/1000 物品名</li>
            <li>子爆率结构: #CHILD 1/10 RANDOM (...) </li>
        </ul>
        <hr>
        <p>使用方法:</p>
        <ol>
            <li>将传奇爆率文件放在 data/MonItems 目录下</li>
            <li>点击"重新加载数据"或按F5刷新</li>
            <li>在左侧搜索和选择物品</li>
            <li>中间查看掉落怪物</li>
            <li>右侧查看详细爆率信息</li>
        </ol>
        <p>© 2026 传奇俱乐部</p>
        """
        
        QMessageBox.about(self, "关于", about_text)


def main():
    app = QApplication(sys.argv)
    
    # 使用中文本地化，确保各种标准按钮和对话框为中文
    from PyQt5.QtCore import QLocale
    QLocale.setDefault(QLocale(QLocale.Chinese))
    
    # 加载设置并应用已保存字体
    settings = Settings()
    font = app.font()
    fam = settings.get('font_family')
    sz = settings.get('font_size')
    if fam:
        font.setFamily(fam)
    if sz:
        try:
            font.setPointSize(int(sz))
        except:
            pass
    if not fam and not sz:
        # 默认字体设为微软雅黑
        try:
            font.setFamily("Microsoft YaHei")
            font.setPointSize(9)
        except Exception:
            pass
    app.setFont(font)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    # 创建并显示窗口
    window = LegendDropApp()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    # 创建必要的目录
    os.makedirs("data/MonItems", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # 检查是否有数据文件
    if not os.listdir("data/MonItems"):
        print("提示: data/MonItems 目录为空")
        print("请将你的传奇爆率文件(.txt)放在此目录下")
    
    main()