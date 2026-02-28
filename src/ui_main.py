# src/ui_main.py
"""
主界面类
"""

import os
import logging
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from config.constants import *
from config.settings import Settings
from src.data_parser import LegendDropParser
from src.utils.file_utils import format_rate_display


logger = logging.getLogger(__name__)


class DropTableModel(QAbstractTableModel):
    """表格数据模型"""
    
    def __init__(self, data=None, headers=None):
        super().__init__()
        self._data = data or []
        self._headers = headers or []
    
    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        
        if role == Qt.DisplayRole:
            return str(self._data[index.row()][index.column()])
        elif role == Qt.TextAlignmentRole:
            if index.column() in [1, 2]:  # 爆率列居中对齐
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter
        
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None
    
    def update_data(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()


class LegendDropApp(QMainWindow):
    """主窗口类"""
    
    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.parser = LegendDropParser()
        self.current_item = None
        self.current_monster = None
        self.is_data_loaded = False
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """初始化界面"""
        # 窗口设置
        self.setWindowTitle(APP_TITLE)
        self.resize(*self.settings.get('window_size', [APP_WIDTH, APP_HEIGHT]))
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(10)
        
        # 创建左侧面板
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 2)
        
        # 创建中间面板
        middle_panel = self.create_middle_panel()
        main_layout.addWidget(middle_panel, 2)
        
        # 创建右侧面板
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 3)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 应用样式
        self.apply_styles()
    
    def create_left_panel(self):
        """创建左侧面板（物品搜索）"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(5)
        
        # 搜索框
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索物品名称...")
        self.search_box.setClearButtonEnabled(True)
        self.search_box.textChanged.connect(self.on_search_items)
        search_layout.addWidget(self.search_box)
        
        # 搜索按钮
        self.search_btn = QPushButton("搜索")
        self.search_btn.clicked.connect(self.on_search_items)
        search_layout.addWidget(self.search_btn)
        layout.addLayout(search_layout)
        
        # 物品列表
        layout.addWidget(QLabel("物品列表:"))
        
        self.item_table = QTableWidget()
        self.item_table.setColumnCount(2)
        self.item_table.setHorizontalHeaderLabels(["物品名称", "可掉落怪物数"])
        self.item_table.horizontalHeader().setStretchLastSection(True)
        self.item_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.item_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.item_table.itemClicked.connect(self.on_item_selected)
        
        # 设置列宽
        self.item_table.setColumnWidth(0, ITEM_COLUMN_WIDTH)
        self.item_table.setColumnWidth(1, 100)
        
        layout.addWidget(self.item_table)
        
        # 底部统计信息
        self.item_stats_label = QLabel("共加载 0 个物品")
        self.item_stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.item_stats_label)
        
        return panel
    
    def create_middle_panel(self):
        """创建中间面板（怪物列表）"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(5)
        
        # 怪物筛选
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("怪物筛选:"))
        
        self.monster_filter = QLineEdit()
        self.monster_filter.setPlaceholderText("筛选怪物...")
        self.monster_filter.textChanged.connect(self.on_filter_monsters)
        filter_layout.addWidget(self.monster_filter)
        layout.addLayout(filter_layout)
        
        # 怪物列表
        layout.addWidget(QLabel("掉落该物品的怪物:"))
        
        self.monster_table = QTableWidget()
        self.monster_table.setColumnCount(3)
        self.monster_table.setHorizontalHeaderLabels(["怪物名称", "爆率", "等级"])
        self.monster_table.horizontalHeader().setStretchLastSection(True)
        self.monster_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.monster_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.monster_table.itemClicked.connect(self.on_monster_selected)
        
        # 设置列宽
        self.monster_table.setColumnWidth(0, MONSTER_COLUMN_WIDTH)
        self.monster_table.setColumnWidth(1, RATE_COLUMN_WIDTH)
        self.monster_table.setColumnWidth(2, 80)
        
        layout.addWidget(self.monster_table)
        
        # 底部统计
        self.monster_stats_label = QLabel("共 0 个怪物可掉落")
        self.monster_stats_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.monster_stats_label)
        
        return panel
    
    def create_right_panel(self):
        """创建右侧面板（详细信息）"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setSpacing(5)
        
        # 详情标题
        title_layout = QHBoxLayout()
        self.detail_title = QLabel("爆率详情")
        self.detail_title.setAlignment(Qt.AlignCenter)
        self.detail_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        title_layout.addWidget(self.detail_title)
        layout.addLayout(title_layout)
        
        # 详细信息显示
        self.detail_text = QTextEdit()
        self.detail_text.setReadOnly(True)
        layout.addWidget(self.detail_text)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        
        self.copy_btn = QPushButton("复制详情")
        self.copy_btn.clicked.connect(self.copy_details)
        button_layout.addWidget(self.copy_btn)
        
        self.export_btn = QPushButton("导出数据")
        self.export_btn.clicked.connect(self.export_data)
        button_layout.addWidget(self.export_btn)
        
        layout.addLayout(button_layout)
        
        return panel
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件(&F)")
        
        open_action = QAction("打开数据目录...", self)
        open_action.triggered.connect(self.open_data_directory)
        file_menu.addAction(open_action)
        
        reload_action = QAction("重新加载数据", self)
        reload_action.triggered.connect(self.reload_data)
        reload_action.setShortcut("F5")
        file_menu.addAction(reload_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("导出为CSV...", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut("Ctrl+Q")
        file_menu.addAction(exit_action)
        
        # 查看菜单
        view_menu = menubar.addMenu("查看(&V)")
        
        show_toolbar = QAction("显示工具栏", self, checkable=True)
        show_toolbar.setChecked(self.settings.get('show_toolbar', True))
        show_toolbar.triggered.connect(self.toggle_toolbar)
        view_menu.addAction(show_toolbar)
        
        show_statusbar = QAction("显示状态栏", self, checkable=True)
        show_statusbar.setChecked(self.settings.get('show_statusbar', True))
        show_statusbar.triggered.connect(self.toggle_statusbar)
        view_menu.addAction(show_statusbar)
        
        # 工具菜单
        tools_menu = menubar.addMenu("工具(&T)")
        
        calc_action = QAction("爆率计算器...", self)
        calc_action.triggered.connect(self.show_calculator)
        tools_menu.addAction(calc_action)
        
        stats_action = QAction("数据统计", self)
        stats_action.triggered.connect(self.show_statistics)
        tools_menu.addAction(stats_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助(&H)")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_tool_bar(self):
        """创建工具栏"""
        toolbar = self.addToolBar("主工具栏")
        toolbar.setObjectName("MainToolbar")
        
        # 刷新按钮
        refresh_action = QAction(QIcon.fromTheme("view-refresh"), "刷新", self)
        refresh_action.triggered.connect(self.reload_data)
        toolbar.addAction(refresh_action)
        
        toolbar.addSeparator()
        
        # 搜索框
        toolbar.addWidget(QLabel("搜索:"))
        self.toolbar_search = QLineEdit()
        self.toolbar_search.setPlaceholderText("快速搜索...")
        self.toolbar_search.setMaximumWidth(200)
        self.toolbar_search.returnPressed.connect(self.quick_search)
        toolbar.addWidget(self.toolbar_search)
        
        # 显示/隐藏工具栏
        if not self.settings.get('show_toolbar', True):
            toolbar.setVisible(False)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = self.statusBar()
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        
        # 数据统计标签
        self.data_stats_label = QLabel("")
        self.status_bar.addPermanentWidget(self.data_stats_label)
        
        # 显示/隐藏状态栏
        if not self.settings.get('show_statusbar', True):
            self.status_bar.setVisible(False)
    
    def apply_styles(self):
        """应用样式"""
        # 基础样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTableWidget {
                border: 1px solid #ddd;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 5px;
                border: 1px solid #34495e;
                font-weight: bold;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            QPushButton {
                padding: 5px 10px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QTextEdit {
                border: 1px solid #ddd;
                background-color: white;
                font-family: "Microsoft YaHei", sans-serif;
            }
            QLabel {
                color: #333;
            }
        """)
    
    def load_data(self):
        """加载数据"""
        data_path = self.settings.get('data_path')
        
        if not os.path.exists(data_path):
            self.show_warning("数据目录不存在", f"请检查数据目录:\n{data_path}")
            return
        
        self.status_label.setText("正在加载数据...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        try:
            start_time = datetime.now()
            success = self.parser.parse_directory(data_path)
            
            if success:
                end_time = datetime.now()
                load_time = (end_time - start_time).total_seconds()
                
                # 更新统计信息
                stats = self.parser.monster_stats
                stats['parse_time'] = load_time
                
                # 显示物品列表
                self.refresh_item_list()
                
                # 更新状态栏
                self.data_stats_label.setText(f"怪物: {stats['total_monsters']} | 物品: {stats['total_items']} | 唯一物品: {stats['unique_items']}")
                self.status_label.setText(f"数据加载完成 ({load_time:.2f}秒)")
                
                self.is_data_loaded = True
                logger.info(f"数据加载成功，耗时{load_time:.2f}秒")
            else:
                self.status_label.setText("数据加载失败")
                self.show_warning("数据加载失败", "未找到有效的爆率文件")
                
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
            self.status_label.setText("数据加载失败")
            self.show_error("加载数据时出错", str(e))
        finally:
            QApplication.restoreOverrideCursor()
    
    def refresh_item_list(self):
        """刷新物品列表"""
        if not self.parser.item_index:
            return
        
        self.item_table.setRowCount(0)
        
        # 获取所有物品并排序
        items = list(self.parser.item_index.keys())
        items.sort()
        
        self.item_table.setRowCount(len(items))
        
        for i, item_name in enumerate(items):
            # 物品名称
            item_cell = QTableWidgetItem(item_name)
            self.item_table.setItem(i, 0, item_cell)
            
            # 可掉落怪物数
            drop_count = len(self.parser.item_index[item_name])
            count_cell = QTableWidgetItem(str(drop_count))
            count_cell.setTextAlignment(Qt.AlignCenter)
            self.item_table.setItem(i, 1, count_cell)
        
        self.item_stats_label.setText(f"共 {len(items)} 个物品")
    
    def on_search_items(self):
        """搜索物品"""
        keyword = self.search_box.text().strip()
        
        if not self.parser.item_index:
            return
        
        if not keyword:
            # 显示所有物品
            self.refresh_item_list()
            return
        
        # 搜索物品
        results = self.parser.search_items(keyword)
        
        # 更新表格
        self.item_table.setRowCount(len(results))
        
        for i, item_name in enumerate(results):
            item_cell = QTableWidgetItem(item_name)
            self.item_table.setItem(i, 0, item_cell)
            
            drop_count = len(self.parser.item_index[item_name])
            count_cell = QTableWidgetItem(str(drop_count))
            count_cell.setTextAlignment(Qt.AlignCenter)
            self.item_table.setItem(i, 1, count_cell)
        
        self.item_stats_label.setText(f"找到 {len(results)} 个物品")
    
    def on_item_selected(self, item):
        """物品被选中时触发"""
        if item.column() == 0:  # 只响应第一列的点击
            item_name = item.text()
            self.current_item = item_name
            self.show_item_drops(item_name)
    
    def show_item_drops(self, item_name):
        """显示物品的掉落信息"""
        if item_name not in self.parser.item_index:
            return
        
        drops = self.parser.item_index[item_name]
        
        # 按爆率排序（从高到低）
        drops.sort(key=lambda x: x[1], reverse=True)
        
        # 更新怪物表格
        self.monster_table.setRowCount(len(drops))
        
        for i, (monster_name, rate) in enumerate(drops):
            # 怪物名称
            monster_cell = QTableWidgetItem(monster_name)
            self.monster_table.setItem(i, 0, monster_cell)
            
            # 爆率（多种格式显示）
            rate_cell = QTableWidgetItem(format_rate_display(rate))
            rate_cell.setTextAlignment(Qt.AlignCenter)
            self.monster_table.setItem(i, 1, rate_cell)
            
            # 等级（这里可以扩展从怪物数据中获取）
            level_cell = QTableWidgetItem("N/A")
            level_cell.setTextAlignment(Qt.AlignCenter)
            self.monster_table.setItem(i, 2, level_cell)
        
        self.monster_stats_label.setText(f"共 {len(drops)} 个怪物可掉落")
        
        # 更新详情标题
        self.detail_title.setText(f"物品详情: {item_name}")
        
        # 清空详情
        self.detail_text.clear()
        
        # 显示物品的简要信息
        self.status_label.setText(f"已选择物品: {item_name}")
    
    def on_filter_monsters(self):
        """筛选怪物"""
        keyword = self.monster_filter.text().strip().lower()
        
        for i in range(self.monster_table.rowCount()):
            monster_name = self.monster_table.item(i, 0).text().lower()
            visible = not keyword or keyword in monster_name
            self.monster_table.setRowHidden(i, not visible)
    
    def on_monster_selected(self, item):
        """怪物被选中时触发"""
        if item.column() == 0:  # 只响应怪物名称列的点击
            monster_name = item.text()
            item_name = self.current_item
            
            if not item_name:
                return
            
            # 查找具体的爆率
            drops = self.parser.item_index.get(item_name, [])
            rate = None
            for drop_monster, drop_rate in drops:
                if drop_monster == monster_name:
                    rate = drop_rate
                    break
            
            if rate is not None:
                self.current_monster = monster_name
                self.show_drop_details(item_name, monster_name, rate)
    
    def show_drop_details(self, item_name, monster_name, rate):
        """显示详细的掉落信息"""
        details = f"""
        <div style="font-family: 'Microsoft YaHei', sans-serif;">
            <h2 style="color: #2c3e50; text-align: center;">爆率详情</h2>
            
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9; width: 30%;">
                        <strong>物品名称:</strong>
                    </td>
                    <td style="padding: 8px; border: 1px solid #ddd; width: 70%;">
                        {item_name}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9;">
                        <strong>怪物名称:</strong>
                    </td>
                    <td style="padding: 8px; border: 1px solid #ddd;">
                        {monster_name}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9;">
                        <strong>爆率:</strong>
                    </td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #e74c3c; font-weight: bold;">
                        {rate * 100:.6f}%
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9;">
                        <strong>分数形式:</strong>
                    </td>
                    <td style="padding: 8px; border: 1px solid #ddd;">
                        约 1/{int(1/rate) if rate > 0 else "∞"}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd; background-color: #f9f9f9;">
                        <strong>期望击杀数:</strong>
                    </td>
                    <td style="padding: 8px; border: 1px solid #ddd;">
                        {int(1/rate) if rate > 0 else "∞"} 只
                    </td>
                </tr>
            </table>
            
            <h3 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 5px;">
                该怪物其他掉落:
            </h3>
            <ul style="max-height: 300px; overflow-y: auto;">
        """
        
        # 获取该怪物的其他掉落
        if monster_name in self.parser.drop_data:
            monster_info = self.parser.drop_data[monster_name]
            other_drops = []
            
            for drop_item in monster_info.drop_items:
                if drop_item.name != item_name:
                    other_drops.append((drop_item.name, drop_item.rate))
            
            # 按爆率排序
            other_drops.sort(key=lambda x: x[1], reverse=True)
            
            # 只显示前20个
            for other_item, other_rate in other_drops[:20]:
                if other_rate >= 0.01:
                    rate_display = f"{other_rate*100:.2f}%"
                else:
                    rate_display = f"{other_rate*100:.6f}%"
                
                details += f"""
                <li style="margin-bottom: 5px;">
                    <strong>{other_item}</strong> - {rate_display}
                </li>
                """
            
            if len(other_drops) > 20:
                details += f'<li style="color: #7f8c8d;">... 等{len(other_drops)}个物品</li>'
        
        details += """
            </ul>
            
            <div style="margin-top: 20px; padding: 10px; background-color: #f8f9fa; border-radius: 5px; border-left: 4px solid #3498db;">
                <strong>温馨提示:</strong> 传奇游戏的爆率通常很低，请耐心刷怪！
            </div>
        </div>
        """
        
        self.detail_text.setHtml(details)
        self.status_label.setText(f"查看: {item_name} → {monster_name}")
    
    def copy_details(self):
        """复制详情到剪贴板"""
        if self.detail_text.toPlainText():
            QApplication.clipboard().setText(self.detail_text.toPlainText())
            self.status_label.setText("详情已复制到剪贴板")
    
    def export_data(self):
        """导出数据"""
        if not self.parser.drop_data:
            self.show_warning("没有数据", "请先加载数据")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出数据", "传奇掉落数据.csv", "CSV文件 (*.csv)"
        )
        
        if file_path:
            success = self.parser.export_to_csv(file_path)
            if success:
                self.show_info("导出成功", f"数据已导出到:\n{file_path}")
            else:
                self.show_error("导出失败", "请检查文件路径和权限")
    
    def open_data_directory(self):
        """打开数据目录"""
        data_path = self.settings.get('data_path')
        
        if os.path.exists(data_path):
            try:
                import subprocess
                
                if sys.platform == 'win32':
                    os.startfile(data_path)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.call(['open', data_path])
                else:  # Linux
                    subprocess.call(['xdg-open', data_path])
                    
                self.status_label.setText(f"已打开数据目录: {data_path}")
            except Exception as e:
                self.show_error("打开失败", str(e))
        else:
            self.show_warning("目录不存在", f"数据目录不存在:\n{data_path}")
    
    def reload_data(self):
        """重新加载数据"""
        self.load_data()
        self.status_label.setText("数据已重新加载")
    
    def quick_search(self):
        """工具栏快速搜索"""
        keyword = self.toolbar_search.text().strip()
        if keyword:
            self.search_box.setText(keyword)
            self.on_search_items()
    
    def toggle_toolbar(self, visible):
        """切换工具栏显示"""
        toolbar = self.findChild(QToolBar, "MainToolbar")
        if toolbar:
            toolbar.setVisible(visible)
            self.settings.set('show_toolbar', visible)
            self.settings.save_settings()
    
    def toggle_statusbar(self, visible):
        """切换状态栏显示"""
        self.status_bar.setVisible(visible)
        self.settings.set('show_statusbar', visible)
        self.settings.save_settings()
    
    def show_calculator(self):
        """显示爆率计算器"""
        # 这里可以扩展一个爆率计算器对话框
        QMessageBox.information(self, "爆率计算器", "爆率计算器功能开发中...")
    
    def show_statistics(self):
        """显示数据统计"""
        if not self.parser.drop_data:
            self.show_warning("没有数据", "请先加载数据")
            return
        
        stats = self.parser.monster_stats
        
        message = f"""
        <h3>数据统计</h3>
        <table style="border-collapse: collapse; width: 100%;">
            <tr><td style="padding: 5px;">数据目录:</td><td style="padding: 5px;"><strong>{stats['directory']}</strong></td></tr>
            <tr><td style="padding: 5px;">怪物总数:</td><td style="padding: 5px;"><strong>{stats['total_monsters']}</strong></td></tr>
            <tr><td style="padding: 5px;">掉落总数:</td><td style="padding: 5px;"><strong>{stats['total_items']}</strong></td></tr>
            <tr><td style="padding: 5px;">唯一物品数:</td><td style="padding: 5px;"><strong>{stats['unique_items']}</strong></td></tr>
        </table>
        
        <h4>怪物掉落统计:</h4>
        <ul>
        """
        
        # 统计掉落最多的怪物
        drop_counts = []
        for monster_name, monster_info in self.parser.drop_data.items():
            drop_counts.append((monster_name, monster_info.get_total_drop_items()))
        
        drop_counts.sort(key=lambda x: x[1], reverse=True)
        
        for monster_name, count in drop_counts[:10]:  # 显示前10
            message += f"<li>{monster_name}: {count}个物品</li>"
        
        message += "</ul>"
        
        QMessageBox.information(self, "数据统计", message)
    
    def show_about(self):
        """显示关于对话框"""
        about_text = f"""
        <h2>{APP_TITLE}</h2>
        <p>版本: {APP_VERSION}</p>
        <p>一个用于解析传奇游戏爆率文件的工具</p>
        <p>支持格式:</p>
        <ul>
            <li>标准爆率行: 1/1000 物品名</li>
            <li>子爆率结构: #CHILD 1/10 RANDOM (...) </li>
        </ul>
        <p>GitHub: <a href="https://github.com/yourusername/LegendDropTool">项目地址</a></p>
        <hr>
        <p>© 2024 传奇掉落查询工具. 保留所有权利.</p>
        """
        
        QMessageBox.about(self, "关于", about_text)
    
    def show_warning(self, title, message):
        """显示警告对话框"""
        QMessageBox.warning(self, title, message)
    
    def show_error(self, title, message):
        """显示错误对话框"""
        QMessageBox.critical(self, title, message)
    
    def show_info(self, title, message):
        """显示信息对话框"""
        QMessageBox.information(self, title, message)
    
    def closeEvent(self, event):
        """关闭事件处理"""
        # 保存窗口设置
        self.settings.set('window_size', [self.width(), self.height()])
        self.settings.set('window_position', [self.x(), self.y()])
        self.settings.save_settings()
        
        # 确认退出
        reply = QMessageBox.question(
            self, '确认退出',
            '确定要退出程序吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            event.accept()
            logger.info("程序正常退出")
        else:
            event.ignore()