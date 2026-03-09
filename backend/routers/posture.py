"""姿态检测路由 - 接收 Jetson 推送、提供查询接口"""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import desc
from core.database import get_db
from core.auth import get_current_user, require_role
from core.config import settings
from models import core as models
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, timezone
import os
import base64
import asyncio
import time as _time
import requests as _req
from typing import List as _List

# ─── 内存帧缓存（Jetson push 带来的最新 JPEG）───
_latest_frame_bytes: Optional[bytes] = None
# ─── SSE 订阅者队列列表（每个连接对应一个 asyncio.Queue）───
_sse_subscribers: _List[asyncio.Queue] = []

router = APIRouter()

# ─── Jetson 服务地址（从 .env 通过 pydantic settings 加载）───
JETSON_IP   = settings.JETSON_IP
JETSON_PORT = settings.JETSON_PORT


# ─── Pydantic Schemas ───────────────────────

class StudentPosture(BaseModel):
    id:        int
    label:     str            # attentive / drowsy / distracted / absent
    label_cn:  str
    bbox:      List[int]      # [x1, y1, x2, y2]
    face_crop: Optional[str] = None    # 头部裁剪图 base64（身份识别用）
    confidence:      Optional[float] = None   # 姿态分类置信度 0~1
    det_conf:        Optional[float] = None   # YOLO 检测置信度 0~1
    drowsy_duration: Optional[float] = 0.0   # 持续困倦秒数

class HeadcountEvent(BaseModel):
    type:  str    # "enter" | "leave"
    prev:  int
    curr:  int
    delta: int

class PushPayload(BaseModel):
    students:        List[StudentPosture]
    jetson_ip:       Optional[str] = None
    course_id:       Optional[int] = None
    frame_b64:       Optional[str] = None    # JPEG 帧 base64（可选）
    headcount_event: Optional[HeadcountEvent] = None   # 人数变化事件


# ─── DB 限频写入控制 ────────────────────────
_last_db_write: float = 0.0
_DB_WRITE_INTERVAL = 5.0   # 每 5 秒写一次 DB

# ─── 内存级最新学生状态（给 /latest 端点用）────
_latest_students: list = []
_latest_push_ts:  float = 0.0

# ─── 识别稳定：滑动窗口投票 ────────────────────
_VOTE_WINDOW  = 5    # 保留最近 N 帧
_VOTE_QUORUM  = 3    # 超过 K 帧出现同一人才确认
from collections import deque as _deque, Counter as _Counter
_vote_window: dict = {}   # {slot_id: deque([name_or_None, ...])}


# ─── 人脸识别模块（OpenCV 直方图，零额外依赖，毫秒级响应）────
from pathlib import Path as _Path
import numpy as _np
import cv2 as _cv2

FACE_DB_DIR = _Path(__file__).parent.parent / "face_db"

# 内存缓存: {student_id: {"name": str, "hist": list[ndarray]}}
_face_hists: dict = {}
_hists_loaded     = False


def _img_to_hists(img: _np.ndarray) -> list:
    """将 BGR 图像转换为 LAB + Hue 多通道直方图特征"""
    img = _cv2.resize(img, (96, 96))
    lab = _cv2.cvtColor(img, _cv2.COLOR_BGR2LAB)
    hsv = _cv2.cvtColor(img, _cv2.COLOR_BGR2HSV)
    hists = []
    for ch in range(3):
        h = _cv2.calcHist([lab], [ch], None, [64], [0, 256])
        hists.append(_cv2.normalize(h, h).flatten())
    h = _cv2.calcHist([hsv], [0], None, [32], [0, 180])
    hists.append(_cv2.normalize(h, h).flatten())
    return hists


def _hist_score(h1: list, h2: list) -> float:
    """多直方图相关系数均值"""
    scores = [float(_cv2.compareHist(a, b, _cv2.HISTCMP_CORREL)) for a, b in zip(h1, h2)]
    return sum(scores) / len(scores)


