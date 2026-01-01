"""
数据库迁移脚本：添加总结字段
为 jobs 表添加 title, learning_points_json, thumbnail_url 字段
"""
import sqlite3
from pathlib import Path

def migrate():
    """执行迁移"""
    db_path = Path("./data/demo.db")
    
    if not db_path.exists():
        print(f"数据库文件不存在: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(jobs)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # 添加 title 字段
        if 'title' not in columns:
            print("添加 title 字段...")
            cursor.execute("ALTER TABLE jobs ADD COLUMN title TEXT")
            print("✓ title 字段已添加")
        else:
            print("✓ title 字段已存在")
        
        # 添加 learning_points_json 字段
        if 'learning_points_json' not in columns:
            print("添加 learning_points_json 字段...")
            cursor.execute("ALTER TABLE jobs ADD COLUMN learning_points_json TEXT")
            print("✓ learning_points_json 字段已添加")
        else:
            print("✓ learning_points_json 字段已存在")
        
        # 添加 thumbnail_url 字段
        if 'thumbnail_url' not in columns:
            print("添加 thumbnail_url 字段...")
            cursor.execute("ALTER TABLE jobs ADD COLUMN thumbnail_url TEXT")
            print("✓ thumbnail_url 字段已添加")
        else:
            print("✓ thumbnail_url 字段已存在")
        
        conn.commit()
        print("\n✅ 数据库迁移完成！")
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()

