import os
import base64
import json
import logging
import re
from typing import List, Dict, Any, Optional
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Few-shot 示例：给模型展示"如何理解课表格子"
# ─────────────────────────────────────────────
FEW_SHOT_EXAMPLE = """
【示例课表格子内的文字（一个格子）】
数字逻辑B(2523114)
李翔
花江校区11B103
1-12周[双]

【对应的正确 JSON】
{
  "course_name": "数字逻辑B",
  "course_code": "2523114",
  "teacher_name": "李翔",
  "location": "花江校区11B103",
  "weeks": "1-12周双",
  "day_of_week": 2,
  "start_session": 3,
  "end_session": 4
}

【说明】
- course_code 括号里的数字，没有则填 ""
- weeks 把 [单]、[双]、[全] 等括号内容保留，例如 "1-16周" "3-15周单"
- day_of_week: 星期一=1, 星期二=2 ... 星期日=7
- start_session/end_session: 该格子所在的节次行范围（如第3-4节课，start=3 end=4）
"""

MAIN_PROMPT = """\
你是专门解析**中国高校教务网格课表截图**的 OCR 专家。

请仔细观察这张课表图片，注意以下结构：
- 最左列通常是节次（第1节、第2节...），或者按节次行分割
- 最顶行是星期（星期一~星期日，或一~日）
- 每个网格格子对应"哪天/哪节"的课程信息

""" + FEW_SHOT_EXAMPLE + """

【你的任务】
遍历课表中每一个有内容的格子，提取所有课程，组成 JSON 数组。

【重要规则】
1. 绝对不要遗漏任何课程，包括周末课、晚上课、边角格子
2. 同一门课如果占据多个独立格子（不同星期），必须分开为多个 JSON 对象
3. 如果一个格子内包含多门不同课程信息（用斜线分隔），拆分为多个对象
4. day_of_week 必须是 1-7 的整数，不能是中文
5. start_session 和 end_session 必须是正整数，start <= end，不能超过 11
6. 如果课程时间跨度不清楚，默认 end_session = start_session + 1
7. weeks 字段保留原始字符串（如 "1-16周" "3-15周单"），不要转为数组

每个 JSON 对象必须包含以下字段：
- course_name (string): 课程名称
- course_code (string): 课程代号（括号内数字），没有则 ""
- teacher_name (string): 教师姓名，没有则 "未知"
- weeks (string): 上课周次，没有则 ""
- day_of_week (integer 1-7): 星期几
- start_session (integer 1-11): 开始节次
- end_session (integer 1-11): 结束节次
- location (string): 教室地点，没有则 ""

只输出纯 JSON 数组，格式：[{}, {}, ...]
禁止添加任何说明文字、```json 标记或其他内容！
"""

# 简化版 Prompt（第一次失败时重试用）
FALLBACK_PROMPT = """\
请读取这张课表图片，提取所有课程，返回 JSON 数组。
每项必须有：course_name(string), course_code(string), teacher_name(string), weeks(string), day_of_week(int 1-7), start_session(int), end_session(int), location(string)。
只返回 JSON 数组，不含任何其他文字。
"""


