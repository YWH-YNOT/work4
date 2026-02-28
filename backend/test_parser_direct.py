"""
直接调用 TimetableParser.parse_image() 的单元诊断脚本
目的：排查 FastAPI 解析器为何始终返回 3 条 Mock 数据
"""
import os
import sys
import logging

# 配置详细日志到控制台
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

# 加载 .env
from dotenv import load_dotenv
load_dotenv()

print("=== TimetableParser 直接诊断 ===")
print(f"API_KEY: {os.getenv('OPENAI_API_KEY', '未设定')[:12]}...")
print(f"VISION_MODEL: {os.getenv('VISION_MODEL', '未设定')}")
print(f"API_BASE: {os.getenv('OPENAI_API_BASE', '未设定')}")

# ==========================================
# 加载真实课表图片
# ==========================================
IMAGE_PATH = r"C:\Users\a2248\.gemini\antigravity\brain\334d4902-b98c-4cd5-b1d7-a84aa66240af\media__1771820882105.jpg"
print(f"\n图片路径: {IMAGE_PATH}")
with open(IMAGE_PATH, 'rb') as f:
    image_bytes = f.read()
print(f"图片大小: {len(image_bytes)} bytes ({len(image_bytes)//1024} KB)")

# ==========================================
# 直接调用 TimetableParser
# ==========================================
print("\n--- 调用 TimetableParser.parse_image() ---")
from services.timetable_parser import TimetableParser

parser = TimetableParser()
print(f"Parser 配置: model={parser.model}, api_base={parser.api_base}")

try:
    result = parser.parse_image(image_bytes, content_type="image/jpeg")
    print(f"\n✅ 解析完成！共 {len(result)} 条记录")
    for i, item in enumerate(result):
        print(f"  [{i+1}] {item.get('course_name')} | 周{item.get('day_of_week')} 第{item.get('start_session')}-{item.get('end_session')}节 | {item.get('teacher_name')}")
except Exception as e:
    print(f"\n❌ 解析异常: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
