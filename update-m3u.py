import requests
import re
import os
from datetime import datetime, timedelta, timezone

# 配置 URL 和替换规则
URLS = [
    "https://raw.githubusercontent.com/fanmingming/live/refs/heads/main/tv/m3u/ipv6.m3u",
    "https://raw.githubusercontent.com/suxuang/myIPTV/refs/heads/main/ipv6.m3u"
]

# 替换 group-title 规则
REMAP_GROUPS = {
    "IHOT频道": "二哈频道",
    "NewTV频道": "全新视野",
    "埋堆堆": "埋堆剧集",
    "港澳台AKTV": "港台电视",
    "港澳台频道": "港台频道",
    "电视剧轮播": "电视轮播"
}

# Telegram 推送配置
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

# 北京时区
BEIJING_TZ = timezone(timedelta(hours=8))


def clean_extinf(line):
    """
    清理 #EXTINF 标签中重复的字段
    """
    # 移除重复字段
    cleaned_line = re.sub(r'(tvg-id="[^"]*")[^#]*\1', r'\1', line)
    cleaned_line = re.sub(r'(tvg-name="[^"]*")[^#]*\1', r'\1', cleaned_line)
    cleaned_line = re.sub(r'(tvg-logo="[^"]*")[^#]*\1', r'\1', cleaned_line)
    cleaned_line = re.sub(r'(group-title="[^"]*")[^#]*\1', r'\1', cleaned_line)
    return cleaned_line


def fetch_and_process_m3u():
    """
    下载并处理 m3u 文件
    """
    combined_content = "#EXTM3U\n"
    for idx, url in enumerate(URLS):
        response = requests.get(url)
        response.raise_for_status()
        content = response.text

        # 对每一行清理重复字段
        cleaned_lines = []
        for line in content.splitlines():
            if line.startswith("#EXTINF"):
                line = clean_extinf(line)
            cleaned_lines.append(line)
        
        # 替换 group-title 内容
        cleaned_content = "\n".join(cleaned_lines)
        for old_group, new_group in REMAP_GROUPS.items():
            if idx == 1:  # 只对第二个链接内容替换
                cleaned_content = cleaned_content.replace(f'group-title="{old_group}"', f'group-title="{new_group}"')

        combined_content += cleaned_content + "\n"

    return combined_content


def save_to_file(content, filename="live.m3u"):
    """
    保存处理后的内容到文件
    """
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)


def send_telegram_message(message):
    """
    使用 Telegram 推送消息
    """
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("Telegram 推送未配置，跳过推送")
        return
    
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("Telegram 推送成功")
    except Exception as e:
        print(f"Telegram 推送失败: {e}")


def get_beijing_time():
    """
    获取当前北京时间
    """
    return datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")


def main():
    """
    主函数
    """
    print("开始处理 m3u 文件...")
    try:
        content = fetch_and_process_m3u()
        save_to_file(content)
        print("m3u 文件处理完成，保存为 live.m3u")
        beijing_time = get_beijing_time()
        send_telegram_message(f"m3u 文件已更新，并成功生成 live.m3u\n推送时间：{beijing_time}")
    except Exception as e:
        print(f"处理失败: {e}")
        beijing_time = get_beijing_time()
        send_telegram_message(f"m3u 文件处理失败: {e}\n推送时间：{beijing_time}")


if __name__ == "__main__":
    main()
