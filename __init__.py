# __init__.py (插件主文件)

import sys
import os
import subprocess
import importlib
import traceback
import sqlite3
from aqt import mw, gui_hooks
from aqt.utils import showInfo

from PyQt6.QtGui import QAction, QShortcut, QKeySequence, QActionGroup
from PyQt6.QtWidgets import QMenu

from .config import get_pomodoro_timer, get_timer_label, set_pomodoro_timer, get_config, save_config
from .hooks import on_reviewer_did_start, on_state_did_change, start_pomodoro_manually, show_statistics_dialog, cleanup_on_unload, toggle_pomodoro_timer, show_pomodoro_exit_dialog, do_not_remind_this_session, review_start_time, review_reminder_sent
from .ui import ConfigDialog, show_timer_in_statusbar
from .ui.countdown_dialog import show_countdown_dialog
from .ui.checkin_dialog import show_checkin_dialog
from .constants import log, AVAILABLE_SOUND_EFFECTS, DEFAULT_SOUND_EFFECT_FILE
from .storage import get_storage

# 检查和安装依赖项
def check_dependencies():
    """检查并安装缺少的依赖库"""
    
    dependencies = {
        "requests": "requests",
        "PyQt6.QtMultimedia": "PyQt6-Qt6",
    }
    
    missing_dependencies = []
    
    for module_name, package_name in dependencies.items():
        try:
            importlib.import_module(module_name)
            log(f"依赖库 {module_name} 已找到")
        except ImportError:
            log(f"依赖库 {module_name} 缺失，将尝试安装 {package_name}")
            missing_dependencies.append((module_name, package_name))
    
    if missing_dependencies:
        # 如果有缺失的依赖项，尝试安装
        try:
            for module_name, package_name in missing_dependencies:
                log(f"安装 {package_name}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
                log(f"{package_name} 安装成功")
                
            showInfo("番茄钟插件已安装所需依赖库，请重启Anki使其生效。")
            return False
        except Exception as e:
            error_msg = str(e)
            tb = traceback.format_exc()
            log(f"安装依赖库时出错: {error_msg}\n{tb}")
            showInfo(f"番茄钟插件无法自动安装所需依赖库。请手动运行以下命令:\n\n"
                     f"pip install {' '.join(p for _, p in missing_dependencies)}")
            return False
    
    return True


def show_config_dialog():
    """Creates and shows the configuration dialog."""
    dialog = ConfigDialog(mw)
    dialog.exec()


def setup_plugin():
    """Loads config, sets up hooks, and adds menu item."""
    log("Setting up Pomodoro Addon...")
    
    # 检查依赖项
    if not check_dependencies():
        return
    
    from .pomodoro import PomodoroTimer

    # 重置智能提醒状态
    from . import hooks
    hooks.do_not_remind_this_session = False
    hooks.review_start_time = None
    hooks.review_reminder_sent = False

    # Register hooks
    # Note: Use reviewer_will_start_review is often better than did_show_question
    # as it fires once per review session start. did_show_question fires per card.
    # Let's stick with did_show_question for now as per original code, but consider changing.
    gui_hooks.reviewer_did_show_question.append(on_reviewer_did_start)
    gui_hooks.state_did_change.append(on_state_did_change)

    # 创建计时器实例
    timer = get_pomodoro_timer()
    if timer is None or not isinstance(timer, PomodoroTimer):
        log("创建新的番茄钟计时器实例")
        timer = PomodoroTimer(mw)
        set_pomodoro_timer(timer)
        # 确保单例属性设置正确
        PomodoroTimer.instance = timer
    else:
        log(f"使用现有的番茄钟计时器实例: {timer}")
        # 确保单例属性设置正确
        PomodoroTimer.instance = timer
    
    # 设置定时检查打卡提醒
    setup_reminder_check()
    
    # 导入励志语录到数据库
    try:
        # 检查是否已经有语录数据
        storage = get_storage()
        yulu_file_path = os.path.join(os.path.dirname(__file__), "data", "yulu.txt")
        
        # 如果文件存在，尝试导入语录
        if os.path.exists(yulu_file_path):
            # 先检查是否已经有语录
            storage._init_db()  # 确保数据库初始化
            conn = sqlite3.connect(storage.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM inspiration_messages WHERE type = 'quote'")
            quote_count = cursor.fetchone()[0]
            conn.close()
            
            if quote_count == 0:
                # 如果还没有语录，导入文件
                log(f"开始导入语录文件: {yulu_file_path}")
                count = storage.import_quotes_from_file(yulu_file_path)
                log(f"成功导入 {count} 条语录")
                
                # 导入成功后，对文件进行保护处理
                if count > 0:
                    try:
                        # 生成一个随机的文件名和加密密钥
                        import random
                        import string
                        random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
                        key = random.randint(1, 255)  # 简单的XOR加密密钥
                        encrypted_file = os.path.join(os.path.dirname(__file__), "data", f".{random_name}.dat")
                        
                        # 读取原文件内容
                        with open(yulu_file_path, 'rb') as f:
                            content = f.read()
                        
                        # 对内容进行简单加密
                        encrypted_content = bytes([b ^ key for b in content])
                        
                        # 写入加密文件
                        with open(encrypted_file, 'wb') as f:
                            f.write(encrypted_content)
                        
                        # 删除原文件
                        os.remove(yulu_file_path)
                        log(f"语录文件已被加密保护: {encrypted_file}")
                        
                        # 将加密信息保存到数据库中
                        conn = sqlite3.connect(storage.db_path)
                        cursor = conn.cursor()
                        
                        # 保存加密文件路径和密钥
                        cursor.execute('''
                        INSERT OR REPLACE INTO settings (key, value)
                        VALUES ('encrypted_yulu_file', ?)
                        ''', (os.path.basename(encrypted_file),))
                        
                        cursor.execute('''
                        INSERT OR REPLACE INTO settings (key, value)
                        VALUES ('encrypted_yulu_key', ?)
                        ''', (str(key),))
                        
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        log(f"保护语录文件时出错: {str(e)}")
            else:
                log(f"数据库中已有 {quote_count} 条语录，跳过导入")
                
                # 如果原文件还存在，也进行保护
                if os.path.exists(yulu_file_path):
                    try:
                        # 生成一个随机的文件名和加密密钥
                        import random
                        import string
                        random_name = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
                        key = random.randint(1, 255)  # 简单的XOR加密密钥
                        encrypted_file = os.path.join(os.path.dirname(__file__), "data", f".{random_name}.dat")
                        
                        # 读取原文件内容
                        with open(yulu_file_path, 'rb') as f:
                            content = f.read()
                        
                        # 对内容进行简单加密
                        encrypted_content = bytes([b ^ key for b in content])
                        
                        # 写入加密文件
                        with open(encrypted_file, 'wb') as f:
                            f.write(encrypted_content)
                        
                        # 删除原文件
                        os.remove(yulu_file_path)
                        log(f"语录文件已被加密保护: {encrypted_file}")
                        
                        # 将加密信息保存到数据库中
                        conn = sqlite3.connect(storage.db_path)
                        cursor = conn.cursor()
                        
                        # 保存加密文件路径和密钥
                        cursor.execute('''
                        INSERT OR REPLACE INTO settings (key, value)
                        VALUES ('encrypted_yulu_file', ?)
                        ''', (os.path.basename(encrypted_file),))
                        
                        cursor.execute('''
                        INSERT OR REPLACE INTO settings (key, value)
                        VALUES ('encrypted_yulu_key', ?)
                        ''', (str(key),))
                        
                        conn.commit()
                        conn.close()
                    except Exception as e:
                        log(f"保护语录文件时出错: {str(e)}")
    except Exception as e:
        log(f"导入语录时出错: {str(e)}")
        traceback.print_exc()
    
    # 定义打开URL的函数
    def open_url(url):
        import webbrowser
        webbrowser.open(url)
    
    # 初始化状态栏显示
    config = get_config()
    if config.get("show_statusbar_timer", True) and config.get("enabled", True):
        def _show_timer():
            show_timer_in_statusbar(True)
        mw.progress.single_shot(500, _show_timer)
    
    # 创建顶级菜单"番茄钟"
    fanqie_menu = QMenu("番茄钟", mw)
    mw.form.menubar.addMenu(fanqie_menu)
    
    # 添加启用番茄钟选项
    enable_action = QAction("启用番茄钟", mw)
    enable_action.setCheckable(True)
    enable_action.setChecked(config.get("enabled", True))
    
    def toggle_enable():
        config = get_config()
        config["enabled"] = enable_action.isChecked()
        save_config()
        # 重新设置计时器显示
        show_timer_in_statusbar(config["enabled"] and config["show_statusbar_timer"])
        
    enable_action.triggered.connect(toggle_enable)
    fanqie_menu.addAction(enable_action)
    
    # 添加分隔线
    fanqie_menu.addSeparator()
    
    # 添加番茄钟统计菜单项
    stats_action = QAction("学习统计 📊", mw)
    stats_action.triggered.connect(show_statistics_dialog)
    fanqie_menu.addAction(stats_action)
    
    # 添加每日打卡菜单项
    checkin_action = QAction("每日打卡 📅", mw)
    checkin_action.triggered.connect(show_checkin_dialog)
    fanqie_menu.addAction(checkin_action)
    
    # 添加倒计时设置菜单项
    countdown_action = QAction("倒计时 ⏱️", mw)
    countdown_action.triggered.connect(show_countdown_dialog)
    fanqie_menu.addAction(countdown_action)
    
    # 添加自动播放音乐菜单项
    auto_play_music_action = QAction("自动播放音乐 🎵", mw)
    auto_play_music_action.setCheckable(True)
    auto_play_music_action.setChecked(config.get("auto_play_music", False))
    
    def toggle_auto_play_music():
        config = get_config()
        config["auto_play_music"] = auto_play_music_action.isChecked()
        save_config()
    
    auto_play_music_action.triggered.connect(toggle_auto_play_music)
    fanqie_menu.addAction(auto_play_music_action)
    
    # 添加环境噪音菜单项
    noise_menu = QMenu("环境噪音 🔊", mw)
    # 应用样式表，添加圆角和鼠标悬停效果
    noise_menu.setStyleSheet("""
        QMenu {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 5px;
            border: none;
            margin: 2px;
        }
        QMenu::item {
            padding: 5px 30px 5px 20px;
            border-radius: 6px;
            margin: 2px;
            background-color: transparent;
        }
        QMenu::item:selected {
            background-color: #f0f0f0;
            color: #333333;
        }
        QMenu::item:hover {
            background-color: #e6f7ff;
            border-radius: 6px;
            transition: background-color 0.3s;
        }
        QMenu::corner {
            background-color: transparent;
        }
        QMenu::separator {
            height: 1px;
            background-color: #eeeeee;
            margin: 4px 10px;
        }
        QMenu::indicator {
            width: 16px;
            height: 16px;
            border-radius: 4px;
            background-color: transparent;
        }
        QMenu::icon {
            padding-left: 8px;
        }
    """)
    
    # 添加泡泡白噪音选项
    ppbzy_action = QAction("泡泡白噪音", mw)
    ppbzy_action.triggered.connect(lambda: open_url("https://www.ppbzy.com/"))
    noise_menu.addAction(ppbzy_action)
    
    # 添加A Soft Murmur选项
    asoft_action = QAction("A Soft Murmur", mw)
    asoft_action.triggered.connect(lambda: open_url("https://asoftmurmur.com/"))
    noise_menu.addAction(asoft_action)
    
    # 添加Rainy Mood选项
    rainy_action = QAction("Rainy Mood", mw)
    rainy_action.triggered.connect(lambda: open_url("https://www.rainymood.com/"))
    noise_menu.addAction(rainy_action)
    
    # 将环境噪音菜单添加到主菜单
    fanqie_menu.addMenu(noise_menu)
    
    # 添加音效相关菜单项
    # 创建一个音效子菜单
    sound_menu = QMenu("音效 🔊", mw)
    # 应用样式表，添加圆角和鼠标悬停效果
    sound_menu.setStyleSheet("""
        QMenu {
            background-color: #ffffff;
            border-radius: 8px;
            padding: 5px;
            border: none;
            margin: 2px;
        }
        QMenu::item {
            padding: 5px 30px 5px 20px;
            border-radius: 6px;
            margin: 2px;
            background-color: transparent;
        }
        QMenu::item:selected {
            background-color: #f0f0f0;
            color: #333333;
        }
        QMenu::item:hover {
            background-color: #e6f7ff;
            border-radius: 6px;
            transition: background-color 0.3s;
        }
        QMenu::corner {
            background-color: transparent;
        }
        QMenu::separator {
            height: 1px;
            background-color: #eeeeee;
            margin: 4px 10px;
        }
        QMenu::indicator {
            width: 16px;
            height: 16px;
            border-radius: 4px;
            background-color: transparent;
        }
        QMenu::icon {
            padding-left: 8px;
        }
    """)
    
    # 当前音效设置
    current_sound_file = config.get("sound_effect_file", DEFAULT_SOUND_EFFECT_FILE)
    sound_effect_enabled = config.get("sound_effect_enabled", False)
    
    # 创建一个动作组，确保音效选项互斥
    sound_action_group = QActionGroup(mw)
    sound_action_group.setExclusive(True)
    
    # 添加"无音效"选项
    no_sound_action = QAction("无音效", mw)
    no_sound_action.setCheckable(True)
    no_sound_action.setChecked(not sound_effect_enabled)
    
    def select_no_sound():
        config = get_config()
        config["sound_effect_enabled"] = False
        save_config()
    
    no_sound_action.triggered.connect(select_no_sound)
    sound_menu.addAction(no_sound_action)
    sound_action_group.addAction(no_sound_action)
    
    # 添加分隔线
    sound_menu.addSeparator()
    
    # 为每个音效文件创建一个选项
    for sound_file in AVAILABLE_SOUND_EFFECTS:
        sound_file_action = QAction(sound_file, mw)
        sound_file_action.setCheckable(True)
        sound_file_action.setChecked(sound_effect_enabled and sound_file == current_sound_file)
        
        def make_select_sound_file(file_name):
            def select_sound_file():
                config = get_config()
                config["sound_effect_enabled"] = True
                config["sound_effect_file"] = file_name
                save_config()
                
                # 播放一下选中的音效作为预览
                try:
                    from .music_player import get_music_player
                    get_music_player().play_sound_effect(file_name)
                except Exception as e:
                    log(f"播放音效预览时出错: {e}")
            
            return select_sound_file
        
        sound_file_action.triggered.connect(make_select_sound_file(sound_file))
        sound_menu.addAction(sound_file_action)
        sound_action_group.addAction(sound_file_action)
    
    # 将音效菜单添加到主菜单
    fanqie_menu.addMenu(sound_menu)
    
    # 添加番茄钟设置菜单项
    settings_action = QAction("时长设置 ⚙️", mw)
    settings_action.triggered.connect(show_config_dialog)
    fanqie_menu.addAction(settings_action)
    
    # 添加快捷键
    def setup_shortcuts():
        # 添加启动快捷键Ctrl+P
        pomo_shortcut = QShortcut(QKeySequence("Ctrl+P"), mw)
        pomo_shortcut.activated.connect(start_pomodoro_manually)
        
        # 添加暂停/恢复快捷键Ctrl+Space
        toggle_shortcut = QShortcut(QKeySequence("Ctrl+Space"), mw)
        toggle_shortcut.activated.connect(toggle_pomodoro_timer)
        
        # 添加退出快捷键Ctrl+Shift+P
        exit_shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), mw)
        exit_shortcut.activated.connect(show_pomodoro_exit_dialog)
    
    mw.progress.single_shot(1000, setup_shortcuts)

    log("Pomodoro Addon setup complete.")


