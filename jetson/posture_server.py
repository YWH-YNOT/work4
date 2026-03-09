"""
Jetson 端姿态检测服务 v2.0
功能：
  - YOLO11-npose 推理 -> 多维评分姿态分类
  - 推流(15fps) / 推理(5fps) 解耦，降低 GPU 负载
  - 本地平滑：每人维护最近 K 帧状态，取众数
  - 困倦持续计时：连续困倦超过阈值才标记 drowsy_duration
  - 人数变化事件推送
  - ThreadPoolExecutor 限制推送并发
  - Flask 路由：/video_feed, /status, /health(含CPU/温度)
  - 命令行参数：--infer-rate, --quality, --fastapi, --cam
"""

import argparse
import base64
import os
import socket
import threading
import time
from collections import Counter, deque
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np
from flask import Flask, Response, jsonify
from ultralytics import YOLO

try:
    import requests as _requests_lib
except ImportError:
    _requests_lib = None
    print("⚠️  requests 未安装，将跳过 FastAPI 推送。运行: pip install requests")

try:
    import psutil
    _PSUTIL_OK = True
except ImportError:
    _PSUTIL_OK = False

# ─────────────────────── 命令行参数 ───────────────────────
parser = argparse.ArgumentParser(description="Jetson 姿态检测服务 v2.0")
parser.add_argument("--model",       default="yolo11n-pose.engine", help="YOLO 模型路径")
parser.add_argument("--cam",         type=int, default=0,           help="摄像头编号")
parser.add_argument("--width",       type=int, default=640,         help="采集宽度")
parser.add_argument("--height",      type=int, default=480,         help="采集高度")
parser.add_argument("--infer-rate",  type=int, default=3,           help="每 N 帧推理一次（越大 FPS 越低）")
parser.add_argument("--quality",     type=int, default=65,          help="推流 JPEG 质量(1-100)")
parser.add_argument("--push-interval", type=float, default=0.1,     help="推送到FastAPI的最短间隔(秒)")
parser.add_argument("--fastapi",     default=os.getenv("FASTAPI_URL", "http://172.20.10.8:8002"),
                                                                     help="FastAPI 服务地址")
parser.add_argument("--port",        type=int, default=5000,        help="Flask 服务端口")
parser.add_argument("--smooth-k",    type=int, default=5,           help="本地状态平滑帧数")
args = parser.parse_args()

# ─────────────────────── 模型加载 ────────────────────────
model = YOLO(args.model)
print(f"✅ 模型加载完毕: {args.model}")

PUSH_API = f"{args.fastapi}/api/v1/posture/push"

# ─────────────────────── 标签定义 ────────────────────────
LABEL_CN = {
    "attentive":  "Focused",
    "drowsy":     "Drowsy",
    "distracted": "Distracted",
    "absent":     "Absent",
}
LABEL_COLOR = {
    "attentive":  (0, 200, 0),
    "drowsy":     (0, 165, 255),
    "distracted": (0, 0, 255),
    "absent":     (128, 128, 128),
}

KP_CONF_THRESH = 0.3       # 关键点置信度阈值
DROWSY_PERSIST_SEC = 3.0   # 持续困倦超过 N 秒才输出 drowsy_duration


# ─────────────────────── 关键点工具 ──────────────────────
def get_kp(kps, idx):
    """安全获取关键点，置信度不足返回 None"""
    if kps is None or len(kps) <= idx:
        return None
    x, y, c = kps[idx]
    return (float(x), float(y)) if float(c) >= KP_CONF_THRESH else None


def _dist(a, b):
    """两点欧式距离"""
    if a is None or b is None:
        return None
    return float(np.hypot(a[0] - b[0], a[1] - b[1]))


