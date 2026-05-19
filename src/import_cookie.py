"""Cookie导入工具 - 从浏览器复制Cookie字符串并转换为config.json格式"""
import json
import sys
from pathlib import Path

CONFIG_FILE = Path(__file__).parent.parent / "config.json"


def parse_cookie_string(cookie_str: str) -> dict:
    """将浏览器复制的Cookie字符串解析为字典

    输入格式: "name1=value1; name2=value2; ..."
    """
    cookies = {}
    for item in cookie_str.split(";"):
        item = item.strip()
        if "=" in item:
            name, value = item.split("=", 1)
            cookies[name.strip()] = value.strip()
    return cookies


def save_cookies(cookies: dict):
    """保存Cookie到config.json"""
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    config["cookie"] = cookies

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"[OK] 已保存 {len(cookies)} 个Cookie到 config.json")


def main():
    print("=" * 50)
    print("  抖音Cookie导入工具")
    print("=" * 50)
    print()
    print("操作步骤:")
    print("  1. 用Chrome打开 https://www.douyin.com 并登录")
    print("  2. 按 F12 打开开发者工具")
    print("  3. 切换到 Network(网络) 标签")
    print("  4. 刷新页面，点击任意一个请求")
    print("  5. 在 Request Headers 中找到 Cookie: ")
    print("  6. 复制整行Cookie值（不含 'Cookie: ' 前缀）")
    print("  7. 粘贴到下面（右键粘贴，Ctrl+V可能不生效）")
    print()
    print("或者直接在地址栏输入以下内容回车，复制弹出的内容:")
    print("  javascript:document.cookie")
    print()
    print("-" * 50)

    cookie_str = input("请粘贴Cookie: ").strip()

    if not cookie_str:
        print("[错误] Cookie为空")
        return

    cookies = parse_cookie_string(cookie_str)

    if len(cookies) < 3:
        print(f"[警告] 只解析到 {len(cookies)} 个Cookie，可能复制不完整")
        print(f"解析结果: {list(cookies.keys())}")

    # 验证关键Cookie
    key_names = ["sessionid", "ttwid", "passport_csrf_token"]
    found = [k for k in key_names if k in cookies]
    if found:
        print(f"[OK] 找到关键Cookie: {', '.join(found)}")
    else:
        print("[警告] 未找到关键Cookie (sessionid/ttwid/passport_csrf_token)")

    save_cookies(cookies)
    print()
    print("现在可以运行 python main.py 使用工具了")


if __name__ == "__main__":
    main()
