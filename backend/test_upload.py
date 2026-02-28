"""
直接 POST 真实课表图片到 FastAPI 端点，验证 load_dotenv 修复是否生效
"""
import requests

IMAGE_PATH = r"test_timetable.jpg"
ENDPOINT = "http://localhost:8002/api/v1/timetable/import"

print(f"测试端点: {ENDPOINT}")
print(f"图片: {IMAGE_PATH}")
print("上传中（模型解析需要 30-120 秒，请稍候）...")

with open(IMAGE_PATH, 'rb') as f:
    files = {'file': ('timetable.jpg', f, 'image/jpeg')}
    try:
        res = requests.post(ENDPOINT, files=files, timeout=180)
        print(f"\n状态码: {res.status_code}")
        print(f"响应体: {res.text}")
    except requests.Timeout:
        print("❌ 超时 (180s)，模型没有返回结果")
    except Exception as e:
        print(f"❌ 错误: {e}")