# ─────────────────────── 多维评分姿态分类 ────────────────
def classify_posture(kps: np.ndarray) -> tuple[str, float]:
    """
    基于多维特征评分的姿态分类。
    返回 (label, confidence)，confidence ∈ [0, 1]。

    评分逻辑（0 正常 → 越高越偏离正常）：
    - drowsy_score  : 头部下垂度 + 眼睛闭合估计
    - distracted_score: 侧脸偏转 + 身体偏转
    最终取最高分决策，低于阈值则 attentive。
    """
    # ── 关键点提取 ──
    nose      = get_kp(kps, 0)
    l_eye     = get_kp(kps, 1);  r_eye  = get_kp(kps, 2)
    l_ear     = get_kp(kps, 3);  r_ear  = get_kp(kps, 4)
    l_sh      = get_kp(kps, 5);  r_sh   = get_kp(kps, 6)
    l_elbow   = get_kp(kps, 7);  r_elbow = get_kp(kps, 8)
    l_wr      = get_kp(kps, 9);  r_wr   = get_kp(kps, 10)

    head_pts = [p for p in [nose, l_eye, r_eye, l_ear, r_ear] if p is not None]

    if not head_pts:
        return "absent", 1.0

    sh_ys = [p[1] for p in [l_sh, r_sh] if p is not None]
    sh_xs = [p[0] for p in [l_sh, r_sh] if p is not None]
    sh_mid_y  = float(np.mean(sh_ys)) if sh_ys else None
    sh_width  = abs(l_sh[0] - r_sh[0]) if (l_sh and r_sh) else None

    head_center_y = float(np.mean([p[1] for p in head_pts]))
    head_center_x = float(np.mean([p[0] for p in head_pts]))

    drowsy_score     = 0.0
    distracted_score = 0.0

    # ── 困倦特征 1：头部在肩线以下（主要判据）──
    if sh_mid_y is not None:
        # 归一化到肩宽（让不同距离的人可比）
        ref = sh_width if sh_width and sh_width > 10 else 100
        drop = (head_center_y - sh_mid_y) / ref
        # drop > 0.3 → 明显垂头
        drowsy_score += float(np.clip(drop / 0.5, 0, 1))

    # ── 困倦特征 2：鼻子 Y 高于双眼 Y（低头时鼻子相对更低）──
    if nose and l_eye and r_eye:
        eye_y = (l_eye[1] + r_eye[1]) / 2
        nose_drop = (nose[1] - eye_y)  # 正值 = 鼻子在眼睛下方（正常），负值 = 抬头
        if sh_width:
            drowsy_score += float(np.clip(nose_drop / (sh_width * 0.5) - 0.5, 0, 0.5))

    # ── 分心特征 1：只有单侧耳朵可见（侧脸/低头）──
    ear_visible = (l_ear is not None, r_ear is not None)
    if ear_visible[0] != ear_visible[1]:   # 只有一侧
        distracted_score += 0.5
    if not ear_visible[0] and not ear_visible[1] and nose is not None:
        # 双耳不可见但鼻子可见 → 侧脸严重
        distracted_score += 0.7

    # ── 分心特征 2：耳朵到鼻子水平偏移（侧脸程度）──
    if nose and (l_ear or r_ear):
        visible_ears_x = [e[0] for e in [l_ear, r_ear] if e]
        ear_center_x = float(np.mean(visible_ears_x))
        if sh_width and sh_width > 10:
            h_shift = abs(nose[0] - ear_center_x) / sh_width
            # 正脸时鼻子大概在耳朵前面，h_shift 小
            distracted_score += float(np.clip(h_shift - 0.3, 0, 0.7))

    # ── 分心特征 3：手腕超过肩膀高度（举手/看手机）──
    if sh_mid_y is not None:
        for wr in [l_wr, r_wr]:
            if wr and wr[1] < sh_mid_y - 10:   # 手腕明显高于肩线
                distracted_score += 0.4
                break

    # ── 分心特征 4：身体左右偏转（肩膀倾斜）──
    if l_sh and r_sh and sh_width and sh_width > 10:
        shoulder_tilt = abs(l_sh[1] - r_sh[1]) / sh_width
        distracted_score += float(np.clip(shoulder_tilt - 0.15, 0, 0.4))

    # ── 决策 ──
    DROWSY_THRESH     = 0.55
    DISTRACTED_THRESH = 0.60

    if drowsy_score >= DROWSY_THRESH and drowsy_score >= distracted_score:
        conf = float(np.clip(drowsy_score, 0, 1))
        return "drowsy", conf
    if distracted_score >= DISTRACTED_THRESH:
        conf = float(np.clip(distracted_score, 0, 1))
        return "distracted", conf

    # attentive: confidence = 1 - max(scores)
    max_score = max(drowsy_score, distracted_score)
    return "attentive", float(np.clip(1.0 - max_score, 0.3, 1.0))


