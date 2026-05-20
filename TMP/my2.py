#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from curl_cffi import requests

API_URLS = ["https://ds65.tv1288.xyz"]
EXCLUDE_KEYWORDS = ["音乐", "金曲", "DJ", "黄色", "激情", "私拍"]
OUTPUT_FILE = "my3.txt"

def fetch_m3u(url):
    """使用 curl_cffi 模拟 okhttp 指纹"""
    try:
        # impersonate="okhttp" 会完全模拟 okhttp 的 TLS 握手和请求头
        response = requests.get(url, impersonate="okhttp", timeout=30, verify=False)
        if response.status_code == 200:
            text = response.text
            if "#EXTM3U" in text or "#EXTINF" in text:
                print(f"✓ 成功获取 M3U，长度 {len(text)} 字节")
                return text
            else:
                print(f"✗ 返回非 M3U 内容，前200字符: {text[:200]}")
                return None
        else:
            print(f"✗ HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"✗ 请求异常: {e}")
        return None

def parse_m3u_to_txt(m3u_content):
    """M3U 转 TXT 格式"""
    if not m3u_content:
        return ""
    lines = m3u_content.splitlines()
    result = []
    current_group = None
    current_name = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#EXTM3U") or line.startswith("#EXT-X-") or line.startswith("//"):
            continue
        if line.startswith("#EXTINF"):
            match = re.search(r',([^,]+)$', line)
            if match:
                current_name = match.group(1).strip()
            group_match = re.search(r'group-title="([^"]*)"', line)
            if group_match:
                current_group = group_match.group(1).strip()
            continue
        if line and not line.startswith("#") and current_name:
            if current_group:
                group_line = f"{current_group},#genre#"
                if not result or result[-1] != group_line:
                    result.append(group_line)
            result.append(f"{current_name},{line}")
            current_name = None

    # 去重分组标记
    seen = set()
    unique_result = []
    for line in result:
        if line.endswith(",#genre#"):
            if line in seen:
                continue
            seen.add(line)
        unique_result.append(line)
    return "\n".join(unique_result)

def filter_by_group(txt_content, exclude_keywords):
    """根据分组关键词过滤"""
    if not txt_content:
        return ""
    lines = txt_content.splitlines()
    filtered = []
    skip_group = False
    for line in lines:
        if line.endswith(",#genre#"):
            group_name = line[:-7]
            if any(kw.lower() in group_name.lower() for kw in exclude_keywords):
                skip_group = True
            else:
                skip_group = False
                filtered.append(line)
        else:
            if not skip_group:
                filtered.append(line)
    return "\n".join(filtered)

def main():
    print("TVBox M3U 获取工具 (模拟 okhttp 指纹)")
    all_txt_parts = []

    for url in API_URLS:
        print(f"\n处理: {url}")
        m3u = fetch_m3u(url)
        if not m3u:
            print("跳过")
            continue
        txt = parse_m3u_to_txt(m3u)
        if txt:
            all_txt_parts.append(txt)
            print(f"转换完成，{len(txt.splitlines())} 行")

    if not all_txt_parts:
        print("未获取到有效内容")
        return

    combined = "\n\n".join(all_txt_parts)
    filtered = filter_by_group(combined, EXCLUDE_KEYWORDS)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(filtered)

    print(f"\n✅ 完成！保存至 {OUTPUT_FILE}")
    print(f"   总行数: {len(filtered.splitlines())}")

if __name__ == "__main__":
    main()
