"""
独立视觉API诊断测试脚本
1. 直接加载真实课表截图（来自 artifacts 或用户指定路径）
2. 测试原始尺寸 vs 压缩到 1280px 宽两种方案
3. 使用完整版课表解析 Prompt
4. 打印 Qwen3-VL 的原始返回字符串供诊断
"""
import os
import base64
import json
import io
import requests
from dotenv import load_dotenv

# 加载 .env 配置
load_dotenv()

API_KEY    = os.getenv("OPENAI_API_KEY")
API_BASE   = os.getenv("OPENAI_API_BASE", "https://api.siliconflow.cn/v1")
MODEL      = os.getenv("VISION_MODEL", "Qwen/Qwen3-VL-32B-Instruct")

# ============================================================
# 配置：指定要测试的图片路径（可以是任意 PNG/JPG 文件）
# ============================================================
IMAGE_PATH = r"C:\Users\a2248\.gemini\antigravity\brain\334d4902-b98c-4cd5-b1d7-a84aa66240af\media__1771820882105.jpg"
RESIZE_WIDTH = 1280   # 压缩到此宽度（px），设为 None 则不压缩

PROMPT = """
你是一个精通教务系统排课逻辑的解析专家。请极其仔细地阅读这张大学的网格课表截图。

【你的任务】
遍历星期一到星期日的每一列，以及从第1节到最后一节课的每一行。
提取图片中出现的所有课程，并组装成一个 JSON 数组。

【极度重要：解析规则】
1. 必须提取图片里的【所有】课程！不要漏掉边缘的、周末的、晚上的，也不要只提取前几个！只要格子里有字，就必须提取。
2. 如果同一门课在不同的星期几或不同的节次有多次上课安排，请将其拆分为多个独立的 JSON 对象！

每个 JSON 对象必须严格包含以下字段（类型要求极严）：
- course_name (字符串): 课程名称 (例如 "数字逻辑B")
- course_code (字符串): 课程代码数字串 (例如 "2523114"，如果没有则为 "")
- teacher_name (字符串): 教师姓名或多位教师名字 (例如 "李翔", "胡鸿志")
- weeks (字符串): 上课周次字符串 (例如 "1-12周" 或 "1,3,5周")
- day_of_week (自然整数): 星期几 (星期一填1，星期天填7)
- start_session (自然整数): 开始节次 (例如该课占据第 5-6 节，则 start_session 为 5)
- end_session (自然整数): 结束节次 (例如该课占据第 5-6 节，则 end_session 为 6)
- location (字符串): 上课地点/教室 (例如 "花江校区 11B103")

只返回纯 JSON 数组 `[{}, {}, ...]`，不要加 ```json 标记，绝对不要包含任何其它废话描述！
"""

print(f"\n=== 视觉 API 诊断测试 ===")
print(f"模型: {MODEL}")
print(f"API:  {API_BASE}")
print(f"图片: {IMAGE_PATH}")
print(f"KEY:  {API_KEY[:12] if API_KEY else '未设置'}...")

def load_and_encode_image(path, resize_width=None):
    from PIL import Image
    img = Image.open(path).convert("RGB")
    orig_size = img.size
    
    if resize_width and img.width > resize_width:
        ratio = resize_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((resize_width, new_height), Image.LANCZOS)
        print(f"  [缩放] {orig_size} → {img.size}")
    else:
        print(f"  [原始] {orig_size} (不缩放)")
    
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode("utf-8"), "image/jpeg"

def call_vision_api(encoded_img, mime_type, label):
    print(f"\n--- 测试: {label} ---")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded_img}"}},
                {"type": "text", "text": PROMPT}
            ]
        }],
        "max_tokens": 4000
    }
    
    print("  发送请求中（可能需要 20-60 秒）...")
    try:
        resp = requests.post(f"{API_BASE}/chat/completions", headers=headers, json=payload, timeout=120)
        print(f"  状态码: {resp.status_code}")
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            print(f"\n=== 模型原始返回 ({label}) ===")
            print(content)
            print(f"=== 字符数: {len(content)} ===\n")
            # 尝试解析 JSON
            try:
                raw = content.strip()
                if raw.startswith("```json"):
                    raw = raw[7:]
                if raw.endswith("```"):
                    raw = raw[:-3]
                data = json.loads(raw.strip())
                print(f"✅ 解析成功！共识别到 {len(data)} 条课程记录")
                return data
            except json.JSONDecodeError as e:
                print(f"⚠️  模型返回了文本但不是合法 JSON: {e}")
        else:
            print(f"  ❌ 请求失败: {resp.text}")
    except Exception as e:
        print(f"  ❌ 网络异常: {e}")
    return None

if __name__ == "__main__":
    # 测试 1：压缩版本（更快、更省 token）
    enc, mime = load_and_encode_image(IMAGE_PATH, resize_width=RESIZE_WIDTH)
    call_vision_api(enc, mime, f"压缩至 {RESIZE_WIDTH}px 宽")
    
    # 测试 2：原始尺寸（如果上面失败了）
    enc2, mime2 = load_and_encode_image(IMAGE_PATH, resize_width=None)
    call_vision_api(enc2, mime2, "原始分辨率")
