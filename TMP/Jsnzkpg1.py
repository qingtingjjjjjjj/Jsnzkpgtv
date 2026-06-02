import re
import os
import sys
import requests

# 全局排除关键词定义（用于分类排除）
EXCLUDE_KEYWORDS = [
    "猫TV", "赛评", "赛事", "全集", "华山论剑", "三国粤", "大时代", 
    "流星花园", "还珠格格", "甄嬛", "大地恩情", "粤经典剧", 
    "射雕英雄", "神雕侠侣", "欣赏音乐", "凡人修仙传", "轮播","频晴","频陆"
]

# 行内容过滤关键词（已更新你提供的新关键词）
CONTENT_FILTER_KEYWORDS = [
    "盗源", "DJ", "p3p", "shorturl", "更新", "group", 
    "颜人中", "打赏", "购买", "河南网", "阜阳", "野草", "少儿", 
    "广东体育", "\\", "iill.top","凡人修仙传","woshinibaba","cfss.cc",
    "新增球帝直播", "蜘蛛直播更换域名", "咪咕", "咪视频", "百视通", "刷新就是新内容"
]


class TVSourceProcessor:
    def __init__(self):
        self.all_lines = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def fetch_url_content(self, url: str):
        """使用 requests 获取URL内容"""
        try:
            print(f"获取: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            # 强制指定编码为 utf-8，解决乱码问题
            response.encoding = 'utf-8'
            
            content = response.text
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            print(f"  成功: {len(lines)} 行")
            return lines
        except Exception as e:
            print(f"  失败: {e}")
            return []

    def fetch_multiple_urls(self, urls: list):
        """获取多个URL内容"""
        self.all_lines = []
        for url in urls:
            lines = self.fetch_url_content(url)
            if lines:
                self.all_lines.extend(lines)
        print(f"总计: {len(self.all_lines)} 行")
        return len(self.all_lines) > 0

    def remove_excluded_sections(self):
        """排除指定区域"""
        if not self.all_lines:
            return []
        result = []
        in_excluded_section = False
        for line in self.all_lines:
            if "#genre#" in line:
                if any(keyword in line for keyword in EXCLUDE_KEYWORDS):
                    in_excluded_section = True
                else:
                    in_excluded_section = False
                    result.append(line)
            elif not in_excluded_section:
                result.append(line)
        print(f"排除后: {len(result)} 行")
        return result

    def remove_genre_lines_and_deduplicate(self, lines: list):
        """处理M3U数据，提取频道名和URL并转换为标准TXT格式"""
        result = []
        seen_urls = set()
        filtered_count = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 1. 跳过分组信息行，不再记录分组
            if "#genre#" in line:
                i += 1
                continue
            
            if not line.strip():
                i += 1
                continue
            
            # 2. 过滤垃圾关键词
            line_lower = line.lower()
            if any(keyword.lower() in line_lower for keyword in CONTENT_FILTER_KEYWORDS):
                filtered_count += 1
                i += 1
                continue
            
            # 3. 核心修改：尝试提取 URL 和 频道名
            url_match = re.search(r'(https?://[^\s,]+)', line)
            
            # 情况A：当前行就是 URL（M3U 标准格式的第二行）
            if url_match:
                url = url_match.group(1)
                if url not in seen_urls:
                    seen_urls.add(url)
                    channel_name = "未知频道"
                    
                    # 检查上一行是否是 #EXTINF，如果是，从中提取频道名
                    if i > 0 and lines[i-1].startswith('#EXTINF'):
                        # 提取逗号后面的内容作为频道名
                        if ',' in lines[i-1]:
                            channel_name = lines[i-1].split(',')[-1].strip()
                    
                    # 转换为标准的 TXT 格式：频道名,URL (去掉了前面的分组)
                    result.append(f"{channel_name},{url}")
                i += 1
            
            # 情况B：当前行是 #EXTINF，但没找到 URL，需要看下一行
            elif line.startswith('#EXTINF'):
                channel_name = line.split(',')[-1].strip() if ',' in line else "未知频道"
                # 检查下一行是否存在且是 URL
                if i + 1 < len(lines):
                    next_line = lines[i+1]
                    next_url_match = re.search(r'(https?://[^\s,]+)', next_line)
                    if next_url_match:
                        url = next_url_match.group(1)
                        if url not in seen_urls:
                            seen_urls.add(url)
                            result.append(f"{channel_name},{url}")
                        i += 2 # 跳两行，因为已经处理了下一行
                        continue
                i += 1
            else:
                i += 1
        
        print(f"内容过滤: {filtered_count} 行被过滤")
        print(f"去重并转换格式后: {len(result)} 行")
        return result

    def save_to_file(self, lines: list, filename: str, first_line: str):
        """保存到文件"""
        try:
            content = [first_line] + lines
            # 写入文件时也强制使用 utf-8 编码
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            file_size = os.path.getsize(filename)
            print(f"保存: {filename} ({len(content)}行, {file_size}字节)")
            return True
        except Exception as e:
            print(f"保存失败: {e}")
            return False

    def process(self):
        """主处理流程"""
        print("开始处理直播源")
        
        urls = [
            "https://raw.githubusercontent.com/Jsnzkpg/Jsnzkpg/refs/heads/Jsnzkpg/Jsnzkpg1.m3u"
        ]
        print(f"源URL: {len(urls)}个")
        
        if not self.fetch_multiple_urls(urls):
            print("无内容可处理")
            return False
        
        filtered = self.remove_excluded_sections()
        if not filtered:
            print("排除后无内容")
            return False
        
        final = self.remove_genre_lines_and_deduplicate(filtered)
        if not final:
            print("去重后无内容")
            return False
        
        # 修改输出文件的第一行标题为 Jsnzkpg1,#genre#
        if self.save_to_file(final, "Jsnzkpg1.txt", "Jsnzkpg1,#genre#"):
            print("处理完成")
            return True
        return False


def main():
    processor = TVSourceProcessor()
    success = processor.process()
    
    if success and os.path.exists("Jsnzkpg1.txt"):
        print(f"文件位置: {os.path.abspath('Jsnzkpg1.txt')}")
        sys.exit(0)
    else:
        print("处理失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
