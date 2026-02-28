# setup.py
"""
打包配置文件
"""

from setuptools import setup
import sys
from cx_Freeze import setup, Executable

# 应用程序的基本信息
app_name = "LegendDropTool"
app_version = "1.0.0"
app_description = "传奇物品掉落查询工具"
author = "Your Name"
author_email = "your.email@example.com"

# 构建选项
build_exe_options = {
    "packages": [
        "os", "sys", "re", "json", "logging", "datetime",
        "collections", "typing", "fractions", "math"
    ],
    "excludes": ["tkinter", "test", "unittest"],
    "include_files": [
        ("data", "data"),           # 数据目录
        ("resources", "resources"), # 资源目录
        ("README.md", "README.md")  # 说明文档
    ],
    "optimize": 2,
    "include_msvcr": True,
    "silent": True,
}

# 排除不需要的包
for exclude in ["PyQt5.QtWebEngine", "PyQt5.QtWebEngineCore", "PyQt5.QtWebChannel"]:
    if exclude in build_exe_options.get("packages", []):
        build_exe_options["packages"].remove(exclude)

# Windows特定设置
base = None
if sys.platform == "win32":
    base = "Win32GUI"
    icon_path = "resources/icons/app_icon.ico"
else:
    icon_path = None

# 可执行文件定义
executables = [
    Executable(
        "main.py",
        base=base,
        target_name="LegendDropTool.exe",
        icon=icon_path,
        shortcut_name="传奇掉落查询工具",
        shortcut_dir="DesktopFolder"
    )
]

# setup函数
setup(
    name=app_name,
    version=app_version,
    description=app_description,
    author=author,
    author_email=author_email,
    options={"build_exe": build_exe_options},
    executables=executables
)