def _load_face_hists():
    """扫描 face_db，预提取所有学生直方图（支持 jpg/jpeg/png）"""
    global _face_hists, _hists_loaded
    _face_hists = {}
    seen_ids: set = set()
    for pattern in ["*.jpg", "*.jpeg", "*.png"]:
        for f in FACE_DB_DIR.glob(pattern):
            parts = f.stem.split("_", 1)
            if len(parts) != 2:
                continue
            student_id, name = parts
            if student_id in seen_ids:
                continue
            # 兼容中文路径
            img_arr = _np.fromfile(str(f), dtype=_np.uint8)
            img     = _cv2.imdecode(img_arr, _cv2.IMREAD_COLOR)
            if img is None:
                print(f"⚠️ 无法读取照片: {f.name}")
                continue
            _face_hists[student_id] = {"name": name, "hist": _img_to_hists(img)}
            seen_ids.add(student_id)
            print(f"✅ 已加载人脸特征: {name} ({student_id})")
    _hists_loaded = True
    print(f"📚 人脸库加载完成，共 {len(_face_hists)} 名学生")


# 启动时同步加载（直方图提取极快，无需异步）
_load_face_hists()


def _identify_face(face_crop_b64: str) -> Optional[str]:
    """单帧识别：直方图相关系数 > 0.55 即匹配，毫秒级。"""
    if not _face_hists:
        return None
    try:
        img_bytes = base64.b64decode(face_crop_b64)
        img_arr   = _np.frombuffer(img_bytes, _np.uint8)
        query_img = _cv2.imdecode(img_arr, _cv2.IMREAD_COLOR)
        if query_img is None:
            return None
        query_hists = _img_to_hists(query_img)
        best_name  = None
        best_score = 0.55
        for sid, info in _face_hists.items():
            score = _hist_score(query_hists, info["hist"])
            if score > best_score:
                best_score = score
                best_name  = info["name"]
        return best_name
    except Exception:
        return None


def _stable_identify(slot_id: int, face_crop_b64: Optional[str]) -> Optional[str]:
    """
    滑动窗口投票识别：最近 _VOTE_WINDOW 帧内超过 _VOTE_QUORUM 帧
    识别为同一人，才确认输出。防止因单帧噪声导致名字闪烁。
    """
    global _vote_window
    if slot_id not in _vote_window:
        _vote_window[slot_id] = _deque(maxlen=_VOTE_WINDOW)
    single = _identify_face(face_crop_b64) if face_crop_b64 else None
    _vote_window[slot_id].append(single)
    names = [n for n in _vote_window[slot_id] if n is not None]
    if not names:
        return None
    top_name, top_count = _Counter(names).most_common(1)[0]
    return top_name if top_count >= _VOTE_QUORUM else None


# ─── 路由实现 ────────────────────────────────

