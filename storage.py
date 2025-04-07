import json
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from aqt import mw

from .constants import log

# 获取Anki配置目录
def get_data_path() -> str:
    """获取数据存储路径"""
    try:
        # 获取Anki主配置目录
        anki_collection_path = os.path.dirname(mw.col.path)
        log(f"当前集合路径: {anki_collection_path}")
        
        # 首先尝试直接在当前用户配置下创建目录
        data_dir = os.path.join(anki_collection_path, "pomodoro_stats")
        
        # 如果目录不存在或无法访问，尝试在"账户 1"下查找
        if not os.path.exists(data_dir):
            anki_base_dir = os.path.dirname(anki_collection_path)
            log(f"尝试查找账户文件夹，基础目录: {anki_base_dir}")
            
            # 检查是否存在"账户 1"文件夹
            account_dir = os.path.join(anki_base_dir, "账户 1")
            if os.path.exists(account_dir):
                log(f"找到账户 1文件夹: {account_dir}")
                data_dir = os.path.join(account_dir, "pomodoro_stats")
            else:
                log(f"未找到账户 1文件夹，将使用默认路径")
        
        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.join(data_dir, "pomodoro_data.db")
        
        log(f"最终使用的数据库路径: {db_path}")
        return db_path
    except Exception as e:
        log(f"获取数据库路径出错: {str(e)}")
        # 返回一个默认路径
        default_dir = os.path.join(os.path.dirname(os.path.dirname(mw.col.path)), "账户 1", "pomodoro_stats")
        os.makedirs(default_dir, exist_ok=True)
        default_path = os.path.join(default_dir, "pomodoro_data.db")
        log(f"使用默认数据库路径: {default_path}")
        return default_path