# --- 启动插件 ---
# This code runs when Anki loads the addon
if __name__ != "__main__":
    # 使用single_shot替代timer，避免内存泄漏
    mw.progress.single_shot(100, setup_plugin)  # Run once after 100ms delay

# 卸载时的清理工作
def unload_addon():
    cleanup_on_unload()

# 添加卸载钩子
if gui_hooks:
    gui_hooks.profile_will_close.append(unload_addon)

# 全局提醒检查计时器
reminder_timer = None

def setup_reminder_check():
    """设置定时检查打卡提醒"""
    from PyQt6.QtCore import QTimer
    from datetime import datetime
    from .storage import get_storage
    from .ui.reminder_dialog import show_reminder_dialog
    
    global reminder_timer
    
    # 创建定时器，每分钟检查一次
    if reminder_timer is None:
        reminder_timer = QTimer(mw)
        reminder_timer.timeout.connect(check_reminder)
        reminder_timer.start(60000)  # 60秒检查一次
    
    # 检查Anki启动时是否需要显示提醒（1分钟后）
    mw.progress.single_shot(60000, check_anki_startup_reminder)

def check_anki_startup_reminder():
    """检查Anki启动后的提醒"""
    from datetime import datetime
    from .storage import get_storage
    from .ui.reminder_dialog import show_reminder_dialog
    
    storage = get_storage()
    reminder = storage.get_reminder()
    
    if not reminder or not reminder['enabled']:
        return
    
    # 获取当前日期
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 检查是否已经提醒过
    if reminder['last_reminded_date'] == today:
        return
        
    # 标记今天已提醒
    storage.update_reminder_status(reminder['id'], today)
    
    # 显示提醒
    show_reminder_dialog()

def check_reminder():
    """检查是否到了提醒时间"""
    from datetime import datetime
    from .storage import get_storage
    from .ui.reminder_dialog import show_reminder_dialog
    
    storage = get_storage()
    reminder = storage.get_reminder()
    
    if not reminder or not reminder['enabled']:
        return
    
    # 获取当前时间和日期
    now = datetime.now()
    current_time = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")
    
    # 检查是否已经提醒过今天
    if reminder['last_reminded_date'] == today:
        return
    
    # 检查是否到了提醒时间
    if current_time >= reminder['reminder_time']:
        # 标记今天已提醒
        storage.update_reminder_status(reminder['id'], today)
        
        # 显示提醒
        show_reminder_dialog()
