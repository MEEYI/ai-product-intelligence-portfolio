# ============================================================
# Website Utilities
# ============================================================

from urllib.parse import urlparse


def normalize_website_domain(website: str):
    """
    把不同格式的网站统一成 domain。

    例如：

    https://www.example.com/
    http://example.com
    www.example.com
    example.com

    最终都变成：

    example.com
    """

    if not website:
        return None

    # 删除前后空格
    website = website.strip()

    # 没写协议时，临时补上 https://
    if not website.startswith(("http://", "https://")):
        website = "https://" + website

    # 提取 domain
    domain = urlparse(website).netloc.lower()

    # 去掉 www.
    if domain.startswith("www."):
        domain = domain[4:]

    return domain