class PomodoroStorage:
    def __init__(self):
        self.db_path = get_data_path()
        self._init_db()
        self._check_and_update_schema()
    
    def _init_db(self):
        """初始化数据库，创建所需表格"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建番茄钟记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pomodoro_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            duration INTEGER,
            actual_duration INTEGER,
            completed BOOLEAN DEFAULT 0,
            date TEXT
        )
        ''')
        
        # 创建暂停记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pause_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pomodoro_id INTEGER,
            pause_time TIMESTAMP NOT NULL,
            resume_time TIMESTAMP,
            FOREIGN KEY (pomodoro_id) REFERENCES pomodoro_sessions (id)
        )
        ''')
        
        # 创建休息时间记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rest_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            duration INTEGER,
            date TEXT
        )
        ''')
        
        # 创建牌组使用记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS deck_usage_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pomodoro_id INTEGER,
            deck_id TEXT,
            deck_name TEXT,
            parent_deck_id TEXT,
            parent_deck_name TEXT,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP,
            duration INTEGER,
            FOREIGN KEY (pomodoro_id) REFERENCES pomodoro_sessions (id)
        )
        ''')
        
        # 创建打卡任务表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkin_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            last_check_date TEXT,
            streak_days INTEGER DEFAULT 0,
            max_streak INTEGER DEFAULT 0,
            sort_order INTEGER DEFAULT 0
        )
        ''')
        
        # 创建打卡记录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkin_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            check_date TEXT NOT NULL,
            check_time TIMESTAMP NOT NULL,
            FOREIGN KEY (task_id) REFERENCES checkin_tasks (id),
            UNIQUE(task_id, check_date)
        )
        ''')
        
        # 创建打卡提醒表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkin_reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reminder_time TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP NOT NULL,
            last_reminded_date TEXT
        )
        ''')
        
        # 创建消息和语录表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS inspiration_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            type TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _check_and_update_schema(self):
        """检查并更新数据库架构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 判断打卡任务表是否存在
        cursor.execute('''
        SELECT name FROM sqlite_master WHERE type='table' AND name='checkin_tasks'
        ''')
        if not cursor.fetchone():
            cursor.execute('''
            CREATE TABLE checkin_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP,
                streak_days INTEGER DEFAULT 0,
                max_streak INTEGER DEFAULT 0,
                last_check_date TEXT,
                sort_order INTEGER DEFAULT 0,
                emoji TEXT DEFAULT '🍅'
            )
            ''')
        else:
            # 检查是否有sort_order列
            cursor.execute("PRAGMA table_info(checkin_tasks)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'sort_order' not in columns:
                cursor.execute('''
                ALTER TABLE checkin_tasks ADD COLUMN sort_order INTEGER DEFAULT 0
                ''')
                
            # 检查是否有emoji列
            if 'emoji' not in columns:
                cursor.execute('''
                ALTER TABLE checkin_tasks ADD COLUMN emoji TEXT DEFAULT '🍅'
                ''')
        
        # 判断打卡记录表是否存在
        cursor.execute('''
        SELECT name FROM sqlite_master WHERE type='table' AND name='checkin_records'
        ''')
        if not cursor.fetchone():
            cursor.execute('''
            CREATE TABLE checkin_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                check_date TEXT,
                check_time TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES checkin_tasks (id)
            )
            ''')
        
        # 判断打卡提醒表是否存在
        cursor.execute('''
        SELECT name FROM sqlite_master WHERE type='table' AND name='checkin_reminders'
        ''')
        if not cursor.fetchone():
            cursor.execute('''
            CREATE TABLE checkin_reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reminder_time TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP NOT NULL,
                last_reminded_date TEXT
            )
            ''')
        
        conn.commit()
        conn.close()
    
    def start_pomodoro(self, duration_minutes: int) -> int:
        """记录番茄钟开始，返回会话ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        cursor.execute('''
        INSERT INTO pomodoro_sessions (start_time, duration, date)
        VALUES (?, ?, ?)
        ''', (now, duration_minutes * 60, today))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return session_id
    
    def complete_pomodoro(self, session_id: int, actual_duration: int):
        """完成番茄钟会话"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        cursor.execute('''
        UPDATE pomodoro_sessions
        SET end_time = ?, actual_duration = ?, completed = 1
        WHERE id = ?
        ''', (now, actual_duration, session_id))
        
        conn.commit()
        conn.close()
    
    def abandon_pomodoro(self, session_id: int, actual_duration: int):
        """中途放弃番茄钟"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        cursor.execute('''
        UPDATE pomodoro_sessions
        SET end_time = ?, actual_duration = ?, completed = 0
        WHERE id = ?
        ''', (now, actual_duration, session_id))
        
        conn.commit()
        conn.close()
    
    def save_partial_pomodoro(self, session_id: int, actual_duration: int):
        """保存进行中番茄钟的已完成时长
        
        这个方法用于在用户关闭Anki时保存正在进行的番茄钟会话的已完成时长。
        会话被标记为"部分完成"，已经完成的时间会计入学习净时长统计。
        
        Args:
            session_id: 番茄钟会话ID
            actual_duration: 已经完成的时长（秒）
        """
        if session_id is None or actual_duration <= 0:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        # 将会话标记为部分完成（completed = 2），区别于正常完成（1）和放弃（0）
        # 并保存已完成的时长
        cursor.execute('''
        UPDATE pomodoro_sessions
        SET end_time = ?, actual_duration = ?, completed = 2
        WHERE id = ?
        ''', (now, actual_duration, session_id))
        
        conn.commit()
        conn.close()
        
        log(f"已保存部分完成的番茄钟会话: ID={session_id}, 时长={actual_duration}秒")
    
    def record_pause(self, session_id: int) -> int:
        """记录暂停事件，返回暂停记录ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        cursor.execute('''
        INSERT INTO pause_records (pomodoro_id, pause_time)
        VALUES (?, ?)
        ''', (session_id, now))
        
        pause_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return pause_id
    
    def record_resume(self, pause_id: int):
        """记录恢复计时事件"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        cursor.execute('''
        UPDATE pause_records
        SET resume_time = ?
        WHERE id = ?
        ''', (now, pause_id))
        
        conn.commit()
        conn.close()
    
    def start_rest(self) -> int:
        """记录休息开始，返回休息记录ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        
        cursor.execute('''
        INSERT INTO rest_records (start_time, date)
        VALUES (?, ?)
        ''', (now, today))
        
        rest_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return rest_id
    
    def end_rest(self, rest_id: int):
        """记录休息结束，计算持续时间"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        # 先获取开始时间
        cursor.execute('''
        SELECT start_time FROM rest_records WHERE id = ?
        ''', (rest_id,))
        
        result = cursor.fetchone()
        if result:
            start_time = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S.%f")
            duration_seconds = int((now - start_time).total_seconds())
            
            cursor.execute('''
            UPDATE rest_records
            SET end_time = ?, duration = ?
            WHERE id = ?
            ''', (now, duration_seconds, rest_id))
        
        conn.commit()
        conn.close()
    
    def start_deck_usage(self, session_id: int, deck_id: str, deck_name: str, 
                      parent_deck_id: str = None, parent_deck_name: str = None) -> int:
        """记录开始使用牌组，返回牌组使用记录ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        cursor.execute('''
        INSERT INTO deck_usage_records 
        (pomodoro_id, deck_id, deck_name, parent_deck_id, parent_deck_name, start_time)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (session_id, deck_id, deck_name, parent_deck_id, parent_deck_name, now))
        
        usage_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return usage_id
    
    def end_deck_usage(self, usage_id: int):
        """记录结束使用牌组，计算持续时间"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        # 先获取开始时间
        cursor.execute('''
        SELECT start_time FROM deck_usage_records WHERE id = ?
        ''', (usage_id,))
        
        result = cursor.fetchone()
        if result:
            start_time = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S.%f")
            duration_seconds = int((now - start_time).total_seconds())
            
            cursor.execute('''
            UPDATE deck_usage_records
            SET end_time = ?, duration = ?
            WHERE id = ?
            ''', (now, duration_seconds, usage_id))
        
        conn.commit()
        conn.close()
    
    def get_daily_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """获取指定日期的统计数据，不指定日期则获取今天的"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取学习总时长、完成数量、放弃数量
        cursor.execute('''
        SELECT 
            SUM(actual_duration) as total_study_time,
            SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed_count,
            SUM(CASE WHEN completed = 0 AND end_time IS NOT NULL THEN 1 ELSE 0 END) as abandoned_count,
            SUM(CASE WHEN completed = 2 THEN 1 ELSE 0 END) as partial_count
        FROM pomodoro_sessions
        WHERE date = ?
        ''', (date,))
        
        result = cursor.fetchone()
        total_study_time = result[0] or 0
        completed_count = result[1] or 0
        abandoned_count = result[2] or 0
        partial_count = result[3] or 0  # 部分完成的番茄数
        
        # 获取暂停次数和暂停总时长（番茄钟内暂停的时间）
        cursor.execute('''
        SELECT 
            COUNT(pr.id) as pause_count,
            SUM(julianday(pr.resume_time) - julianday(pr.pause_time)) * 86400 as total_pause_time
        FROM pause_records pr
        JOIN pomodoro_sessions ps ON pr.pomodoro_id = ps.id
        WHERE ps.date = ? AND pr.resume_time IS NOT NULL
        ''', (date,))
        
        result = cursor.fetchone()
        pause_count = result[0] or 0
        total_pause_time = int(result[1] or 0)  # 将浮点数转换为整数秒
        
        # 获取实际休息时间总和
        cursor.execute('''
        SELECT 
            COUNT(*) as rest_count,
            SUM(duration) as total_rest_time
        FROM rest_records
        WHERE date = ? AND end_time IS NOT NULL
        ''', (date,))
        
        result = cursor.fetchone()
        rest_count = result[0] or 0
        
        # 如果有休息记录，使用记录的休息时间；如果没有，使用旧的计算方式
        if rest_count > 0:
            total_rest_time = result[1] or 0
        else:
            # 旧的计算方式 - 计算番茄钟之间的休息时间
            cursor.execute('''
            SELECT start_time
            FROM pomodoro_sessions
            WHERE date = ?
            ORDER BY start_time
            ''', (date,))
            
            sessions = cursor.fetchall()
            total_rest_time = 0
            
            if len(sessions) > 1:
                # 按开始时间排序
                sessions.sort()
                
                # 计算相邻番茄钟之间的时间间隔
                for i in range(1, len(sessions)):
                    current_start = datetime.strptime(sessions[i][0], "%Y-%m-%d %H:%M:%S.%f")
                    prev_session_id = i - 1
                    
                    # 获取前一个番茄钟的结束时间
                    cursor.execute('''
                    SELECT end_time
                    FROM pomodoro_sessions
                    WHERE date = ? AND start_time = ?
                    ''', (date, sessions[prev_session_id][0]))
                    
                    prev_end_result = cursor.fetchone()
                    if prev_end_result and prev_end_result[0]:
                        prev_end = datetime.strptime(prev_end_result[0], "%Y-%m-%d %H:%M:%S.%f")
                        # 计算休息时间（当前番茄钟开始 - 上一个番茄钟结束）
                        rest_seconds = (current_start - prev_end).total_seconds()
                        # 限制最大休息时间为30分钟(1800秒)，避免长时间间隔被计入
                        if rest_seconds > 0:
                            total_rest_time += min(rest_seconds, 1800)
        
        # 获取每个小时的学习时长分布
        cursor.execute('''
        SELECT 
            strftime('%H', start_time) as hour, 
            SUM(actual_duration) as duration
        FROM pomodoro_sessions
        WHERE date = ?
        GROUP BY hour
        ORDER BY hour
        ''', (date,))
        
        hourly_distribution = {}
        for hour, duration in cursor.fetchall():
            # 确保duration不会是None
            hourly_distribution[f"{int(hour):02d}"] = duration if duration is not None else 0
        
        conn.close()
        
        # 计算净学习时长（不再从总学习时长中减去暂停时长）
        net_study_time = total_study_time
        
        return {
            "date": date,
            "total_study_time": total_study_time,
            "total_pause_time": total_pause_time,
            "total_rest_time": total_rest_time,
            "net_study_time": net_study_time,
            "completed_count": completed_count,
            "abandoned_count": abandoned_count,
            "partial_count": partial_count,
            "pause_count": pause_count,
            "hourly_distribution": hourly_distribution
        }
    
    def get_weekly_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """获取指定日期所在周的统计数据，不指定日期则获取本周的"""
        # 计算周的开始日期和结束日期
        if date is None:
            today = datetime.now()
        else:
            today = datetime.strptime(date, "%Y-%m-%d")
            
        # 计算本周的第一天（周一）和最后一天（周日）
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        
        # 格式化为日期字符串
        start_date = start_of_week.strftime("%Y-%m-%d")
        end_date = end_of_week.strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取周内学习总时长、完成数量、放弃数量
        cursor.execute('''
        SELECT 
            SUM(actual_duration) as total_study_time,
            SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed_count,
            SUM(CASE WHEN completed = 0 AND end_time IS NOT NULL THEN 1 ELSE 0 END) as abandoned_count,
            SUM(CASE WHEN completed = 2 THEN 1 ELSE 0 END) as partial_count
        FROM pomodoro_sessions
        WHERE date BETWEEN ? AND ?
        ''', (start_date, end_date))
        
        result = cursor.fetchone()
        total_study_time = result[0] or 0
        completed_count = result[1] or 0
        abandoned_count = result[2] or 0
        partial_count = result[3] or 0  # 部分完成的番茄数
        
        # 获取暂停次数和暂停总时长（番茄钟内暂停的时间）
        cursor.execute('''
        SELECT 
            COUNT(pr.id) as pause_count,
            SUM(julianday(pr.resume_time) - julianday(pr.pause_time)) * 86400 as total_pause_time
        FROM pause_records pr
        JOIN pomodoro_sessions ps ON pr.pomodoro_id = ps.id
        WHERE ps.date BETWEEN ? AND ? AND pr.resume_time IS NOT NULL
        ''', (start_date, end_date))
        
        result = cursor.fetchone()
        pause_count = result[0] or 0
        total_pause_time = int(result[1] or 0)  # 将浮点数转换为整数秒
        
        # 获取实际休息时间总和
        cursor.execute('''
        SELECT 
            COUNT(*) as rest_count,
            SUM(duration) as total_rest_time
        FROM rest_records
        WHERE date BETWEEN ? AND ? AND end_time IS NOT NULL
        ''', (start_date, end_date))
        
        result = cursor.fetchone()
        rest_count = result[0] or 0
        
        # 如果有休息记录，使用记录的休息时间；如果没有，使用旧的计算方式
        if rest_count > 0:
            total_rest_time = result[1] or 0
        else:
            # 旧的计算方式 - 计算番茄钟之间的休息时间
            cursor.execute('''
            SELECT start_time, end_time
            FROM pomodoro_sessions
            WHERE date BETWEEN ? AND ?
            ORDER BY start_time
            ''', (start_date, end_date))
            
            sessions = cursor.fetchall()
            total_rest_time = 0
            
            if len(sessions) > 1:
                # 计算相邻番茄钟之间的时间间隔
                for i in range(1, len(sessions)):
                    current_start = datetime.strptime(sessions[i][0], "%Y-%m-%d %H:%M:%S.%f")
                    prev_end = sessions[i-1][1]
                    
                    if prev_end:
                        prev_end = datetime.strptime(prev_end, "%Y-%m-%d %H:%M:%S.%f")
                        # 计算休息时间（当前番茄钟开始 - 上一个番茄钟结束）
                        rest_seconds = (current_start - prev_end).total_seconds()
                        # 限制最大休息时间为30分钟(1800秒)，避免长时间间隔被计入
                        if rest_seconds > 0:
                            total_rest_time += min(rest_seconds, 1800)
        
        # 获取每天的学习时长分布
        cursor.execute('''
        SELECT 
            date, 
            SUM(actual_duration) as duration
        FROM pomodoro_sessions
        WHERE date BETWEEN ? AND ?
        GROUP BY date
        ORDER BY date
        ''', (start_date, end_date))
        
        daily_distribution = {}
        for date, duration in cursor.fetchall():
            # 确保duration不会是None
            daily_distribution[date] = duration if duration is not None else 0
        
        conn.close()
        
        # 计算净学习时长（不再从总学习时长中减去暂停时长）
        net_study_time = total_study_time
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_study_time": total_study_time,
            "total_pause_time": total_pause_time,
            "total_rest_time": total_rest_time,
            "net_study_time": net_study_time,
            "completed_count": completed_count,
            "abandoned_count": abandoned_count,
            "partial_count": partial_count,
            "pause_count": pause_count,
            "daily_distribution": daily_distribution
        }
        
    def get_monthly_stats(self, month: Optional[str] = None) -> Dict[str, Any]:
        """获取指定月份的统计数据，格式为YYYY-MM，不指定则获取本月"""
        if month is None:
            month = datetime.now().strftime("%Y-%m")
            
        year, month_num = map(int, month.split('-'))
        
        # 获取当月的第一天和最后一天
        first_day = datetime(year, month_num, 1).strftime("%Y-%m-%d")
        
        # 获取下个月的第一天，然后减去一天，得到当月最后一天
        if month_num == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month_num + 1, 1) - timedelta(days=1)
        last_day = last_day.strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取本月学习总时长、完成数量、放弃数量
        cursor.execute('''
        SELECT 
            SUM(actual_duration) as total_study_time,
            SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed_count,
            SUM(CASE WHEN completed = 0 AND end_time IS NOT NULL THEN 1 ELSE 0 END) as abandoned_count,
            SUM(CASE WHEN completed = 2 THEN 1 ELSE 0 END) as partial_count
        FROM pomodoro_sessions
        WHERE date BETWEEN ? AND ?
        ''', (first_day, last_day))
        
        result = cursor.fetchone()
        total_study_time = result[0] or 0
        completed_count = result[1] or 0
        abandoned_count = result[2] or 0
        partial_count = result[3] or 0  # 部分完成的番茄数
        
        # 获取暂停次数和暂停总时长（番茄钟内暂停的时间）
        cursor.execute('''
        SELECT 
            COUNT(pr.id) as pause_count,
            SUM(julianday(pr.resume_time) - julianday(pr.pause_time)) * 86400 as total_pause_time
        FROM pause_records pr
        JOIN pomodoro_sessions ps ON pr.pomodoro_id = ps.id
        WHERE ps.date BETWEEN ? AND ? AND pr.resume_time IS NOT NULL
        ''', (first_day, last_day))
        
        result = cursor.fetchone()
        pause_count = result[0] or 0
        total_pause_time = int(result[1] or 0)  # 将浮点数转换为整数秒
        
        # 获取实际休息时间总和
        cursor.execute('''
        SELECT 
            COUNT(*) as rest_count,
            SUM(duration) as total_rest_time
        FROM rest_records
        WHERE date BETWEEN ? AND ? AND end_time IS NOT NULL
        ''', (first_day, last_day))
        
        result = cursor.fetchone()
        rest_count = result[0] or 0
        
        # 如果有休息记录，使用记录的休息时间；如果没有，使用旧的计算方式
        if rest_count > 0:
            total_rest_time = result[1] or 0
        else:
            # 旧的计算方式 - 计算每天的番茄钟之间的休息时间并汇总
            cursor.execute('''
            SELECT DISTINCT date FROM pomodoro_sessions WHERE date BETWEEN ? AND ? ORDER BY date
            ''', (first_day, last_day))
            
            dates = cursor.fetchall()
            total_rest_time = 0
            
            for date_row in dates:
                current_date = date_row[0]
                
                cursor.execute('''
                SELECT start_time, end_time
                FROM pomodoro_sessions
                WHERE date = ?
                ORDER BY start_time
                ''', (current_date,))
                
                sessions = cursor.fetchall()
                
                if len(sessions) > 1:
                    # 计算相邻番茄钟之间的时间间隔
                    for i in range(1, len(sessions)):
                        current_start = datetime.strptime(sessions[i][0], "%Y-%m-%d %H:%M:%S.%f")
                        prev_end = sessions[i-1][1]
                        
                        if prev_end:
                            prev_end = datetime.strptime(prev_end, "%Y-%m-%d %H:%M:%S.%f")
                            # 计算休息时间（当前番茄钟开始 - 上一个番茄钟结束）
                            rest_seconds = (current_start - prev_end).total_seconds()
                            # 限制最大休息时间为30分钟(1800秒)，避免长时间间隔被计入
                            if rest_seconds > 0:
                                total_rest_time += min(rest_seconds, 1800)
        
        # 获取每日分布
        cursor.execute('''
        SELECT 
            date, 
            SUM(actual_duration) as duration
        FROM pomodoro_sessions
        WHERE date BETWEEN ? AND ?
        GROUP BY date
        ORDER BY date
        ''', (first_day, last_day))
        
        daily_distribution = {}
        for date, duration in cursor.fetchall():
            # 确保duration不会是None
            daily_distribution[date] = duration if duration is not None else 0
        
        # 计算每周的学习时长分布
        # 获取该月包含的所有日期
        start_date = datetime(year, month_num, 1)
        end_date = datetime(year, month_num, 1)
        if month_num == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month_num + 1, 1) - timedelta(days=1)
        
        # 初始化周分布数据
        weekly_distribution = {}
        
        # 遍历每一天，按周分组
        current_date = start_date
        while current_date <= end_date:
            # 获取当前日期所在的周数（从1开始）
            week_of_month = (current_date.day - 1) // 7 + 1
            week_label = f"第{week_of_month}周"
            
            # 获取当前日期的学习时长
            date_str = current_date.strftime("%Y-%m-%d")
            study_duration = daily_distribution.get(date_str, 0)
            
            # 确保study_duration不会是None
            if study_duration is None:
                study_duration = 0
                
            # 累加到对应的周
            if week_label not in weekly_distribution:
                weekly_distribution[week_label] = 0
            weekly_distribution[week_label] += study_duration
            
            # 移动到下一天
            current_date += timedelta(days=1)
        
        conn.close()
        
        # 计算净学习时长（不再从总学习时长中减去暂停时长）
        net_study_time = total_study_time
        
        return {
            "month": month,
            "start_date": first_day,
            "end_date": last_day,
            "total_study_time": total_study_time,
            "total_pause_time": total_pause_time,
            "total_rest_time": total_rest_time,
            "net_study_time": net_study_time,
            "completed_count": completed_count,
            "abandoned_count": abandoned_count,
            "partial_count": partial_count,
            "pause_count": pause_count,
            "daily_distribution": daily_distribution,
            "weekly_distribution": weekly_distribution
        }
    
    def get_yearly_stats(self, year: Optional[int] = None) -> Dict[str, Any]:
        """获取指定年份的统计数据，不指定则获取本年"""
        if year is None:
            year = datetime.now().year
            
        # 获取当年的第一天和最后一天
        first_day = f"{year}-01-01"
        last_day = f"{year}-12-31"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取本年学习总时长、完成数量、放弃数量
        cursor.execute('''
        SELECT 
            SUM(actual_duration) as total_study_time,
            SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed_count,
            SUM(CASE WHEN completed = 0 AND end_time IS NOT NULL THEN 1 ELSE 0 END) as abandoned_count,
            SUM(CASE WHEN completed = 2 THEN 1 ELSE 0 END) as partial_count
        FROM pomodoro_sessions
        WHERE strftime('%Y', date) = ?
        ''', (str(year),))
        
        result = cursor.fetchone()
        total_study_time = result[0] or 0
        completed_count = result[1] or 0
        abandoned_count = result[2] or 0
        partial_count = result[3] or 0  # 部分完成的番茄数
        
        # 获取暂停次数和暂停总时长（番茄钟内暂停的时间）
        cursor.execute('''
        SELECT 
            COUNT(pr.id) as pause_count,
            SUM(julianday(pr.resume_time) - julianday(pr.pause_time)) * 86400 as total_pause_time
        FROM pause_records pr
        JOIN pomodoro_sessions ps ON pr.pomodoro_id = ps.id
        WHERE strftime('%Y', ps.date) = ? AND pr.resume_time IS NOT NULL
        ''', (str(year),))
        
        result = cursor.fetchone()
        pause_count = result[0] or 0
        total_pause_time = int(result[1] or 0)  # 将浮点数转换为整数秒
        
        # 获取实际休息时间总和
        cursor.execute('''
        SELECT 
            COUNT(*) as rest_count,
            SUM(duration) as total_rest_time
        FROM rest_records
        WHERE strftime('%Y', date) = ? AND end_time IS NOT NULL
        ''', (str(year),))
        
        result = cursor.fetchone()
        rest_count = result[0] or 0
        
        # 如果有休息记录，使用记录的休息时间；如果没有，使用旧的计算方式
        if rest_count > 0:
            total_rest_time = result[1] or 0
        else:
            # 旧的计算方式 - 计算年度休息时间 - 按月份分组计算
            cursor.execute('''
            SELECT DISTINCT strftime('%Y-%m', date) as month 
            FROM pomodoro_sessions 
            WHERE strftime('%Y', date) = ? 
            ORDER BY month
            ''', (str(year),))
            
            months = cursor.fetchall()
            total_rest_time = 0
            
            for month_row in months:
                month = month_row[0]
                year_num, month_num = map(int, month.split('-'))
                
                # 获取当月的第一天和最后一天
                month_first_day = datetime(year_num, month_num, 1).strftime("%Y-%m-%d")
                
                # 获取下个月的第一天，然后减去一天，得到当月最后一天
                if month_num == 12:
                    month_last_day = datetime(year_num + 1, 1, 1) - timedelta(days=1)
                else:
                    month_last_day = datetime(year_num, month_num + 1, 1) - timedelta(days=1)
                month_last_day = month_last_day.strftime("%Y-%m-%d")
                
                # 计算该月份每天的番茄钟之间的休息时间
                cursor.execute('''
                SELECT DISTINCT date FROM pomodoro_sessions 
                WHERE date BETWEEN ? AND ? 
                ORDER BY date
                ''', (month_first_day, month_last_day))
                
                dates = cursor.fetchall()
                
                for date_row in dates:
                    current_date = date_row[0]
                    
                    cursor.execute('''
                    SELECT start_time, end_time
                    FROM pomodoro_sessions
                    WHERE date = ?
                    ORDER BY start_time
                    ''', (current_date,))
                    
                    sessions = cursor.fetchall()
                    
                    if len(sessions) > 1:
                        # 计算相邻番茄钟之间的时间间隔
                        for i in range(1, len(sessions)):
                            current_start = datetime.strptime(sessions[i][0], "%Y-%m-%d %H:%M:%S.%f")
                            prev_end = sessions[i-1][1]
                            
                            if prev_end:
                                prev_end = datetime.strptime(prev_end, "%Y-%m-%d %H:%M:%S.%f")
                                # 计算休息时间（当前番茄钟开始 - 上一个番茄钟结束）
                                rest_seconds = (current_start - prev_end).total_seconds()
                                # 限制最大休息时间为30分钟(1800秒)，避免长时间间隔被计入
                                if rest_seconds > 0:
                                    total_rest_time += min(rest_seconds, 1800)
        
        # 获取每月的学习时长分布
        cursor.execute('''
        SELECT 
            strftime('%m', date) as month, 
            SUM(actual_duration) as duration
        FROM pomodoro_sessions
        WHERE strftime('%Y', date) = ?
        GROUP BY month
        ORDER BY month
        ''', (str(year),))
        
        monthly_distribution = {}
        for month, duration in cursor.fetchall():
            # 确保duration不会是None
            monthly_distribution[f"{int(month):02d}"] = duration if duration is not None else 0
        
        conn.close()
        
        # 计算净学习时长（不再从总学习时长中减去暂停时长）
        net_study_time = total_study_time
        
        return {
            "year": year,
            "total_study_time": total_study_time,
            "total_pause_time": total_pause_time,
            "total_rest_time": total_rest_time or 0,
            "net_study_time": net_study_time,
            "completed_count": completed_count,
            "abandoned_count": abandoned_count,
            "partial_count": partial_count,
            "pause_count": pause_count,
            "monthly_distribution": monthly_distribution
        }
    
    def get_deck_usage_stats(self, date: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """获取指定日期的牌组使用统计数据"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        log(f"获取牌组使用统计：日期={date}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取指定日期的牌组使用情况
        cursor.execute('''
        SELECT 
            dur.deck_id, 
            dur.deck_name, 
            dur.parent_deck_id,
            dur.parent_deck_name,
            SUM(dur.duration) as total_duration
        FROM deck_usage_records dur
        JOIN pomodoro_sessions ps ON dur.pomodoro_id = ps.id
        WHERE ps.date = ? AND dur.duration IS NOT NULL
        GROUP BY dur.deck_id
        ORDER BY total_duration DESC
        ''', (date,))
        
        results = cursor.fetchall()
        log(f"获取牌组使用统计：找到 {len(results)} 条牌组记录")
        
        # 构建牌组使用统计
        deck_stats = []
        for row in results:
            deck_stats.append({
                "deck_id": row[0],
                "deck_name": row[1],
                "parent_deck_id": row[2],
                "parent_deck_name": row[3],
                "duration": row[4]
            })
            log(f"牌组使用统计：牌组={row[1]}, 使用时长={row[4]}秒")
        
        # 统计顶级牌组数据
        cursor.execute('''
        SELECT 
            COALESCE(dur.parent_deck_id, dur.deck_id) as top_deck_id,
            COALESCE(dur.parent_deck_name, dur.deck_name) as top_deck_name,
            SUM(dur.duration) as total_duration
        FROM deck_usage_records dur
        JOIN pomodoro_sessions ps ON dur.pomodoro_id = ps.id
        WHERE ps.date = ? AND dur.duration IS NOT NULL
        GROUP BY top_deck_id
        ORDER BY total_duration DESC
        ''', (date,))
        
        results = cursor.fetchall()
        log(f"获取牌组使用统计：找到 {len(results)} 条顶级牌组记录")
        
        # 构建顶级牌组统计
        top_deck_stats = []
        for row in results:
            if row[0] == "0":  # 处于牌组界面，不属于任何牌组
                deck_name = "牌组管理界面"
            else:
                deck_name = row[1]
                
            top_deck_stats.append({
                "deck_id": row[0],
                "deck_name": deck_name,
                "duration": row[2]
            })
            log(f"顶级牌组统计：牌组={deck_name}, 使用时长={row[2]}秒")
        
        conn.close()
        
        return {
            "deck_stats": deck_stats,
            "top_deck_stats": top_deck_stats
        }
        
    def get_weekly_deck_usage_stats(self, date: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """获取指定周的牌组使用统计数据"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        # 转换为datetime对象
        day = datetime.strptime(date, "%Y-%m-%d")
        
        # 计算本周的开始日期（周一）和结束日期（周日）
        start_of_week = (day - timedelta(days=day.weekday())).strftime("%Y-%m-%d")
        end_of_week = (day + timedelta(days=6-day.weekday())).strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取本周的牌组使用情况
        cursor.execute('''
        SELECT 
            dur.deck_id, 
            dur.deck_name, 
            dur.parent_deck_id,
            dur.parent_deck_name,
            SUM(dur.duration) as total_duration
        FROM deck_usage_records dur
        JOIN pomodoro_sessions ps ON dur.pomodoro_id = ps.id
        WHERE ps.date BETWEEN ? AND ? AND dur.duration IS NOT NULL
        GROUP BY dur.deck_id
        ORDER BY total_duration DESC
        ''', (start_of_week, end_of_week))
        
        results = cursor.fetchall()
        
        # 构建牌组使用统计
        deck_stats = []
        for row in results:
            deck_stats.append({
                "deck_id": row[0],
                "deck_name": row[1],
                "parent_deck_id": row[2],
                "parent_deck_name": row[3],
                "duration": row[4]
            })
        
        # 统计顶级牌组数据
        cursor.execute('''
        SELECT 
            COALESCE(dur.parent_deck_id, dur.deck_id) as top_deck_id,
            COALESCE(dur.parent_deck_name, dur.deck_name) as top_deck_name,
            SUM(dur.duration) as total_duration
        FROM deck_usage_records dur
        JOIN pomodoro_sessions ps ON dur.pomodoro_id = ps.id
        WHERE ps.date BETWEEN ? AND ? AND dur.duration IS NOT NULL
        GROUP BY top_deck_id
        ORDER BY total_duration DESC
        ''', (start_of_week, end_of_week))
        
        results = cursor.fetchall()
        
        # 构建顶级牌组统计
        top_deck_stats = []
        for row in results:
            if row[0] == "0":  # 处于牌组界面，不属于任何牌组
                deck_name = "牌组管理界面"
            else:
                deck_name = row[1]
                
            top_deck_stats.append({
                "deck_id": row[0],
                "deck_name": deck_name,
                "duration": row[2]
            })
        
        conn.close()
        
        return {
            "deck_stats": deck_stats,
            "top_deck_stats": top_deck_stats
        }
        
    def get_monthly_deck_usage_stats(self, month: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """获取指定月份的牌组使用统计数据，格式为YYYY-MM"""
        if month is None:
            month = datetime.now().strftime("%Y-%m")
            
        year, month_num = map(int, month.split('-'))
        
        # 获取当月的第一天和最后一天
        first_day = datetime(year, month_num, 1).strftime("%Y-%m-%d")
        
        # 获取下个月的第一天，然后减去一天，得到当月最后一天
        if month_num == 12:
            last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = datetime(year, month_num + 1, 1) - timedelta(days=1)
        last_day = last_day.strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取本月的牌组使用情况
        cursor.execute('''
        SELECT 
            dur.deck_id, 
            dur.deck_name, 
            dur.parent_deck_id,
            dur.parent_deck_name,
            SUM(dur.duration) as total_duration
        FROM deck_usage_records dur
        JOIN pomodoro_sessions ps ON dur.pomodoro_id = ps.id
        WHERE ps.date BETWEEN ? AND ? AND dur.duration IS NOT NULL
        GROUP BY dur.deck_id
        ORDER BY total_duration DESC
        ''', (first_day, last_day))
        
        results = cursor.fetchall()
        
        # 构建牌组使用统计
        deck_stats = []
        for row in results:
            deck_stats.append({
                "deck_id": row[0],
                "deck_name": row[1],
                "parent_deck_id": row[2],
                "parent_deck_name": row[3],
                "duration": row[4]
            })
        
        # 统计顶级牌组数据
        cursor.execute('''
        SELECT 
            COALESCE(dur.parent_deck_id, dur.deck_id) as top_deck_id,
            COALESCE(dur.parent_deck_name, dur.deck_name) as top_deck_name,
            SUM(dur.duration) as total_duration
        FROM deck_usage_records dur
        JOIN pomodoro_sessions ps ON dur.pomodoro_id = ps.id
        WHERE ps.date BETWEEN ? AND ? AND dur.duration IS NOT NULL
        GROUP BY top_deck_id
        ORDER BY total_duration DESC
        ''', (first_day, last_day))
        
        results = cursor.fetchall()
        
        # 构建顶级牌组统计
        top_deck_stats = []
        for row in results:
            if row[0] == "0":  # 处于牌组界面，不属于任何牌组
                deck_name = "牌组管理界面"
            else:
                deck_name = row[1]
                
            top_deck_stats.append({
                "deck_id": row[0],
                "deck_name": deck_name,
                "duration": row[2]
            })
        
        conn.close()
        
        return {
            "deck_stats": deck_stats,
            "top_deck_stats": top_deck_stats
        }
        
    def get_yearly_deck_usage_stats(self, year: Optional[int] = None) -> Dict[str, List[Dict[str, Any]]]:
        """获取指定年份的牌组使用统计数据"""
        if year is None:
            year = datetime.now().year
            
        # 获取当年的第一天和最后一天
        first_day = f"{year}-01-01"
        last_day = f"{year}-12-31"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取本年的牌组使用情况
        cursor.execute('''
        SELECT 
            dur.deck_id, 
            dur.deck_name, 
            dur.parent_deck_id,
            dur.parent_deck_name,
            SUM(dur.duration) as total_duration
        FROM deck_usage_records dur
        JOIN pomodoro_sessions ps ON dur.pomodoro_id = ps.id
        WHERE strftime('%Y', ps.date) = ? AND dur.duration IS NOT NULL
        GROUP BY dur.deck_id
        ORDER BY total_duration DESC
        ''', (str(year),))
        
        results = cursor.fetchall()
        
        # 构建牌组使用统计
        deck_stats = []
        for row in results:
            deck_stats.append({
                "deck_id": row[0],
                "deck_name": row[1],
                "parent_deck_id": row[2],
                "parent_deck_name": row[3],
                "duration": row[4]
            })
        
        # 统计顶级牌组数据
        cursor.execute('''
        SELECT 
            COALESCE(dur.parent_deck_id, dur.deck_id) as top_deck_id,
            COALESCE(dur.parent_deck_name, dur.deck_name) as top_deck_name,
            SUM(dur.duration) as total_duration
        FROM deck_usage_records dur
        JOIN pomodoro_sessions ps ON dur.pomodoro_id = ps.id
        WHERE strftime('%Y', ps.date) = ? AND dur.duration IS NOT NULL
        GROUP BY top_deck_id
        ORDER BY total_duration DESC
        ''', (str(year),))
        
        results = cursor.fetchall()
        
        # 构建顶级牌组统计
        top_deck_stats = []
        for row in results:
            if row[0] == "0":  # 处于牌组界面，不属于任何牌组
                deck_name = "牌组管理界面"
            else:
                deck_name = row[1]
                
            top_deck_stats.append({
                "deck_id": row[0],
                "deck_name": deck_name,
                "duration": row[2]
            })
        
        conn.close()
        
        return {
            "deck_stats": deck_stats,
            "top_deck_stats": top_deck_stats
        }

    def clear_all_data(self) -> bool:
        """清空所有统计数据
        
        清空所有番茄钟相关的统计数据表，包括会话记录、暂停记录、休息记录和牌组使用记录
        
        Returns:
            bool: 操作是否成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 清空所有表
            cursor.execute("DELETE FROM pomodoro_sessions")
            cursor.execute("DELETE FROM pause_records")
            cursor.execute("DELETE FROM rest_records")
            cursor.execute("DELETE FROM deck_usage_records")
            
            # 重置自增ID
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='pomodoro_sessions'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='pause_records'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='rest_records'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='deck_usage_records'")
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            log(f"清空数据出错: {str(e)}")
            return False

    def get_checkin_tasks(self) -> List[Dict[str, Any]]:
        """获取所有打卡任务
        
        Returns:
            打卡任务列表，每个任务包含id、name、streak_days、max_streak和checked_today信息
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # 先尝试使用sort_order排序
            cursor.execute('''
            SELECT t.id, t.name, t.streak_days, t.max_streak, t.last_check_date, t.emoji
            FROM checkin_tasks t
            ORDER BY t.sort_order, t.name
            ''')
        except sqlite3.OperationalError:
            # 如果sort_order不存在，只按名称排序
            log("回退到仅按名称排序任务")
            cursor.execute('''
            SELECT t.id, t.name, t.streak_days, t.max_streak, t.last_check_date, 
                   COALESCE(t.emoji, '🍅') as emoji
            FROM checkin_tasks t
            ORDER BY t.name
            ''')
        
        tasks = []
        for row in cursor.fetchall():
            task_id, name, streak_days, max_streak, last_check_date, emoji = row
            checked_today = (last_check_date == today)
            
            tasks.append({
                'id': task_id,
                'name': name,
                'streak_days': streak_days,
                'max_streak': max_streak,
                'checked_today': checked_today,
                'emoji': emoji or '🍅'  # 确保emoji字段有值
            })
        
        conn.close()
        return tasks
    
    def get_checkin_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取单个打卡任务的详情
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务详情字典，如果任务不存在则返回None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            cursor.execute('''
            SELECT id, name, streak_days, max_streak, last_check_date, COALESCE(emoji, '🍅') as emoji
            FROM checkin_tasks
            WHERE id = ?
            ''', (task_id,))
            
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
                
            task_id, name, streak_days, max_streak, last_check_date, emoji = row
            checked_today = (last_check_date == today)
            
            task = {
                'id': task_id,
                'name': name,
                'streak_days': streak_days,
                'max_streak': max_streak,
                'checked_today': checked_today,
                'emoji': emoji
            }
            
            conn.close()
            return task
        except Exception as e:
            log(f"获取打卡任务详情失败: {e}")
            conn.close()
            return None
    
    def add_checkin_task(self, task_name: str, emoji: str = '🍅') -> int:
        """添加新的打卡任务
        
        Args:
            task_name: 任务名称
            emoji: 任务图标
            
        Returns:
            新任务的ID，失败则返回None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        try:
            # 获取当前最大的排序值
            cursor.execute('''
            SELECT MAX(sort_order) FROM checkin_tasks
            ''')
            
            result = cursor.fetchone()
            next_order = 0 if result[0] is None else result[0] + 1
            
            # 检查是否支持emoji字段
            cursor.execute("PRAGMA table_info(checkin_tasks)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'emoji' in columns:
                cursor.execute('''
                INSERT INTO checkin_tasks (name, created_at, streak_days, max_streak, sort_order, emoji)
                VALUES (?, ?, 0, 0, ?, ?)
                ''', (task_name, now, next_order, emoji))
            else:
                cursor.execute('''
                INSERT INTO checkin_tasks (name, created_at, streak_days, max_streak, sort_order)
                VALUES (?, ?, 0, 0, ?)
                ''', (task_name, now, next_order))
            
            task_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return task_id
        except Exception as e:
            log(f"添加打卡任务失败: {e}")
            conn.rollback()
            conn.close()
            return None
    
    def delete_checkin_task(self, task_id: int) -> bool:
        """删除打卡任务及其所有打卡记录
        
        Args:
            task_id: 任务ID
            
        Returns:
            操作是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 首先删除所有关联的打卡记录
            cursor.execute('''
            DELETE FROM checkin_records
            WHERE task_id = ?
            ''', (task_id,))
            
            # 然后删除任务
            cursor.execute('''
            DELETE FROM checkin_tasks
            WHERE id = ?
            ''', (task_id,))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            log(f"删除打卡任务失败: {e}")
            conn.rollback()
            conn.close()
            return False
    
    def rename_checkin_task(self, task_id: int, new_name: str, new_emoji: str = None) -> bool:
        """重命名打卡任务
        
        Args:
            task_id: 任务ID
            new_name: 新的任务名称
            new_emoji: 新的任务图标
            
        Returns:
            操作是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 检查是否支持emoji字段
            cursor.execute("PRAGMA table_info(checkin_tasks)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'emoji' in columns and new_emoji is not None:
                cursor.execute('''
                UPDATE checkin_tasks
                SET name = ?, emoji = ?
                WHERE id = ?
                ''', (new_name, new_emoji, task_id))
            else:
                cursor.execute('''
                UPDATE checkin_tasks
                SET name = ?
                WHERE id = ?
                ''', (new_name, task_id))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            log(f"重命名打卡任务失败: {e}")
            conn.rollback()
            conn.close()
            return False
    
    def check_in_task(self, task_id: int) -> Tuple[bool, int]:
        """为任务打卡
        
        Args:
            task_id: 任务ID
            
        Returns:
            成功与否，以及更新后的连续打卡天数
        """
        conn = sqlite3.connect(self.db_path)
        
        try:
            cursor = conn.cursor()
            
            today = datetime.now().strftime("%Y-%m-%d")
            now = datetime.now()
            
            # 检查今天是否已经打卡
            cursor.execute('''
            SELECT id FROM checkin_records
            WHERE task_id = ? AND check_date = ?
            ''', (task_id, today))
            
            if cursor.fetchone():
                # 今天已经打卡过了，返回当前连续天数
                cursor.execute('''
                SELECT streak_days FROM checkin_tasks
                WHERE id = ?
                ''', (task_id,))
                streak_days = cursor.fetchone()[0]
                conn.close()
                return False, streak_days
            
            # 添加新的打卡记录
            cursor.execute('''
            INSERT INTO checkin_records (task_id, check_date, check_time)
            VALUES (?, ?, ?)
            ''', (task_id, today, now))
            
            # 获取所有打卡记录，重新计算连续打卡天数（与补打卡使用相同的逻辑）
            cursor.execute('''
            SELECT check_date
            FROM checkin_records
            WHERE task_id = ?
            ORDER BY check_date
            ''', (task_id,))
            
            dates = [datetime.strptime(row[0], '%Y-%m-%d').date() for row in cursor.fetchall()]
            
            # 计算当前的连续打卡天数
            streak_days = self._calculate_current_streak(dates, datetime.strptime(today, '%Y-%m-%d').date())
            
            # 计算历史最长连续打卡
            max_streak = self._calculate_max_streak(dates)
            
            # 更新任务信息
            cursor.execute('''
            UPDATE checkin_tasks
            SET last_check_date = ?, streak_days = ?, max_streak = ?
            WHERE id = ?
            ''', (today, streak_days, max_streak, task_id))
            
            conn.commit()
            conn.close()
            
            return True, streak_days
        except Exception as e:
            log(f"打卡失败: {e}")
            try:
                conn.rollback()
            except Exception as e:
                log(f"回滚失败: {e}")
            
            try:
                conn.close()
            except Exception as e:
                log(f"关闭连接失败: {e}")
                
            return False, 0
    
    def makeup_checkin(self, task_id: int, check_date: str) -> Tuple[bool, int]:
        """为过去日期补打卡
        
        Args:
            task_id: 任务ID
            check_date: 需要补打卡的日期，格式为YYYY-MM-DD
            
        Returns:
            成功与否，以及更新后的连续打卡天数
        """
        conn = sqlite3.connect(self.db_path)
        
        try:
            cursor = conn.cursor()
            
            now = datetime.now()
            today = now.strftime("%Y-%m-%d")
            
            # 检查日期是否合法（不能是未来日期）
            if check_date > today:
                log(f"不能为未来日期打卡: {check_date}")
                conn.close()
                return False, 0
            
            # 检查是否已经有打卡记录
            cursor.execute('''
            SELECT id FROM checkin_records
            WHERE task_id = ? AND check_date = ?
            ''', (task_id, check_date))
            
            if cursor.fetchone():
                # 该日期已经有打卡记录，获取当前连续天数后返回
                log(f"该日期已经打卡: {check_date}")
                cursor.execute('''
                SELECT streak_days FROM checkin_tasks
                WHERE id = ?
                ''', (task_id,))
                streak_days = cursor.fetchone()[0]
                conn.close()
                return False, streak_days
            
            # 添加补打卡记录
            cursor.execute('''
            INSERT INTO checkin_records (task_id, check_date, check_time)
            VALUES (?, ?, ?)
            ''', (task_id, check_date, now))
            
            # 获取所有打卡记录，重新计算连续打卡天数
            cursor.execute('''
            SELECT check_date
            FROM checkin_records
            WHERE task_id = ?
            ORDER BY check_date
            ''', (task_id,))
            
            dates = [datetime.strptime(row[0], '%Y-%m-%d').date() for row in cursor.fetchall()]
            
            # 计算当前的连续打卡天数
            streak_days = self._calculate_current_streak(dates, datetime.strptime(today, '%Y-%m-%d').date())
            
            # 计算历史最长连续打卡
            max_streak = self._calculate_max_streak(dates)
            
            # 更新任务信息
            cursor.execute('''
            UPDATE checkin_tasks
            SET streak_days = ?, max_streak = ?
            WHERE id = ?
            ''', (streak_days, max_streak, task_id))
            
            conn.commit()
            conn.close()
            
            return True, streak_days
        except Exception as e:
            log(f"补打卡失败: {e}")
            try:
                conn.rollback()
            except Exception as e:
                log(f"回滚失败: {e}")
            
            try:
                conn.close()
            except Exception as e:
                log(f"关闭连接失败: {e}")
                
            return False, 0
    
    def _calculate_current_streak(self, dates, today):
        """计算当前连续打卡天数
        
        Args:
            dates: 所有打卡日期的列表
            today: 今天的日期
            
        Returns:
            当前连续打卡天数
        """
        if not dates:
            return 0
        
        # 确保日期已排序
        dates = sorted(dates)
        
        # 检查最后一个打卡日期
        last_date = dates[-1]
        
        # 如果最后一次打卡不是今天也不是昨天，连续打卡中断
        if last_date != today and (today - last_date).days > 1:
            return 0
        
        # 从最后一个日期往前数，计算连续天数
        streak = 1
        for i in range(len(dates) - 1, 0, -1):
            # 如果日期是连续的（前一天）
            if (dates[i] - dates[i-1]).days == 1:
                streak += 1
            else:
                break
                
        return streak
    
    def _calculate_max_streak(self, dates):
        """计算历史最长连续打卡天数
        
        Args:
            dates: 所有打卡日期的列表
            
        Returns:
            历史最长连续打卡天数
        """
        if not dates:
            return 0
        
        # 确保日期已排序
        dates = sorted(dates)
        
        max_streak = 1
        current_streak = 1
        
        for i in range(1, len(dates)):
            # 如果日期是连续的（前一天）
            if (dates[i] - dates[i-1]).days == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            # 如果日期相同（重复记录）
            elif (dates[i] - dates[i-1]).days == 0:
                continue
            # 如果日期不连续，重置计数
            else:
                current_streak = 1
                
        return max_streak
    
    def cancel_checkin(self, task_id: int) -> Tuple[bool, int]:
        """取消今日打卡
        
        Args:
            task_id: 任务ID
            
        Returns:
            成功与否，以及更新后的连续打卡天数
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # 检查今天是否有打卡记录
            cursor.execute('''
            SELECT id FROM checkin_records
            WHERE task_id = ? AND check_date = ?
            ''', (task_id, today))
            
            if not cursor.fetchone():
                conn.close()
                return False, 0
            
            # 删除今天的打卡记录
            cursor.execute('''
            DELETE FROM checkin_records
            WHERE task_id = ? AND check_date = ?
            ''', (task_id, today))
            
            # 查找上一次打卡的日期
            cursor.execute('''
            SELECT check_date FROM checkin_records
            WHERE task_id = ?
            ORDER BY check_date DESC
            LIMIT 1
            ''', (task_id,))
            
            row = cursor.fetchone()
            last_check_date = row[0] if row else None
            
            # 重新计算连续打卡天数
            new_streak = 0
            
            if last_check_date:
                # 获取昨天的日期
                yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                
                # 如果上次打卡是昨天，连续天数保持不变
                if last_check_date == yesterday:
                    cursor.execute('''
                    SELECT streak_days FROM checkin_tasks
                    WHERE id = ?
                    ''', (task_id,))
                    current_streak = cursor.fetchone()[0]
                    new_streak = max(0, current_streak - 1)  # 减去今天的1次
                else:
                    # 如果上次打卡不是昨天，计算从上次打卡到昨天的连续天数
                    # 需要复杂的逻辑，这里简化处理，直接查询最近连续的记录
                    last_date = datetime.strptime(last_check_date, '%Y-%m-%d').date()
                    count = 1
                    
                    # 从上次打卡日期往前查找连续的记录
                    current_date = last_date
                    while True:
                        prev_date = current_date - timedelta(days=1)
                        prev_date_str = prev_date.strftime("%Y-%m-%d")
                        
                        cursor.execute('''
                        SELECT id FROM checkin_records
                        WHERE task_id = ? AND check_date = ?
                        ''', (task_id, prev_date_str))
                        
                        if not cursor.fetchone():
                            break
                        
                        count += 1
                        current_date = prev_date
                    
                    new_streak = count
            
            # 更新任务信息
            cursor.execute('''
            UPDATE checkin_tasks
            SET last_check_date = ?, streak_days = ?
            WHERE id = ?
            ''', (last_check_date, new_streak, task_id))
            
            conn.commit()
            conn.close()
            
            return True, new_streak
        except Exception as e:
            log(f"取消打卡失败: {e}")
            conn.rollback()
            conn.close()
            return False, 0
    
    def cancel_date_checkin(self, task_id: int, check_date: str) -> Tuple[bool, int]:
        """取消指定日期的打卡记录
        
        Args:
            task_id: 任务ID
            check_date: 需要取消打卡的日期，格式为YYYY-MM-DD
            
        Returns:
            成功与否，以及更新后的连续打卡天数
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # 如果是今天的打卡，使用cancel_checkin方法
            if check_date == today:
                conn.close()
                return self.cancel_checkin(task_id)
            
            # 检查指定日期是否有打卡记录
            cursor.execute('''
            SELECT id FROM checkin_records
            WHERE task_id = ? AND check_date = ?
            ''', (task_id, check_date))
            
            if not cursor.fetchone():
                conn.close()
                log(f"该日期没有打卡记录: {check_date}")
                return False, 0
            
            # 删除指定日期的打卡记录
            cursor.execute('''
            DELETE FROM checkin_records
            WHERE task_id = ? AND check_date = ?
            ''', (task_id, check_date))
            
            # 获取所有打卡记录，重新计算连续打卡天数
            cursor.execute('''
            SELECT check_date
            FROM checkin_records
            WHERE task_id = ?
            ORDER BY check_date
            ''', (task_id,))
            
            dates = [datetime.strptime(row[0], '%Y-%m-%d').date() for row in cursor.fetchall()]
            
            # 如果没有记录了，重置任务状态
            if not dates:
                cursor.execute('''
                UPDATE checkin_tasks
                SET last_check_date = NULL, streak_days = 0, max_streak = 0
                WHERE id = ?
                ''', (task_id,))
                
                conn.commit()
                conn.close()
                return True, 0
            
            # 获取最新的打卡日期
            last_check_date = dates[-1].strftime("%Y-%m-%d")
            
            # 计算当前的连续打卡天数
            streak_days = self._calculate_current_streak(dates, datetime.strptime(today, '%Y-%m-%d').date())
            
            # 计算历史最长连续打卡
            max_streak = self._calculate_max_streak(dates)
            
            # 更新任务信息
            cursor.execute('''
            UPDATE checkin_tasks
            SET last_check_date = ?, streak_days = ?, max_streak = ?
            WHERE id = ?
            ''', (last_check_date, streak_days, max_streak, task_id))
            
            conn.commit()
            conn.close()
            
            return True, streak_days
        except Exception as e:
            log(f"取消指定日期打卡失败: {e}")
            conn.rollback()
            conn.close()
            return False, 0
    
    def get_task_checkin_history(self, task_id: int) -> Dict[str, Any]:
        """获取任务的打卡历史
        
        Args:
            task_id: 任务ID
            
        Returns:
            包含打卡信息的字典，包括 streak_days, max_streak, total_days, 
            以及 check_history (日期到布尔值的映射，表示该日期是否打卡)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 获取任务基本信息
            cursor.execute('''
            SELECT name, streak_days, max_streak, last_check_date
            FROM checkin_tasks
            WHERE id = ?
            ''', (task_id,))
            
            row = cursor.fetchone()
            if not row:
                conn.close()
                return None
            
            name, streak_days, max_streak, last_check_date = row
            
            # 获取打卡记录
            cursor.execute('''
            SELECT check_date
            FROM checkin_records
            WHERE task_id = ?
            ORDER BY check_date
            ''', (task_id,))
            
            check_dates = [row[0] for row in cursor.fetchall()]
            total_days = len(check_dates)
            
            # 创建打卡历史记录字典
            check_history = {date: True for date in check_dates}
            
            conn.close()
            
            return {
                'name': name,
                'streak_days': streak_days,
                'max_streak': max_streak,
                'total_days': total_days,
                'last_check_date': last_check_date,
                'check_history': check_history
            }
        except Exception as e:
            log(f"获取打卡历史失败: {e}")
            conn.close()
            return None

    def update_tasks_order(self, task_ids: List[int]) -> bool:
        """更新任务排序顺序
        
        Args:
            task_ids: 排序后的任务ID列表
            
        Returns:
            操作是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # 为每个任务设置新的排序值
            for order, task_id in enumerate(task_ids):
                cursor.execute('''
                UPDATE checkin_tasks
                SET sort_order = ?
                WHERE id = ?
                ''', (order, task_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            log(f"更新任务顺序失败: {e}")
            conn.rollback()
            conn.close()
            return False

    def save_reminder(self, reminder_time: str) -> int:
        """保存打卡提醒时间
        
        Args:
            reminder_time: 提醒时间，格式为 HH:MM
            
        Returns:
            新提醒的ID，失败则返回None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        try:
            # 首先检查是否已经存在提醒，如果存在则更新
            cursor.execute('''
            SELECT id FROM checkin_reminders
            ''')
            
            existing_reminder = cursor.fetchone()
            
            if existing_reminder:
                cursor.execute('''
                UPDATE checkin_reminders
                SET reminder_time = ?, enabled = 1
                WHERE id = ?
                ''', (reminder_time, existing_reminder[0]))
                reminder_id = existing_reminder[0]
            else:
                cursor.execute('''
                INSERT INTO checkin_reminders (reminder_time, enabled, created_at)
                VALUES (?, 1, ?)
                ''', (reminder_time, now))
                reminder_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return reminder_id
        except Exception as e:
            log(f"保存打卡提醒失败: {e}")
            conn.rollback()
            conn.close()
            return None
    
    def get_reminder(self) -> dict:
        """获取打卡提醒设置
        
        Returns:
            包含提醒设置的字典，如果没有设置则返回None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, reminder_time, enabled, last_reminded_date
        FROM checkin_reminders
        LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'id': result[0],
                'reminder_time': result[1],
                'enabled': result[2] == 1,
                'last_reminded_date': result[3]
            }
        else:
            return None
    
    def disable_reminder(self, reminder_id: int) -> bool:
        """禁用打卡提醒
        
        Args:
            reminder_id: 提醒ID
            
        Returns:
            操作是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE checkin_reminders
            SET enabled = 0
            WHERE id = ?
            ''', (reminder_id,))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            log(f"禁用打卡提醒失败: {e}")
            conn.rollback()
            conn.close()
            return False
    
    def update_reminder_status(self, reminder_id: int, reminded_date: str) -> bool:
        """更新提醒状态，记录最后提醒日期
        
        Args:
            reminder_id: 提醒ID
            reminded_date: 提醒日期，格式为YYYY-MM-DD
            
        Returns:
            操作是否成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            UPDATE checkin_reminders
            SET last_reminded_date = ?
            WHERE id = ?
            ''', (reminded_date, reminder_id))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            log(f"更新提醒状态失败: {e}")
            conn.rollback()
            conn.close()
            return False

    def get_completed_pomodoros_since(self, start_timestamp, date_str=None):
        """获取从指定时间点以来已完成的番茄钟数量
        
        Args:
            start_timestamp: Anki启动时间的时间戳
            date_str: 日期字符串 (YYYY-MM-DD)，若提供则只统计该日期的记录
            
        Returns:
            已完成的番茄钟数量
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            query = '''
            SELECT COUNT(*) FROM pomodoro_sessions 
            WHERE completed = 1 
            AND end_time >= datetime(?, 'unixepoch', 'localtime')
            '''
            
            params = [start_timestamp]
            
            # 如果提供了日期，则只统计该日期的完成数量
            if date_str:
                query += ' AND date = ?'
                params.append(date_str)
            
            cursor.execute(query, params)
            count = cursor.fetchone()[0]
            
            return count
        except Exception as e:
            log(f"获取已完成番茄钟数量时出错: {e}")
            return 0
        finally:
            conn.close()

    def add_user_message(self, message: str) -> int:
        """添加用户的消息到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        cursor.execute('''
        INSERT INTO inspiration_messages (content, type, created_at)
        VALUES (?, ?, ?)
        ''', (message, 'user', now))
        
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return message_id
        
    def add_quote(self, quote: str) -> int:
        """添加语录到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        cursor.execute('''
        INSERT INTO inspiration_messages (content, type, created_at)
        VALUES (?, ?, ?)
        ''', (quote, 'quote', now))
        
        quote_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return quote_id

    def remove_message(self, message_id: int) -> bool:
        """从数据库中删除一条消息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            DELETE FROM inspiration_messages
            WHERE id = ?
            ''', (message_id,))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
        except Exception as e:
            log(f"删除消息时出错: {str(e)}")
            return False
    
    def get_random_inspiration(self) -> Optional[Dict[str, Any]]:
        """根据权重随机获取一条励志语录或用户消息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取用户消息和语录的数量
            cursor.execute("SELECT COUNT(*) FROM inspiration_messages WHERE type = 'user'")
            user_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM inspiration_messages WHERE type = 'quote'")
            quote_count = cursor.fetchone()[0]
            
            # 如果没有任何消息，返回None
            if user_count + quote_count == 0:
                conn.close()
                return None
                
            import random
            
            # 计算权重
            total_count = user_count + quote_count
            user_probability = user_count / total_count if total_count > 0 else 0
            
            # 根据权重随机选择消息类型
            message_type = 'user' if random.random() < user_probability else 'quote'
            
            # 如果某一类型没有消息，就选择另一类型
            if (message_type == 'user' and user_count == 0) or (message_type == 'quote' and quote_count == 0):
                message_type = 'user' if quote_count == 0 else 'quote'
            
            # 随机获取指定类型的一条消息
            cursor.execute('''
            SELECT id, content, type, created_at
            FROM inspiration_messages
            WHERE type = ?
            ORDER BY RANDOM()
            LIMIT 1
            ''', (message_type,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'content': result[1],
                    'type': result[2],
                    'created_at': result[3]
                }
            return None
        except Exception as e:
            log(f"获取随机激励消息时出错: {str(e)}")
            return None
    
    def get_all_messages(self) -> List[Dict[str, Any]]:
        """获取所有励志语录和用户消息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, content, type, created_at
            FROM inspiration_messages
            ORDER BY type, created_at DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            messages = []
            for result in results:
                messages.append({
                    'id': result[0],
                    'content': result[1],
                    'type': result[2],
                    'created_at': result[3]
                })
            
            return messages
        except Exception as e:
            log(f"获取所有消息时出错: {str(e)}")
            return []
    
    def import_quotes_from_file(self, file_path: str) -> int:
        """从文件导入语录到数据库，返回成功导入的条数"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            count = 0
            now = datetime.now()
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 匹配并去掉前面的序号（如"1. "或"123. "格式）
                import re
                content = re.sub(r'^\d+\.\s*', '', line)
                
                if content:
                    cursor.execute('''
                    INSERT INTO inspiration_messages (content, type, created_at)
                    VALUES (?, ?, ?)
                    ''', (content, 'quote', now))
                    count += 1
            
            conn.commit()
            conn.close()
            
            return count
        except Exception as e:
            log(f"从文件导入语录时出错: {str(e)}")
            return 0
            
    def import_encrypted_quotes(self, file_path: str, key: int) -> int:
        """从加密文件导入语录到数据库，返回成功导入的条数"""
        try:
            # 读取加密文件内容
            with open(file_path, 'rb') as f:
                encrypted_content = f.read()
            
            # 解密内容
            decrypted_content = bytes([b ^ key for b in encrypted_content])
            
            # 将二进制内容转换为文本
            try:
                text_content = decrypted_content.decode('utf-8')
            except UnicodeDecodeError:
                # 如果UTF-8解码失败，尝试其他编码
                text_content = decrypted_content.decode('gbk', errors='ignore')
            
            lines = text_content.splitlines()
            
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            count = 0
            now = datetime.now()
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 匹配并去掉前面的序号（如"1. "或"123. "格式）
                import re
                content = re.sub(r'^\d+\.\s*', '', line)
                
                if content:
                    cursor.execute('''
                    INSERT INTO inspiration_messages (content, type, created_at)
                    VALUES (?, ?, ?)
                    ''', (content, 'quote', now))
                    count += 1
            
            conn.commit()
            conn.close()
            
            return count
        except Exception as e:
            log(f"从加密文件导入语录时出错: {str(e)}")
            return 0

# 提供一个全局单例访问点
_storage_instance = None

def get_storage() -> PomodoroStorage:
    """获取存储管理器实例"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = PomodoroStorage()
    return _storage_instance 