# ─────────────────────── 本地状态平滑 ─────────────────────
# slot_id -> deque([label, ...])
_smooth_history: dict[int, deque] = {}
# 困倦计时: slot_id -> (start_ts_or_None)
_drowsy_since: dict[int, float | None] = {}

def _smooth_label(slot_id: int, raw_label: str) -> tuple[str, float]:
    """
    用最近 K 帧的多数表决对标签做本地平滑。
    返回 (smoothed_label, drowsy_duration_sec)
    """
    if slot_id not in _smooth_history:
        _smooth_history[slot_id] = deque(maxlen=args.smooth_k)
        _drowsy_since[slot_id]   = None

    _smooth_history[slot_id].append(raw_label)
    smoothed = Counter(_smooth_history[slot_id]).most_common(1)[0][0]

    # 困倦持续计时
    now = time.time()
    if smoothed == "drowsy":
        if _drowsy_since[slot_id] is None:
            _drowsy_since[slot_id] = now
        duration = now - _drowsy_since[slot_id]
    else:
        _drowsy_since[slot_id] = None
        duration = 0.0

    return smoothed, duration


# ─────────────────────── 标注绘制 ────────────────────────
def draw_label(frame, text: str, pos, color, conf: float = 1.0):
    """在帧上绘制带背景的标签，置信度用颜色透明度体现"""
    x, y = int(pos[0]), int(pos[1])
    font, scale, thick = cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
    (tw, th), bl = cv2.getTextSize(text, font, scale, thick)
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y - th - 6), (x + tw + 6, y + bl + 2), (0, 0, 0), -1)
    alpha = 0.4 + 0.4 * conf   # 置信度越高背景越深
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    cv2.putText(frame, text, (x + 3, y), font, scale, color, thick, cv2.LINE_AA)


# ─────────────────────── 帧推理 ──────────────────────────
def process_frame(frame: np.ndarray) -> tuple[np.ndarray, list]:
    """
    对单帧执行 YOLO 推理 + 姿态分类 + 本地平滑。
    返回 (annotated_frame, students_list)
    """
    results = model(frame, stream=False, verbose=False)
    result  = results[0]
    annotated = result.plot(kpt_radius=3, line_width=1)
    students  = []

    if result.keypoints is not None and result.boxes is not None:
        kps_all = result.keypoints.data.cpu().numpy()
        boxes   = result.boxes.xyxy.cpu().numpy()
        confs   = result.boxes.conf.cpu().numpy()

        for i, (kps, box, det_conf) in enumerate(zip(kps_all, boxes, confs)):
            raw_label, pose_conf = classify_posture(kps)
            smoothed, drowsy_dur  = _smooth_label(i + 1, raw_label)

            color = LABEL_COLOR[smoothed]
            x1, y1 = int(box[0]), int(box[1])

            # 标签文本：编号 + 状态 + 置信度
            label_text = f"#{i+1} {LABEL_CN[smoothed]} {pose_conf:.0%}"
            # 困倦持续超过阈值时附加时间
            if smoothed == "drowsy" and drowsy_dur >= DROWSY_PERSIST_SEC:
                label_text += f" ({drowsy_dur:.0f}s)"

            draw_label(annotated, label_text, (x1, max(y1 - 10, 12)), color, pose_conf)

            student_entry = {
                "id":            i + 1,
                "label":         smoothed,
                "label_cn":      LABEL_CN[smoothed],
                "confidence":    round(float(pose_conf), 3),
                "det_conf":      round(float(det_conf), 3),
                "bbox":          [int(box[0]), int(box[1]), int(box[2]), int(box[3])],
                "drowsy_duration": round(drowsy_dur, 1) if drowsy_dur >= DROWSY_PERSIST_SEC else 0.0,
            }
            students.append(student_entry)

    return annotated, students


