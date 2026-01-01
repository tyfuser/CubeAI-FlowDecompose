#!/usr/bin/env python3
"""
为已有的成功任务生成缩略图
运行方式: python generate_thumbnails.py
"""
import sqlite3
from pathlib import Path
import json
import sys

# 添加app模块到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings

def generate_thumbnails():
    """为所有缺少缩略图的成功任务生成缩略图"""
    
    data_dir = settings.data_dir
    db_path = data_dir / "demo.db"
    
    if not db_path.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    print(f"连接数据库: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 查询所有成功但没有缩略图的任务
    cursor.execute("""
        SELECT id, result_json, title 
        FROM jobs 
        WHERE status = 'succeeded' 
        AND (thumbnail_url IS NULL OR thumbnail_url = '')
        ORDER BY created_at DESC
    """)
    
    rows = cursor.fetchall()
    total = len(rows)
    
    if total == 0:
        print("✓ 所有成功的任务都已有缩略图")
        conn.close()
        return
    
    print(f"\n找到 {total} 个需要生成缩略图的任务\n")
    
    success_count = 0
    failed_count = 0
    
    for job_id, result_json, title in rows:
        try:
            if not result_json:
                print(f"⊘ {job_id}: 跳过（无结果数据）")
                failed_count += 1
                continue
            
            result = json.loads(result_json)
            target = result.get("target", {})
            keyframes = target.get("keyframes", [])
            
            if not keyframes:
                print(f"⊘ {job_id}: 跳过（无关键帧）")
                failed_count += 1
                continue
            
            # 取第一个关键帧
            first_keyframe = keyframes[0]
            keyframe_path_str = first_keyframe.get("keyframe_path")
            
            if not keyframe_path_str:
                print(f"⊘ {job_id}: 跳过（关键帧路径为空）")
                failed_count += 1
                continue
            
            keyframe_path = Path(keyframe_path_str)
            
            if not keyframe_path.exists():
                print(f"✗ {job_id}: 关键帧文件不存在: {keyframe_path}")
                failed_count += 1
                continue
            
            # 生成缩略图URL
            try:
                relative_path = keyframe_path.relative_to(data_dir)
                thumbnail_url = f"/data/{relative_path.as_posix()}"
            except ValueError:
                # 如果路径不在data_dir下，尝试其他方式
                if '/data/' in str(keyframe_path):
                    parts = str(keyframe_path).split('/data/', 1)
                    thumbnail_url = f"/data/{parts[1]}"
                else:
                    print(f"✗ {job_id}: 无法生成相对路径")
                    failed_count += 1
                    continue
            
            # 更新数据库
            cursor.execute(
                "UPDATE jobs SET thumbnail_url = ? WHERE id = ?",
                (thumbnail_url, job_id)
            )
            
            title_display = (title[:40] + '...') if title and len(title) > 40 else (title or '未命名')
            print(f"✓ {job_id}: {title_display}")
            print(f"  └─ {thumbnail_url}")
            success_count += 1
            
        except Exception as e:
            print(f"✗ {job_id}: 错误 - {str(e)}")
            failed_count += 1
    
    # 提交更改
    conn.commit()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"完成！")
    print(f"  成功: {success_count}/{total}")
    print(f"  失败: {failed_count}/{total}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    try:
        generate_thumbnails()
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

