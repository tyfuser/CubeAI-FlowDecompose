"""
视频拍摄辅助系统 - 基于镜头切换的分割分析

通过检测帧间差异来识别镜头切换点，然后对每个镜头进行独立分析。

并显示给出中间变量
"""
import json
import sys
import cv2
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from src.models.enums import MotionType


def detect_shot_boundaries(video_path: str, threshold: float = 30.0) -> List[Tuple[float, float]]:
    """
    检测镜头切换边界。
    
    使用帧间直方图差异来检测场景变化。
    
    Args:
        video_path: 视频路径
        threshold: 切换检测阈值（越大越不敏感）
        
    Returns:
        镜头列表 [(start_time, end_time), ...]
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    
    print(f"视频信息: {duration:.2f}秒, {fps:.0f}fps, {total_frames}帧")
    print(f"镜头切换检测阈值: {threshold}")
    print("-" * 60)
    
    # 读取所有帧的直方图
    prev_hist = None
    frame_diffs = []
    frame_idx = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 转换为HSV并计算直方图
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        
        if prev_hist is not None:
            # 计算直方图差异（使用相关性）
            diff = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CHISQR)
            frame_diffs.append((frame_idx, diff))
        
        prev_hist = hist
        frame_idx += 1
    
    cap.release()
    
    # 找到切换点（差异超过阈值的帧）
    cut_frames = [0]  # 开始帧
    
    for idx, diff in frame_diffs:
        if diff > threshold:
            # 避免连续检测
            if idx - cut_frames[-1] > fps * 0.5:  # 至少间隔0.5秒
                cut_frames.append(idx)
    
    cut_frames.append(total_frames)  # 结束帧
    
    # 转换为时间段
    shots = []
    for i in range(len(cut_frames) - 1):
        start_time = cut_frames[i] / fps
        end_time = cut_frames[i + 1] / fps
        if end_time - start_time >= 0.5:  # 至少0.5秒的镜头
            shots.append((start_time, end_time))
    
    return shots


def analyze_shot(video_path: str, start_time: float, end_time: float, shot_idx: int, verbose: bool = True) -> Dict:
    """
    分析单个镜头，显示所有中间计算过程。
    
    Args:
        video_path: 视频路径
        start_time: 开始时间
        end_time: 结束时间
        shot_idx: 镜头序号
        verbose: 是否显示详细中间计算
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    start_frame = int(start_time * fps)
    end_frame = int(end_time * fps)
    total_shot_frames = end_frame - start_frame
    
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    frames = []
    for _ in range(min(total_shot_frames, 90)):  # 最多90帧
        ret, frame = cap.read()
        if not ret:
            break
        frame_resized = cv2.resize(frame, (640, 360))
        if len(frames) < 30:  # 采样30帧
            frames.append(frame_resized)
    
    cap.release()
    
    if len(frames) < 2:
        return None
    
    if verbose:
        print(f"\n{'='*70}")
        print(f"📹 镜头 {shot_idx} 详细分析")
        print(f"{'='*70}")
        print(f"时间范围: {start_time:.2f}s - {end_time:.2f}s (时长: {end_time-start_time:.2f}s)")
        print(f"帧范围: {start_frame} - {end_frame} (共{total_shot_frames}帧)")
        print(f"采样帧数: {len(frames)}帧")
    
    # ========== 1. 计算光流 ==========
    flow_magnitudes = []
    flow_angles = []
    flow_x_components = []
    flow_y_components = []
    
    prev_gray = cv2.cvtColor(frames[0], cv2.COLOR_BGR2GRAY)
    
    if verbose:
        print(f"\n--- 光流计算 (Farneback算法) ---")
        print(f"参数: pyr_scale=0.5, levels=3, winsize=15, iterations=3")
    
    for i in range(1, len(frames)):
        curr_gray = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, curr_gray, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )
        
        # 计算幅度和角度
        mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        
        avg_mag = float(np.mean(mag))
        avg_ang = float(np.mean(ang) * 180 / np.pi)
        avg_flow_x = float(np.mean(flow[..., 0]))
        avg_flow_y = float(np.mean(flow[..., 1]))
        
        flow_magnitudes.append(avg_mag)
        flow_angles.append(avg_ang)
        flow_x_components.append(avg_flow_x)
        flow_y_components.append(avg_flow_y)
        
        prev_gray = curr_gray
    
    # ========== 2. 光流统计 ==========
    avg_magnitude = float(np.mean(flow_magnitudes)) if flow_magnitudes else 0.0
    std_magnitude = float(np.std(flow_magnitudes)) if flow_magnitudes else 0.0
    min_magnitude = float(np.min(flow_magnitudes)) if flow_magnitudes else 0.0
    max_magnitude = float(np.max(flow_magnitudes)) if flow_magnitudes else 0.0
    variance = float(np.var(flow_magnitudes)) if len(flow_magnitudes) > 1 else 0.0
    
    avg_angle = float(np.mean(flow_angles)) if flow_angles else 0.0
    avg_flow_x = float(np.mean(flow_x_components)) if flow_x_components else 0.0
    avg_flow_y = float(np.mean(flow_y_components)) if flow_y_components else 0.0
    
    # 转换为像素/秒
    avg_speed = avg_magnitude * fps
    
    if verbose:
        print(f"\n光流幅度统计:")
        print(f"  平均幅度: {avg_magnitude:.4f} px/帧")
        print(f"  标准差: {std_magnitude:.4f}")
        print(f"  最小值: {min_magnitude:.4f}")
        print(f"  最大值: {max_magnitude:.4f}")
        print(f"  方差: {variance:.4f}")
        print(f"  平均速度: {avg_speed:.2f} px/s (= {avg_magnitude:.4f} × {fps:.0f}fps)")
        
        print(f"\n光流方向统计:")
        print(f"  平均角度: {avg_angle:.2f}°")
        print(f"  平均X分量: {avg_flow_x:.4f} (正=向右)")
        print(f"  平均Y分量: {avg_flow_y:.4f} (正=向下)")
        
        # 显示前5帧的光流值
        print(f"\n逐帧光流幅度 (前5帧):")
        for i, mag in enumerate(flow_magnitudes[:5]):
            print(f"  帧{i+1}: {mag:.4f} px/帧")
        if len(flow_magnitudes) > 5:
            print(f"  ... (共{len(flow_magnitudes)}帧)")
    
    # ========== 3. 计算运动平滑度 ==========
    motion_smoothness = 1.0 / (1.0 + variance)
    
    if verbose:
        print(f"\n--- 运动平滑度计算 ---")
        print(f"公式: smoothness = 1 / (1 + variance)")
        print(f"计算: smoothness = 1 / (1 + {variance:.4f}) = {motion_smoothness:.4f}")
        print(f"解释: 方差越小，平滑度越高")
    
    # ========== 4. 推断运动类型 ==========
    if verbose:
        print(f"\n--- 运动类型推断 ---")
        print(f"判断条件:")
        print(f"  avg_speed < 5.0 → static")
        print(f"  smoothness < 0.4 → handheld")
        print(f"  smoothness > 0.8 → dolly/track")
        print(f"  其他 → pan/tilt")
    
    if avg_speed < 5.0:
        motion_type = "static"
        type_reason = f"avg_speed({avg_speed:.2f}) < 5.0"
    elif motion_smoothness < 0.4:
        motion_type = "handheld"
        type_reason = f"smoothness({motion_smoothness:.4f}) < 0.4"
    elif motion_smoothness > 0.8:
        motion_type = "dolly/track"
        type_reason = f"smoothness({motion_smoothness:.4f}) > 0.8"
    else:
        motion_type = "pan/tilt"
        type_reason = f"0.4 <= smoothness({motion_smoothness:.4f}) <= 0.8"
    
    if verbose:
        print(f"结果: {motion_type} (因为 {type_reason})")
    
    # ========== 5. 拍摄质量评估 ==========
    if verbose:
        print(f"\n--- 拍摄质量评估 ---")
        print(f"评估标准 (基于运动平滑度):")
        print(f"  A (优秀): smoothness > 0.8")
        print(f"  B (良好): smoothness > 0.5")
        print(f"  C (一般): smoothness > 0.3")
        print(f"  D (需改进): smoothness <= 0.3")
    
    if motion_smoothness > 0.8:
        quality = "优秀"
        quality_score = "A"
    elif motion_smoothness > 0.5:
        quality = "良好"
        quality_score = "B"
    elif motion_smoothness > 0.3:
        quality = "一般"
        quality_score = "C"
    else:
        quality = "需改进"
        quality_score = "D"
    
    if verbose:
        print(f"结果: {quality_score} ({quality})")
    
    return {
        "start_time": round(start_time, 2),
        "end_time": round(end_time, 2),
        "duration": round(end_time - start_time, 2),
        "frame_range": [start_frame, end_frame],
        "sampled_frames": len(frames),
        # 光流原始数据
        "optical_flow": {
            "avg_magnitude_per_frame": round(avg_magnitude, 4),
            "std_magnitude": round(std_magnitude, 4),
            "min_magnitude": round(min_magnitude, 4),
            "max_magnitude": round(max_magnitude, 4),
            "variance": round(variance, 4),
            "avg_angle_deg": round(avg_angle, 2),
            "avg_flow_x": round(avg_flow_x, 4),
            "avg_flow_y": round(avg_flow_y, 4),
        },
        # 计算结果
        "avg_motion_px_s": round(avg_speed, 2),
        "motion_smoothness": round(motion_smoothness, 4),
        "motion_type": motion_type,
        "motion_type_reason": type_reason,
        "quality": quality,
        "quality_score": quality_score,
    }


