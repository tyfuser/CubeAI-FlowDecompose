"""
视频拍摄辅助系统 - 细粒度分段分析脚本

每3秒分析一次，生成详细的分段报告。
"""
import json
import sys
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent))

from src.models.data_types import BBox, OpticalFlowData, SubjectTrackingData
from src.models.enums import MotionType, SpeedProfile, SuggestedScale


def analyze_segment(frames: List[np.ndarray], start_time: float, end_time: float, fps: float) -> Dict:
    """分析单个视频片段。"""
    if len(frames) < 2:
        return None
    
    # 计算光流
    flow_magnitudes = []
    flow_angles = []
    prev_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    
    for i in range(1, len(frames)):
        curr_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, curr_gray, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )
        mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        flow_magnitudes.append(np.mean(mag))
        flow_angles.append(np.mean(ang) * 180 / np.pi)
        prev_gray = curr_gray
    
    avg_speed = np.mean(flow_magnitudes) * fps if flow_magnitudes else 0.0
    primary_direction = np.mean(flow_angles) if flow_angles else 0.0
    
    # 检测主体
    bbox_areas = []
    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            frame_h, frame_w = frame.shape[:2]
            bbox_areas.append((w / frame_w) * (h / frame_h))
        else:
            bbox_areas.append(0.25)
    
    # 计算指标
    frame_pct_change = abs(bbox_areas[-1] - bbox_areas[0]) / bbox_areas[0] if bbox_areas[0] > 0 else 0
    frame_pct_change = min(1.0, frame_pct_change)
    
    variance = np.var(flow_magnitudes) if len(flow_magnitudes) > 1 else 0
    motion_smoothness = 1.0 / (1.0 + variance)
    subject_occupancy = np.mean(bbox_areas)
    
    # 推断运动类型
    if avg_speed < 5.0:
        motion_type = "static"
    elif motion_smoothness < 0.4:
        motion_type = "handheld"
    elif frame_pct_change > 0.1:
        motion_type = "dolly_in"
    else:
        direction = primary_direction % 360
        motion_type = "tilt" if 45 <= direction < 135 or 225 <= direction < 315 else "pan"
    
    # 速度描述
    if frame_pct_change < 0.1:
        speed_desc = "缓慢"
    elif frame_pct_change <= 0.25:
        speed_desc = "中速"
    else:
        speed_desc = "快速"
    
    # 器材建议
    if motion_smoothness > 0.7:
        equipment = "滑轨/云台"
    elif motion_smoothness >= 0.4:
        equipment = "手持云台"
    else:
        equipment = "静止/三脚架"
    
    # 置信度
    confidence = 0.5 + motion_smoothness * 0.3 + (1 - frame_pct_change) * 0.2
    confidence = min(1.0, max(0.0, confidence))
    
    return {
        "time_range": f"{start_time:.1f}s - {end_time:.1f}s",
        "start_time": start_time,
        "end_time": end_time,
        "avg_motion_px_s": round(avg_speed, 2),
        "frame_pct_change": round(frame_pct_change, 4),
        "motion_smoothness": round(motion_smoothness, 4),
        "subject_occupancy": round(subject_occupancy, 4),
        "motion_type": motion_type,
        "speed_desc": speed_desc,
        "equipment": equipment,
        "confidence": round(confidence, 4),
    }


def analyze_video_segments(video_path: str, segment_duration: float = 3.0) -> List[Dict]:
    """按固定时长分段分析视频。"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    frames_per_segment = int(fps * segment_duration)
    
    print(f"视频信息: {duration:.2f}秒, {fps:.0f}fps, 每段{segment_duration}秒({frames_per_segment}帧)")
    print(f"预计分段数: {int(np.ceil(duration / segment_duration))}")
    print("-" * 60)
    
    segments = []
    current_time = 0.0
    segment_idx = 0
    
    while current_time < duration:
        end_time = min(current_time + segment_duration, duration)
        
        # 读取该段的帧
        frames = []
        start_frame = int(current_time * fps)
        end_frame = int(end_time * fps)
        
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        for _ in range(end_frame - start_frame):
            ret, frame = cap.read()
            if not ret:
                break
            frame_resized = cv2.resize(frame, (640, 360))
            # 每隔几帧采样一次
            if len(frames) < 30:
                frames.append(frame_resized)
        
        if len(frames) >= 2:
            result = analyze_segment(frames, current_time, end_time, fps)
            if result:
                segments.append(result)
                segment_idx += 1
                print(f"[{segment_idx:2d}] {result['time_range']:15s} | {result['motion_type']:10s} | "
                      f"速度:{result['speed_desc']:4s} | 平滑度:{result['motion_smoothness']:.2%} | "
                      f"置信度:{result['confidence']:.2%}")
        
        current_time = end_time
    
    cap.release()
    return segments


def main():
    video_path = "用户视频.mp4"
    
    print("=" * 70)
    print("🎬 视频细粒度分段分析 (每3秒)")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"\n分析文件: {video_path}\n")
    
    if not Path(video_path).exists():
        print(f"❌ 文件不存在: {video_path}")
        return
    
    start = datetime.now()
    segments = analyze_video_segments(video_path, segment_duration=3.0)
    elapsed = (datetime.now() - start).total_seconds()
    
    # 统计
    print("\n" + "=" * 70)
    print("📊 分析统计")
    print("=" * 70)
    
    motion_types = {}
    for seg in segments:
        mt = seg['motion_type']
        motion_types[mt] = motion_types.get(mt, 0) + 1
    
    print(f"\n总分段数: {len(segments)}")
    print(f"处理时间: {elapsed:.2f}秒")
    print(f"\n运动类型分布:")
    for mt, count in sorted(motion_types.items(), key=lambda x: -x[1]):
        print(f"  {mt}: {count}段 ({count/len(segments)*100:.1f}%)")
    
    avg_smoothness = np.mean([s['motion_smoothness'] for s in segments])
    avg_confidence = np.mean([s['confidence'] for s in segments])
    print(f"\n平均运动平滑度: {avg_smoothness:.2%}")
    print(f"平均置信度: {avg_confidence:.2%}")
    
    # 保存结果
    output = {
        "video": video_path,
        "segment_duration": 3.0,
        "total_segments": len(segments),
        "processing_time": elapsed,
        "statistics": {
            "motion_type_distribution": motion_types,
            "avg_motion_smoothness": round(avg_smoothness, 4),
            "avg_confidence": round(avg_confidence, 4),
        },
        "segments": segments
    }
    
    output_file = f"segment_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n📄 结果已保存: {output_file}")


if __name__ == "__main__":
    main()