class TimetableParser:
    """
    使用 Vision LLM 解析课表图片，返回结构化的课程数据。
    """

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model = os.getenv("VISION_MODEL", "Qwen/Qwen2-VL-72B-Instruct")
        logger.info(
            f"TimetableParser ready: model={self.model}, "
            f"key={'ok' if self.api_key else 'MISSING'}"
        )

    # ────────────────────────────────────────
    # 图片预处理：压缩大图 & 提升质量
    # ────────────────────────────────────────
    def _preprocess_image(self, image_bytes: bytes) -> bytes:
        """
        1. 确保最短边 >= 800px（太小则放大，Vision 模型需要足够分辨率）
        2. 确保不超过 2000px（太大则缩小，避免 token 超限）
        3. 适度提升对比度，让文字更清晰
        4. 统一输出为 JPEG，控制文件大小
        """
        try:
            img = Image.open(BytesIO(image_bytes)).convert("RGB")
            w, h = img.size

            # 1. 缩放：短边至少 800px，长边最多 2000px
            min_side = min(w, h)
            max_side = max(w, h)

            if min_side < 800:
                scale = 800 / min_side
                img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
                w, h = img.size
                logger.info(f"Image upscaled to {w}x{h}")

            if max_side > 2000:
                scale = 2000 / max(w, h)
                img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
                logger.info(f"Image downscaled to {int(w*scale)}x{int(h*scale)}")

            # 2. 提升对比度 1.2 倍，让表格线和文字更清晰
            img = ImageEnhance.Contrast(img).enhance(1.2)

            # 3. 轻微锐化，减少压缩模糊
            img = img.filter(ImageFilter.SHARPEN)

            # 4. 输出 JPEG（quality=92 在质量和大小之间取平衡）
            output = BytesIO()
            img.save(output, format="JPEG", quality=92, optimize=True)
            result = output.getvalue()
            logger.info(
                f"Preprocessed image: {len(image_bytes)//1024}KB -> {len(result)//1024}KB"
            )
            return result
        except Exception as e:
            logger.warning(f"Image preprocess failed: {e}, using original bytes")
            return image_bytes

    def _encode_image(self, image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode("utf-8")

    # ────────────────────────────────────────
    # 调用 Vision API
    # ────────────────────────────────────────
    def _call_vision_api(self, base64_image: str, prompt: str) -> str:
        """调用 OpenAI 兼容的 Vision API，返回模型响应文本"""
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": "high",   # 启用高细节模式
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            "max_tokens": 6000,   # 提升上限，防止课程多时截断
            "temperature": 0,     # 稳定输出，减少随机性
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        resp = requests.post(
            f"{self.api_base}/chat/completions",
            headers=headers,
            json=payload,
            timeout=180,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()

    # ────────────────────────────────────────
    # JSON 提取（兼容各种 LLM 输出格式）
    # ────────────────────────────────────────
    @staticmethod
    def _extract_json(raw: str) -> Optional[List[Dict]]:
        """从 LLM 响应中提取 JSON 数组，兼容 markdown code block 等格式"""
        # 1. 去掉 ```json ... ``` 包装
        raw = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`")

        # 2. 尝试直接解析
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                # LLM 有时返回 {"courses": [...]}
                for v in data.values():
                    if isinstance(v, list):
                        return v
        except json.JSONDecodeError:
            pass

        # 3. 用正则提取第一个 [...] 块
        match = re.search(r"\[.*?\]", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    # ────────────────────────────────────────
    # 字段后处理：合法性校验 & 自动纠错
    # ────────────────────────────────────────
    @staticmethod
    def _sanitize_item(item: Dict) -> Optional[Dict]:
        """
        对单条课程数据进行后处理：
        - 去掉 course_name 为空的记录
        - 强制 day_of_week 在 1-7 之间
        - 强制 start_session/end_session 在 1-11 之间
        - 修正 start > end 的情况
        - 统一字符串字段类型
        """
        name = str(item.get("course_name", "")).strip()
        if not name:
            return None

        def safe_int(val, default: int, lo: int, hi: int) -> int:
            try:
                v = int(val)
                return max(lo, min(hi, v))
            except (TypeError, ValueError):
                return default

        dow = safe_int(item.get("day_of_week"), 1, 1, 7)
        ss = safe_int(item.get("start_session"), 1, 1, 11)
        es = safe_int(item.get("end_session"), ss + 1, 1, 11)
        if ss > es:
            ss, es = es, ss  # 交换

        return {
            "course_name": name,
            "course_code": str(item.get("course_code", "")).strip(),
            "teacher_name": str(item.get("teacher_name", "未知")).strip() or "未知",
            "weeks": str(item.get("weeks", "")).strip(),
            "day_of_week": dow,
            "start_session": ss,
            "end_session": es,
            "location": str(item.get("location", "")).strip(),
        }

    # ────────────────────────────────────────
    # 公开接口
    # ────────────────────────────────────────
    def parse_image(self, image_bytes: bytes, content_type: str = "image/jpeg") -> List[Dict[str, Any]]:
        """
        解析课表截图，返回结构化课程列表。
        策略：主 Prompt → 解析失败时自动用简化 Prompt 重试一次。
        """
        if not self.api_key:
            logger.warning("No API key — returning mock data")
            return self._get_mock_data()

        # 图片预处理
        processed = self._preprocess_image(image_bytes)
        b64 = self._encode_image(processed)

        # 第一次尝试（主 Prompt）
        try:
            raw = self._call_vision_api(b64, MAIN_PROMPT)
            logger.info(f"Vision API raw response (first 600 chars): {raw[:600]}")
            parsed = self._extract_json(raw)
            if parsed:
                result = [self._sanitize_item(x) for x in parsed]
                result = [x for x in result if x]  # 过滤 None
                if result:
                    logger.info(f"Parsed {len(result)} courses (main prompt)")
                    return result
            logger.warning("Main prompt returned no valid data, retrying with fallback prompt...")
        except Exception as e:
            logger.warning(f"Main prompt failed: {e}, retrying with fallback...")

        # 第二次尝试（简化 Prompt，更容易让模型产出格式正确的 JSON）
        try:
            raw = self._call_vision_api(b64, FALLBACK_PROMPT)
            logger.info(f"Fallback raw response (first 600 chars): {raw[:600]}")
            parsed = self._extract_json(raw)
            if parsed:
                result = [self._sanitize_item(x) for x in parsed]
                result = [x for x in result if x]
                if result:
                    logger.info(f"Parsed {len(result)} courses (fallback prompt)")
                    return result
        except Exception as e:
            logger.error(f"Fallback prompt also failed: {e}")

        return []

    # ────────────────────────────────────────
    # Mock 数据（无 API key 时测试用）
    # ────────────────────────────────────────
    def _get_mock_data(self) -> List[Dict[str, Any]]:
        return [
            {
                "course_name": "数字逻辑B",
                "course_code": "2523114",
                "teacher_name": "李翔",
                "weeks": "1-12周",
                "day_of_week": 2,
                "start_session": 3,
                "end_session": 4,
                "location": "花江校区11B103",
            },
            {
                "course_name": "信号与系统分析",
                "course_code": "2521378",
                "teacher_name": "苏海涛",
                "weeks": "1-15周",
                "day_of_week": 1,
                "start_session": 3,
                "end_session": 4,
                "location": "花江校区17509",
            },
            {
                "course_name": "跨文化交际",
                "course_code": "2522700",
                "teacher_name": "温露",
                "weeks": "1-16周",
                "day_of_week": 5,
                "start_session": 3,
                "end_session": 4,
                "location": "花江校区17413研",
            },
        ]