def main():
    video_path = "用户视频.mp4"
    
    print("=" * 70)
    print("🎬 基于镜头切换的视频分割分析")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print(f"\n分析文件: {video_path}\n")
    
    if not Path(video_path).exists():
        print(f"❌ 文件不存在: {video_path}")
        return
    
    # 检测镜头切换
    print("🔍 检测镜头切换点...")
    shots = detect_shot_boundaries(video_path, threshold=25.0)
    print(f"\n检测到 {len(shots)} 个镜头\n")
    
    # 分析每个镜头
    print("\n📊 分析各镜头...")
    
    results = []
    for i, (start, end) in enumerate(shots, 1):
        result = analyze_shot(video_path, start, end, shot_idx=i, verbose=True)
        if result:
            results.append(result)
    
    # 统计
    print("\n" + "=" * 70)
    print("📋 汇总表格")
    print("=" * 70)
    print(f"\n{'镜头':<6} {'时间范围':<18} {'时长':<8} {'运动类型':<12} {'平滑度':<10} {'质量':<6}")
    print("-" * 70)
    for i, r in enumerate(results, 1):
        print(f"{i:<6} {r['start_time']:.1f}s - {r['end_time']:.1f}s{'':<4} {r['duration']:.1f}s{'':<4} "
              f"{r['motion_type']:<12} {r['motion_smoothness']:.2%}{'':<4} {r['quality_score']}")
    
    print("\n" + "=" * 70)
    print("📋 分析摘要")
    print("=" * 70)
    
    print(f"\n总镜头数: {len(results)}")
    
    # 运动类型分布
    motion_types = {}
    for r in results:
        mt = r['motion_type']
        motion_types[mt] = motion_types.get(mt, 0) + 1
    
    print("\n运动类型分布:")
    for mt, count in sorted(motion_types.items(), key=lambda x: -x[1]):
        print(f"  {mt}: {count}个镜头")
    
    # 质量分布
    quality_dist = {}
    for r in results:
        q = r['quality_score']
        quality_dist[q] = quality_dist.get(q, 0) + 1
    
    print("\n拍摄质量分布:")
    for q in ['A', 'B', 'C', 'D']:
        count = quality_dist.get(q, 0)
        if count > 0:
            print(f"  {q} ({['优秀','良好','一般','需改进'][['A','B','C','D'].index(q)]}): {count}个镜头")
    
    avg_smoothness = np.mean([r['motion_smoothness'] for r in results])
    print(f"\n平均运动平滑度: {avg_smoothness:.2%}")
    
    # 保存结果
    output = {
        "video": video_path,
        "total_shots": len(results),
        "motion_type_distribution": motion_types,
        "quality_distribution": quality_dist,
        "avg_smoothness": float(avg_smoothness),
        "shots": results
    }
    
    output_file = f"shot_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n📄 结果已保存: {output_file}")


if __name__ == "__main__":
    main()
