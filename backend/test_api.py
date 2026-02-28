import os
import requests
import base64
from dotenv import load_dotenv

# Load from backend .env
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
API_BASE = os.getenv("OPENAI_API_BASE")
MODEL = os.getenv("VISION_MODEL")

print(f"=== 步骤 1: 检查配置 ===")
print(f"Using API Base: {API_BASE}")
print(f"Using Model: {MODEL}")
if not API_KEY or API_KEY == "YOUR_SILICONFLOW_API_KEY_HERE":
    print("错误: 未检测到有效的 API 密钥！请确认在 .env 中填写了真实的 sk-...")
    exit(1)
print("🔑 API 密钥已读取 (前8位):", API_KEY[:8], "...")

def test_text_chat():
    print(f"\n=== 步骤 2: 测试存活性 (基础对话) ===")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "你好，回复我是谁。"}],
        "max_tokens": 50
    }
    
    try:
        response = requests.post(f"{API_BASE}/chat/completions", headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ 基础对话成功! 平台响应:", response.json()["choices"][0]["message"]["content"])
            return True
        else:
            print(f"❌ 基础对话失败! 状态码: {response.status_code}")
            print(f"响应详情: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 请求发生异常: {str(e)}")
        return False

def test_vision_chat():
    print(f"\n=== 步骤 3: 测试 Vision 视觉能力 (多模态) ===")
    
    # 动态生成一张真实能够被 PIL 解析并存为 PNG 的微小图片字节块并将其 Base64 编码
    # 因为上一次直接写死的 base64 存在 bad header checksum 的问题，导致 SiliconFlow 底层 PIL 抛出异常 500 或 400
    import io
    from PIL import Image
    
    try:
        # Create a tiny 100x100 RGB image (Qwen3-VL demands > 28px)
        img = Image.new('RGB', (100, 100), color = 'red')
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr = img_byte_arr.getvalue()
        encoded_string = base64.b64encode(img_byte_arr).decode('utf-8')
    except Exception as e:
        print("图片生成失败:", e)
        return
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}},
                    {"type": "text", "text": "描述这张图是什么颜色。"}
                ]
            }
        ],
        "max_tokens": 100
    }
    
    try:
        print("正在发送包含图片的请求，请稍候...")
        response = requests.post(f"{API_BASE}/chat/completions", headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            print("✅ 视觉能力测试成功! 平台响应:", response.json()["choices"][0]["message"]["content"])
        else:
            print(f"❌ 视觉能力失败! 模型可能不支持图片。状态码: {response.status_code}")
            print(f"错误详情: {response.text}")
    except Exception as e:
        print(f"❌ 请求发生异常: {str(e)}")

if __name__ == "__main__":
    if test_text_chat():
        test_vision_chat()
