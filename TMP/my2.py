#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBox直播接口解密工具
用于获取和解析直播接口内容

使用方法:
    python tv_api_decrypt.py

功能:
    1. 自动使用正确的User-Agent请求接口
    2. 解析返回的JSON配置数据
    3. 提取直播源、解析接口、站点信息等
    4. 下载直播源内容并保存到my3.txt
    5. 支持关键词过滤，排除特定#genre#分组
"""

import requests
import json
import re
from datetime import datetime
from urllib.parse import unquote

# 禁用SSL警告
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ==================== 全局配置 ====================

# 目标接口地址列表（可配置多个）
# 程序会依次获取每个接口的直播源内容并合并
API_URLS = [
    "http://tv.nxog.top/m/",
    # 可以添加更多接口地址...
    # "http://tv.nxog.top/api.php?mz=xb&id=2&b=欧歌",
    # "http://other-api.com/config.json",
]

# 排除关键词列表（不区分大小写）
# 含有这些关键词的 #genre# 分组将被完全过滤
EXCLUDE_KEYWORDS = [
    "音乐",
    "金曲",
    "DJ",
    "黄色",
    "激情",
    "私拍",
    # 可以继续添加更多关键词...
]

# 输出文件名
OUTPUT_FILE = "my3.txt"


class TVBoxAPI:
    """TVBox API 解密器"""
    
    def __init__(self):
        # TVBox常用的User-Agent列表
        self.user_agents = [
            'okhttp/3.12.1',
            'Dalvik/2.1.0 (Linux; U; Android 10; MI 9 Build/QKQ1.190825.002)',
            'TVBox',
        ]
        self.session = requests.Session()
        self.session.verify = False
        self.data = None
        
    def fetch_api(self, url, params=None):
        """
        获取API数据
        使用特定的User-Agent来获取JSON格式的响应
        """
        headers = {
            'User-Agent': self.user_agents[0],
            'Accept': '*/*',
            'Accept-Encoding': 'gzip',
        }
        
        try:
            response = self.session.get(url, headers=headers, params=params, timeout=15)
            response.encoding = 'utf-8'
            return response.text
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return None
    
    def fetch_live_content(self, url):
        """
        获取直播源内容
        """
        headers = {
            'User-Agent': self.user_agents[0],
            'Accept': '*/*',
        }
        
        try:
            response = self.session.get(url, headers=headers, timeout=60)
            # 尝试多种编码
            for encoding in ['utf-8', 'gbk', 'gb2312', 'utf-16']:
                try:
                    response.encoding = encoding
                    content = response.text
                    # 检查是否解码成功（没有乱码）
                    if '频道' in content or '#genre#' in content or '#EXTM3U' in content:
                        return content
                except:
                    continue
            response.encoding = 'utf-8'
            return response.text
        except requests.RequestException as e:
            print(f"获取直播源内容失败: {e}")
            return None
    
    def parse_json(self, text):
        """
        解析JSON数据
        处理可能包含注释的JSON
        """
        # 移除开头的空白和控制字符
        text = text.strip()
        
        # 移除JavaScript风格的注释
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            if '//' in line and not line.strip().startswith('"'):
                in_string = False
                result = []
                for i, char in enumerate(line):
                    if char == '"' and (i == 0 or line[i-1] != '\\'):
                        in_string = not in_string
                    if char == '/' and i < len(line) - 1 and line[i+1] == '/' and not in_string:
                        break
                    result.append(char)
                cleaned_lines.append(''.join(result).rstrip())
            else:
                cleaned_lines.append(line.rstrip())
        
        text = '\n'.join(cleaned_lines)
        
        try:
            self.data = json.loads(text)
            return True
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            error_pos = e.pos if hasattr(e, 'pos') else 0
            print(f"出错位置附近: {text[max(0, error_pos-50):error_pos+50]}")
            return False
    
    def extract_info(self):
        """提取关键信息"""
        if not self.data:
            return None
            
        info = {
            '基本信息': {
                '壁纸': self.data.get('wallpaper', ''),
                'Logo': self.data.get('logo', ''),
                'Spider插件': self.data.get('spider', ''),
                '警告文本': self.data.get('warningText', ''),
            },
            '直播源数量': len(self.data.get('lives', [])),
            '直播源列表': self.data.get('lives', []),
            '解析接口数量': len(self.data.get('parses', [])),
            '解析接口列表': self.data.get('parses', []),
            '站点数量': len(self.data.get('sites', [])),
            '站点列表': self.data.get('sites', []),
            '代理规则': self.data.get('proxy', []),
            '域名映射': self.data.get('hosts', []),
        }
        return info
    
    def get_live_sources(self):
        """获取直播源地址列表"""
        if not self.data:
            return []
        
        lives = self.data.get('lives', [])
        sources = []
        for live in lives:
            source = {
                '名称': live.get('name', '未知'),
                '类型': live.get('type', 0),
                '地址': live.get('url', ''),
                'EPG': live.get('epg', ''),
                'Logo模板': live.get('logo', ''),
                '播放器类型': live.get('playerType', 1),
                'UA': live.get('ua', ''),
            }
            sources.append(source)
        return sources
    
    def get_parse_urls(self):
        """获取解析接口列表"""
        if not self.data:
            return []
        
        parses = self.data.get('parses', [])
        urls = []
        for parse in parses:
            urls.append({
                '名称': parse.get('name', ''),
                '类型': parse.get('type', 0),
                '地址': parse.get('url', ''),
                '扩展配置': parse.get('ext', {}),
            })
        return urls
    
    def get_spider_info(self):
        """获取Spider插件信息"""
        spider = self.data.get('spider', '')
        if not spider:
            return None
        
        parts = spider.split(';')
        return {
            '下载地址': parts[0] if len(parts) > 0 else '',
            '校验类型': parts[1] if len(parts) > 1 else '',
            '校验值': parts[2] if len(parts) > 2 else '',
        }


def filter_live_content(content, exclude_keywords):
    """
    过滤直播源内容
    1. 根据排除关键词过滤掉含有这些关键词的#genre#分组
    2. 去掉所有#genre#行，在开头添加固定的"gt,#genre#"
    
    参数:
        content: 直播源原始内容
        exclude_keywords: 排除关键词列表
    
    返回:
        过滤后的内容
    """
    if not content:
        return ""
    
    lines = content.split('\n')
    filtered_lines = []
    skip_mode = False
    skipped_count = 0
    total_genres = 0
    kept_channels = 0
    
    for line in lines:
        line_stripped = line.strip()
        
        # 检查是否是 #genre# 行
        if '#genre#' in line_stripped:
            total_genres += 1
            
            # 检查是否包含排除关键词
            should_skip = False
            for keyword in exclude_keywords:
                if keyword.lower() in line_stripped.lower():
                    should_skip = True
                    skipped_count += 1
                    print(f"    [过滤] 分组: {line_stripped} (关键词: {keyword})")
                    break
            
            # 更新skip_mode状态
            skip_mode = should_skip
            
            # 不再保留#genre#行
        else:
            # 非分组行，根据skip_mode决定是否保留
            if not skip_mode:
                # 只保留非空行和包含逗号的频道行
                if line_stripped and ',' in line_stripped:
                    filtered_lines.append(line)
                    kept_channels += 1
    
    print(f"\n    分组统计: 总计 {total_genres} 个, 已过滤 {skipped_count} 个")
    print(f"    频道数量: 保留 {kept_channels} 个")
    
    # 在开头添加固定的 #genre# 行
    result = ["gt,#genre#"]
    result.extend(filtered_lines)
    
    return '\n'.join(result)


def parse_m3u_to_txt(content):
    """
    将M3U格式转换为TXT格式
    TXT格式: 频道名,URL
    """
    if not content:
        return ""
    
    lines = content.split('\n')
    result = []
    current_channel = None
    current_url = None
    
    for line in lines:
        line = line.strip()
        
        if line.startswith('#EXTINF:'):
            # 提取频道名称
            match = re.search(r',(.+)$', line)
            if match:
                current_channel = match.group(1).strip()
                # 提取分组信息
                group_match = re.search(r'group-title="([^"]*)"', line)
                if group_match:
                    group = group_match.group(1)
                    # 检查分组是否需要过滤
                    result.append(f"{group},#genre#")
        elif line and not line.startswith('#'):
            if current_channel:
                result.append(f"{current_channel},{line}")
                current_channel = None
    
    return '\n'.join(result)


def main():
    """主函数"""
    print("=" * 60)
    print("TVBox直播接口解密工具")
    print("=" * 60)
    print()
    
    # 显示配置信息
    print(f"[配置] 接口数量: {len(API_URLS)}")
    for i, url in enumerate(API_URLS, 1):
        print(f"        接口{i}: {url}")
    print(f"[配置] 排除关键词: {EXCLUDE_KEYWORDS}")
    print(f"[配置] 输出文件: {OUTPUT_FILE}")
    print()
    
    all_live_content = []
    total_channels = 0
    
    # 遍历所有接口地址
    for api_index, api_url in enumerate(API_URLS, 1):
        print("=" * 60)
        print(f"[接口 {api_index}/{len(API_URLS)}] {api_url}")
        print("=" * 60)
        
        # 创建API实例
        api = TVBoxAPI()
        
        print(f"\n[1] 正在请求接口...")
        print(f"    使用 User-Agent: {api.user_agents[0]}")
        
        # 获取数据
        text = api.fetch_api(api_url)
        if not text:
            print("    获取数据失败，跳过此接口")
            continue
        
        print(f"[2] 获取成功! 数据长度: {len(text)} 字节")
        
        # 解析JSON
        print("[3] 正在解析JSON数据...")
        if not api.parse_json(text):
            print("    解析失败，跳过此接口")
            continue
        
        print("    解析成功!")
        
        # 提取信息
        info = api.extract_info()
        print(f"[4] 直播源数量: {info['直播源数量']}, 解析接口: {info['解析接口数量']}, 站点: {info['站点数量']}")
        
        # 获取直播源内容
        print("[5] 获取直播源内容...")
        print("-" * 40)
        
        live_sources = api.get_live_sources()
        
        for i, source in enumerate(live_sources, 1):
            name = source.get('名称', '未知')
            url = source.get('地址', '')
            
            if not url:
                continue
            
            print(f"\n  正在获取: {name}")
            print(f"  地址: {url}")
            
            content = api.fetch_live_content(url)
            
            if content:
                print(f"  获取成功! 内容长度: {len(content)} 字节")
                
                # 如果是M3U格式，转换为TXT格式
                if content.strip().startswith('#EXTM3U'):
                    print("  检测到M3U格式，正在转换为TXT格式...")
                    content = parse_m3u_to_txt(content)
                
                all_live_content.append(content)
            else:
                print(f"  获取失败!")
        
        print()
    
    # 检查是否有内容
    if not all_live_content:
        print("没有获取到任何直播源内容!")
        return
    
    # 合并所有直播源内容
    print("=" * 60)
    print("[处理] 合并并过滤内容...")
    print("=" * 60)
    
    combined_content = '\n\n'.join(all_live_content)
    
    print(f"\n[6] 正在过滤内容...")
    print("-" * 40)
    
    # 过滤内容
    filtered_content = filter_live_content(combined_content, EXCLUDE_KEYWORDS)
    
    # 保存到文件
    print()
    print(f"[7] 保存到 {OUTPUT_FILE}...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(filtered_content)
    
    # 统计信息
    lines = filtered_content.split('\n')
    channel_count = len([l for l in lines if ',' in l and '#genre#' not in l])
    
    print(f"    保存成功!")
    print(f"    文件大小: {len(filtered_content)} 字节")
    print(f"    频道数量: {channel_count}")
    
    print()
    print("=" * 60)
    print("处理完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
