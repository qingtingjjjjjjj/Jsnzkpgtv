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

# 行内容过滤关键词
CONTENT_FILTER_KEYWORDS = [
    "盗源", "DJ", "p3p", "shorturl", "更新", "group", 
    "颜人中", "打赏", "购买", "河南网", "阜阳", "野草", "少儿", 
    "广东体育", "\\", "iill.top","凡人修仙传","woshinibaba","cfss.cc"
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
            response.encoding = response.apparent_encoding
            
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
        """删除genre行，按URL去重，并过滤内容关键词"""
        result = []
        seen_urls = set()
        filtered_count = 0
        
        for line in lines:
            if "#genre#" in line:
                continue
            if not line.strip():
                continue
            
            line_lower = line.lower()
            if any(keyword.lower() in line_lower for keyword in CONTENT_FILTER_KEYWORDS):
                filtered_count += 1
                continue
            
            url_match = re.search(r'(https?://[^\s,]+)', line)
            if url_match:
                url = url_match.group(1)
                if url not in seen_urls:
                    seen_urls.add(url)
                    result.append(line)
            else:
                result.append(line)
        
        print(f"内容过滤: {filtered_count} 行被过滤")
        print(f"去重后: {len(result)} 行")
        return result

    def save_to_file(self, lines: list, filename: str, first_line: str):
        """保存到文件"""
        try:
            content = [first_line] + lines
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
            #"http://119.91.7.169:35789/dszb/dszb.txt",
            "http://rihou.cc:555/gggg.nzk"
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
        
        if self.save_to_file(final, "rihou.txt", "rihou,#genre#"):
            print("处理完成")
            return True
        return False


def main():
    processor = TVSourceProcessor()
    success = processor.process()
    
    if success and os.path.exists("rihou.txt"):
        print(f"文件位置: {os.path.abspath('rihou.txt')}")
        sys.exit(0)
    else:
        print("处理失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