# ─────────────────────── 人脸裁剪 ─────────────────────────
def _crop_face(frame: np.ndarray, bbox: list) -> str:
    """裁剪头部区域，缩到 96×96，返回 base64 JPEG"""
    x1, y1, x2, y2 = bbox
    h = y2 - y1
    face_y1 = max(0, y1 - int(h * 0.1))
    face_y2 = min(frame.shape[0], y1 + int(h * 0.5))
    face_x1, face_x2 = max(0, x1), min(frame.shape[1], x2)
    crop = frame[face_y1:face_y2, face_x1:face_x2]
    if crop.size == 0:
        return ""
    crop = cv2.resize(crop, (96, 96))
    ok, buf = cv2.imencode('.jpg', crop, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return base64.b64encode(buf.tobytes()).decode() if ok else ""


# ─────────────────────── FastAPI 推送 ────────────────────
_last_headcount = -1   # 上次推送的人数，用于检测变化

def push_to_fastapi(students: list, jip: str, jpeg_bytes: bytes, frame: np.ndarray):
    """后台线程: POST 姿态数据 + JPEG帧 + 人脸裁剪 → FastAPI"""
    global _last_headcount
    if _requests_lib is None:
        return

    try:
        enriched = []
        for s in students:
            sd = dict(s)
            if frame is not None and "bbox" in sd:
                sd["face_crop"] = _crop_face(frame, sd["bbox"])
            enriched.append(sd)

        headcount = len(students)
        headcount_event = None
        if _last_headcount >= 0 and headcount != _last_headcount:
            headcount_event = {
                "type":  "enter" if headcount > _last_headcount else "leave",
                "prev":  _last_headcount,
                "curr":  headcount,
                "delta": headcount - _last_headcount,
            }
        _last_headcount = headcount

        payload = {
            "students":        enriched,
            "jetson_ip":       jip,
            "course_id":       None,
            "frame_b64":       base64.b64encode(jpeg_bytes).decode(),
            "headcount_event": headcount_event,
        }
        _requests_lib.post(PUSH_API, json=payload, timeout=2.0)
    except Exception:
        pass


# ─────────────────────── IP 获取 ─────────────────────────
def _get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

jetson_ip = _get_local_ip()

# ─────────────────────── 全局状态 ────────────────────────
latest_status: dict = {"timestamp": 0, "students": [], "fps": 0.0}
status_lock   = threading.Lock()
_frame_lock   = threading.Lock()
_latest_jpeg  = b""

_push_executor = ThreadPoolExecutor(max_workers=2)
_last_push_ts  = 0.0

# 推理性能统计
_infer_times   = deque(maxlen=30)


# ─────────────────────── 采集主循环 ──────────────────────
def capture_loop():
    global _latest_jpeg, _last_push_ts

    cap = cv2.VideoCapture(args.cam)
    if not cap.isOpened():
        print(f"⚠️  无法打开摄像头 {args.cam}")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_FPS, 30)
    print(f"✅ 摄像头已打开  分辨率: {args.width}×{args.height}")

    frame_idx    = 0
    last_students: list = []
    last_annotated: np.ndarray | None = None

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue

        frame_idx += 1

        # ─── 推理帧（每 infer-rate 帧推理一次）───
        if frame_idx % args.infer_rate == 0:
            t0 = time.time()
            annotated, students = process_frame(frame)
            infer_ms = (time.time() - t0) * 1000
            _infer_times.append(infer_ms)

            last_students  = students
            last_annotated = annotated

            with status_lock:
                latest_status["timestamp"] = int(time.time())
                latest_status["students"]  = students
                latest_status["fps"]       = round(1000 / (sum(_infer_times) / len(_infer_times)), 1) if _infer_times else 0.0

        # ─── 推流帧（每帧都更新，推流更流畅）───
        display = last_annotated if last_annotated is not None else frame
        ok, buf  = cv2.imencode('.jpg', display, [cv2.IMWRITE_JPEG_QUALITY, args.quality])
        if ok:
            jpeg_bytes = buf.tobytes()
            with _frame_lock:
                _latest_jpeg = jpeg_bytes

            # ─── 按时间间隔推送 FastAPI ───
            now = time.time()
            if now - _last_push_ts >= args.push_interval and last_students is not None:
                _last_push_ts = now
                # 拷贝一份避免线程竞争
                _push_executor.submit(
                    push_to_fastapi,
                    list(last_students), jetson_ip, jpeg_bytes, frame.copy()
                )


