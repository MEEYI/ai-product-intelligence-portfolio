# ============================================================
# Product Analyzer Service
# ============================================================

import base64
import json
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# Environment
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class ProductAnalyzerConfigurationError(RuntimeError):
    """AI 分析所需的本地配置尚未完成。"""


def get_openai_model() -> str:
    """Require an explicit API model instead of assuming account availability."""
    model = (os.getenv("OPENAI_MODEL") or "").strip()
    if not model:
        raise ProductAnalyzerConfigurationError("Configure OPENAI_MODEL before using AI features.")
    return model


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise ProductAnalyzerConfigurationError(
            "未配置 OPENAI_API_KEY。请在项目根目录的 .env 文件中填写 API 密钥，"
            "然后重启后端。"
        )

    return OpenAI(api_key=api_key)


# ============================================================
# Convert Local Image to Data URL
# ============================================================

def local_image_to_data_url(image_path: str) -> str:
    """
    把本地图片转换成 OpenAI 可以直接读取的 Data URL。

    例如：

    uploads/product_references/xxx.jpg

    会被转换成：

    data:image/jpeg;base64,xxxxx...

    这样 OpenAI 不需要访问我们的本地文件地址，
    图片本身会直接随 API 请求发送过去。
    """

    # --------------------------------------------------------
    # 1. 检查图片是否真的存在
    # --------------------------------------------------------

    # Resolve both paths to prevent traversal and links escaping the upload area.
    # Relative paths are project-relative, independent of the process directory.
    try:
        project_root = PROJECT_ROOT.resolve()
        upload_root = project_root / "uploads" / "product_references"
        resolved_upload_root = upload_root.resolve()
        if resolved_upload_root != upload_root:
            raise ValueError("Product upload directory must not redirect outside its location.")
        candidate = Path(image_path)
        image_file_path = (candidate if candidate.is_absolute() else project_root / candidate).resolve()
        image_file_path.relative_to(resolved_upload_root)
    except (OSError, RuntimeError, ValueError):
        raise ValueError("Product image must be inside the product upload directory.") from None

    if not image_file_path.is_file():
        raise FileNotFoundError("Product image is unavailable.")

    # --------------------------------------------------------
    # 2. 根据扩展名判断图片类型
    # --------------------------------------------------------

    extension = image_file_path.suffix.lower()

    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    mime_type = mime_types.get(extension)

    if mime_type is None:
        raise ValueError("Unsupported product image format.")

    # --------------------------------------------------------
    # 3. 读取图片
    # --------------------------------------------------------

    try:
        image_bytes = image_file_path.read_bytes()
    except OSError:
        raise OSError("Product image could not be read.") from None

    # --------------------------------------------------------
    # 4. 图片二进制 → Base64 文本
    # --------------------------------------------------------

    encoded_image = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    # --------------------------------------------------------
    # 5. 组成 Data URL
    # --------------------------------------------------------

    return (
        f"data:{mime_type};base64,{encoded_image}"
    )


# ============================================================
# Analyze Product
# ============================================================

def analyze_product(
    product_name: str,
    product_type: str | None,
    image_url: str | None,
):
    """
    使用 AI 分析一件产品。

    V1 输入：
    - 产品名称
    - 已知产品类型
    - 产品图片

    图片目前可以是：
    - 项目 uploads/product_references/ 内的本地图片路径
    - 用户提供的 HTTP/HTTPS 图片 URL（由上游获取；本服务不验证远程资源的安全性）

    V1 输出：
    - 结构化 Python dict
    """

    model = get_openai_model()
    client = get_openai_client()

    # --------------------------------------------------------
    # 1. 给 AI 的分析要求
    # --------------------------------------------------------

    prompt = f"""
You are a professional headwear product analyst.

Analyze the product based on the supplied product information
and image.

Product name:
{product_name}

Existing product type:
{product_type or "unknown"}

Only describe characteristics that are visible or strongly supported.

Do not invent details.

Return ONLY valid JSON.

Use exactly these fields:

{{
    "product_type": null,
    "crown_structure": null,
    "visor_shape": null,
    "main_color": null,
    "secondary_color": null,
    "logo_treatment": null,
    "logo_position": null,
    "material_language": null,
    "style_tags": null,
    "confidence": null
}}

Examples:

product_type:
trucker, 6_panel, 5_panel, bucket, boonie, beanie

crown_structure:
structured, unstructured, unknown

visor_shape:
curved, flat, short, wide, unknown

logo_treatment:
embroidery, patch, print, applique, metal_logo, none, unknown

logo_position:
front_center, front_left, side, all_over, none, unknown

material_language:
short comma-separated description

style_tags:
short comma-separated style tags

confidence:
number between 0 and 1

If something cannot be determined, use null.
"""

    # --------------------------------------------------------
    # 2. 准备模型输入
    # --------------------------------------------------------

    content = [
        {
            "type": "input_text",
            "text": prompt,
        }
    ]

    # --------------------------------------------------------
    # 3. 如果有图片，判断是本地图片还是公网 URL
    # --------------------------------------------------------

    if image_url:

        # Remote URLs are forwarded to the provider. Local path containment does
        # not validate a remote URL's content, ownership, or privacy.
        if image_url.startswith(
            ("http://", "https://")
        ):
            image_input = image_url

        # 否则按照本地图片处理
        else:
            image_input = local_image_to_data_url(
                image_url
            )

        content.append(
            {
                "type": "input_image",
                "image_url": image_input,
            }
        )

    # --------------------------------------------------------
    # 4. 调用 OpenAI
    # --------------------------------------------------------

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "user",
                "content": content,
            }
        ],
        store=False,
    )

    # --------------------------------------------------------
    # 5. 获取模型返回文本
    # --------------------------------------------------------

    result_text = response.output_text

    # --------------------------------------------------------
    # 6. JSON → Python dict
    # --------------------------------------------------------

    result = json.loads(result_text)

    return result