@router.post("/push")
async def push_snapshot(
    payload: PushPayload,
    db: Session = Depends(get_db)
):
    """
    Jetson 端主动推送（无需登录态）。
    - 视频帧：每次更新内存 + SSE 广播（高频，不写DB）
    - 姿态记录：每 5 秒写一次 DB（防止 SQLite 因高频写入卡死）
    """
    global _latest_frame_bytes, _last_db_write, _latest_students, _latest_push_ts

    # ── 1. 视频帧 → 内存缓存 + SSE 广播（高频，无磁盘 IO）──
    if payload.frame_b64:
        try:
            frame_bytes = base64.b64decode(payload.frame_b64)
            _latest_frame_bytes = frame_bytes
            dead = []
            for q in _sse_subscribers:
                try:
                    q.put_nowait(frame_bytes)
                except asyncio.QueueFull:
                    # 队列持续满说明消费者已断开，纳入待清理列表
                    dead.append(q)
                except Exception:
                    dead.append(q)
            for q in dead:
                try:
                    _sse_subscribers.remove(q)
                except ValueError:
                    pass
        except Exception:
            pass

    # ── 2. 学生状态 → 内存缓存（前端 /latest 轮询用）──
    students_data = []
    for s in payload.students:
        d = s.model_dump()
        # 身份识别：滑动窗口投票（稳定，不闪烁），毫秒级直方图比对
        name = _stable_identify(s.id, s.face_crop)
        if name:
            d["student_name"] = name
        d.pop("face_crop", None)   # 不存入内存/DB
        students_data.append(d)

    _latest_students = students_data
    _latest_push_ts  = _time.time()


    # ── 3. 限频写 DB（5s 一次）──
    now = _time.time()
    record_id = None
    if now - _last_db_write >= _DB_WRITE_INTERVAL:
        _last_db_write = now
        try:
            record = models.PostureRecord(
                course_id=payload.course_id,
                snapshot=students_data,
                jetson_ip=(payload.jetson_ip or JETSON_IP),
                recorded_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            record_id = record.id
        except Exception:
            db.rollback()

    return {"ok": True, "record_id": record_id}


@router.get("/latest")
def get_latest(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """最新一条快照（前端 2s 轮询）。
    优先返回内存中最新推送（含 student_name 识别结果），
    若内存为空则降级读 DB。
    """
    # ── 内存优先（student_name 只存在内存中，DB 没有）──
    if _latest_students:
        from datetime import datetime as _dt
        return {
            "students":    _latest_students,
            "recorded_at": _dt.utcfromtimestamp(_latest_push_ts).isoformat(),
            "jetson_ip":   JETSON_IP,
        }

    # ── 降级到 DB（首次启动/重启后内存为空时）──
    record = (
        db.query(models.PostureRecord)
        .order_by(desc(models.PostureRecord.recorded_at))
        .first()
    )
    if not record:
        return {"students": [], "recorded_at": None, "jetson_ip": JETSON_IP}
    return {
        "students":    record.snapshot,
        "recorded_at": record.recorded_at.isoformat(),
        "jetson_ip":   record.jetson_ip or JETSON_IP,
    }


@router.get("/history")
def get_history(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user=Depends(require_role("teacher", "admin"))
):
    """最近 N 条历史快照（教师/管理员）"""
    records = (
        db.query(models.PostureRecord)
        .order_by(desc(models.PostureRecord.recorded_at))
        .limit(limit)
        .all()
    )
    return [
        {
            "id":          r.id,
            "students":    r.snapshot,
            "recorded_at": r.recorded_at.isoformat(),
            "jetson_ip":   r.jetson_ip,
        }
        for r in records
    ]


@router.get("/stats")
def get_stats(
    current_user=Depends(require_role("teacher", "admin"))
):
    """
    当前课堂实时姿态统计（基于最新一次 push 的内存数据）。
    返回：{attentive: N, drowsy: N, distracted: N, absent: N, total: N, attentive_rate: %}
    """
    counts = {"attentive": 0, "drowsy": 0, "distracted": 0, "absent": 0}
    for student in _latest_students:
        label = student.get("label", "")
        if label in counts:
            counts[label] += 1

    total = sum(counts.values())
    attentive_rate = round(counts["attentive"] / total * 100, 1) if total > 0 else 0

    return {
        **counts,
        "total": total,
        "attentive_rate": attentive_rate,
    }


@router.get("/trends")
def get_trends(
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=5, le=100),
    current_user=Depends(require_role("teacher", "admin"))
):
    """
    历史专注率趋势（最近 N 条 DB 记录，每条聚合专注率）
    用于前端折线图。
    """
    records = (
        db.query(models.PostureRecord)
        .order_by(desc(models.PostureRecord.recorded_at))
        .limit(limit)
        .all()
    )
    result = []
    for r in reversed(records):
        snap = r.snapshot or []
        total = len(snap)
        if total == 0:
            continue
        focused = sum(1 for s in snap if s.get("label") == "attentive")
        result.append({
            "t":    r.recorded_at.strftime("%H:%M:%S"),
            "rate": round(focused / total * 100, 1),
        })
    return result


@router.get("/my-stats")
def get_my_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    学生端：查看自己的姿态历史汇总。
    用登录用户的 full_name 匹配 snapshot 中的 student_name 字段。
    返回：{attentive, drowsy, distracted, absent, total, records:[{t, label}]}
    """
    my_name = getattr(current_user, "full_name", None) or getattr(current_user, "username", "")

    records = (
        db.query(models.PostureRecord)
        .order_by(desc(models.PostureRecord.recorded_at))
        .limit(500)
        .all()
    )

    counts  = {"attentive": 0, "drowsy": 0, "distracted": 0, "absent": 0}
    details = []
    for r in reversed(records):
        for s in (r.snapshot or []):
            if s.get("student_name") == my_name:
                label = s.get("label", "")
                if label in counts:
                    counts[label] += 1
                details.append({
                    "t":     r.recorded_at.strftime("%m-%d %H:%M"),
                    "label": label,
                })
                break

    total = sum(counts.values())
    return {
        **counts,
        "total":          total,
        "attentive_rate": round(counts["attentive"] / total * 100, 1) if total > 0 else 0,
        "records":        details[-50:],
        "my_name":        my_name,
    }


@router.get("/stream-url")
def get_stream_url(
    current_user=Depends(get_current_user)
):
    """返回运动图片轮询地址（替代 MJPEG）"""
    return {
        "video_url":  "/api/v1/posture/latest-frame",
        "status_url": f"http://{JETSON_IP}:{JETSON_PORT}/status",
        "health_url": f"http://{JETSON_IP}:{JETSON_PORT}/health",
    }


@router.get("/latest-frame")
def get_latest_frame():
    """
    返回最新 JPEG 帧（前端 1s 轮询显示）。
    无需登录态。
    """
    if _latest_frame_bytes is None:
        from fastapi import Response as FR
        placeholder = bytes([
            0x47,0x49,0x46,0x38,0x39,0x61,0x01,0x00,0x01,0x00,
            0x80,0x00,0x00,0x00,0x00,0x00,0xff,0xff,0xff,0x21,
            0xf9,0x04,0x00,0x00,0x00,0x00,0x00,0x2c,0x00,0x00,
            0x00,0x00,0x01,0x00,0x01,0x00,0x00,0x02,0x02,0x44,
            0x01,0x00,0x3b
        ])
        return FR(content=placeholder, media_type="image/gif")
    return Response(content=_latest_frame_bytes, media_type="image/jpeg")


@router.get("/frame-stream")
async def frame_stream():
    """
    SSE 端点：Jetson 每次 push 到后端后立刻广播给订阅的前端。
    前端用 EventSource 接收，实现近实时帧更新（无轮询开销）。
    无需登录态（EventSource 不支持自定义 header）。
    """
    q: asyncio.Queue = asyncio.Queue(maxsize=4)
    _sse_subscribers.append(q)

    async def event_gen():
        try:
            if _latest_frame_bytes:
                b64 = base64.b64encode(_latest_frame_bytes).decode()
                yield f"data:{b64}\n\n"
            while True:
                frame_bytes = await asyncio.wait_for(q.get(), timeout=30)
                b64 = base64.b64encode(frame_bytes).decode()
                yield f"data:{b64}\n\n"
        except asyncio.TimeoutError:
            yield "data:timeout\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if q in _sse_subscribers:
                _sse_subscribers.remove(q)

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/stream-proxy")
def stream_proxy():
    """
    MJPEG 流代理：后端从 Jetson 拉取并转发给浏览器。
    解决 iPhone 热点客户端隔离问题。
    """
    jetson_url = f"http://{JETSON_IP}:{JETSON_PORT}/video_feed"
    try:
        upstream = _req.get(jetson_url, stream=True, timeout=5)
        return StreamingResponse(
            upstream.iter_content(chunk_size=4096),
            media_type=upstream.headers.get("Content-Type", "multipart/x-mixed-replace; boundary=frame"),
        )
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail=f"Jetson stream unavailable: {e}")