# ─────────────────────── MJPEG 流生成 ────────────────────
def generate_stream():
    """MJPEG 流生成器（从缓冲区读）"""
    while True:
        with _frame_lock:
            frame_bytes = _latest_jpeg
        if frame_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.05)   # ~20fps 推流上限


# ─────────────────────── Flask 路由 ──────────────────────
app = Flask(__name__)


@app.route('/video_feed')
def video_feed():
    return Response(generate_stream(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/status')
def get_status():
    with status_lock:
        return jsonify(latest_status)


@app.route('/health')
def health():
    info: dict = {
        "status": "ok",
        "model":  args.model,
        "fps":    latest_status.get("fps", 0),
        "headcount": len(latest_status.get("students", [])),
    }
    # 平均推理耗时
    if _infer_times:
        info["avg_infer_ms"] = round(sum(_infer_times) / len(_infer_times), 1)

    # psutil 资源监控（Jetson 上可用）
    if _PSUTIL_OK:
        info["cpu_percent"]    = psutil.cpu_percent(interval=None)
        info["ram_percent"]    = psutil.virtual_memory().percent
        # 尝试读取 Jetson 主核温度
        try:
            temps = psutil.sensors_temperatures()
            for key in ("thermal_zone0", "cpu_thermal", "coretemp"):
                if key in temps and temps[key]:
                    info["cpu_temp_c"] = round(temps[key][0].current, 1)
                    break
        except Exception:
            pass

    return jsonify(info)


@app.route('/stats-summary')
def stats_summary():
    """当前课堂学生状态统计摘要"""
    with status_lock:
        students = latest_status.get("students", [])
    counts = {"attentive": 0, "drowsy": 0, "distracted": 0, "absent": 0}
    drowsy_warnings = []
    for s in students:
        label = s.get("label", "")
        if label in counts:
            counts[label] += 1
        if s.get("drowsy_duration", 0) >= DROWSY_PERSIST_SEC:
            drowsy_warnings.append({
                "id":       s["id"],
                "duration": s["drowsy_duration"],
            })
    total = sum(counts.values())
    return jsonify({
        **counts,
        "total":           total,
        "attentive_rate":  round(counts["attentive"] / total * 100, 1) if total else 0,
        "drowsy_warnings": drowsy_warnings,
        "timestamp":       latest_status.get("timestamp", 0),
    })


# ─────────────────────── 入口 ────────────────────────────
if __name__ == '__main__':
    print(f"\n{'='*50}")
    print(f"  Jetson 姿态检测服务 v2.0")
    print(f"  IP 地址  : {jetson_ip}")
    print(f"  视频流   : http://{jetson_ip}:{args.port}/video_feed")
    print(f"  状态接口 : http://{jetson_ip}:{args.port}/status")
    print(f"  推送目标 : {PUSH_API}")
    print(f"  推理帧率 : 每 {args.infer_rate} 帧推理一次")
    print(f"  JPEG质量 : {args.quality}")
    print(f"{'='*50}\n")

    # 启动采集推理线程
    threading.Thread(target=capture_loop, daemon=True).start()

    app.run(host='0.0.0.0', port=args.port, debug=False, threaded=True)
