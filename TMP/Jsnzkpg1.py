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
            print(f"正在获取: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            
            content = response.text
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            print(f"  -> 获取成功: 共 {len(lines)} 行")
            return lines
        except Exception as e:
            print(f"  -> 获取失败: {e}")
            return []

    def fetch_multiple_urls(self, urls: list):
        """获取多个URL内容"""
        self.all_lines = []
        for url in urls:
            lines = self.fetch_url_content(url)
            if lines:
                self.all_lines.extend(lines)
        print(f"所有源总计: {len(self.all_lines)} 行")
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
                    print(f"  -> 排除分组: {line}")
                else:
                    in_excluded_section = False
                    result.append(line)
            elif not in_excluded_section:
                result.append(line)
        print(f"排除指定区域后剩余: {len(result)} 行")
        return result

    def remove_genre_lines_and_deduplicate(self, lines: list):
        """处理M3U数据，提取频道名和URL并转换为标准TXT格式"""
        result = []
        seen_urls = set()
        filtered_count = 0
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # 1. 跳过分组信息行
            if "#genre#" in line:
                i += 1
                continue
            
            if not line.strip():
                i += 1
                continue
            
            # 2. 过滤垃圾关键词（增加了打印具体匹配到的关键词）
            line_lower = line.lower()
            matched_keyword = None
            for keyword in CONTENT_FILTER_KEYWORDS:
                if keyword.lower() in line_lower:
                    matched_keyword = keyword
                    break
            
            if matched_keyword:
                filtered_count += 1
                # 如果过滤行数较少，可以打印出来看看；如果太多可以注释掉这行
                if filtered_count <= 10: 
                    print(f"  -> 因包含关键词 '{matched_keyword}' 被过滤: {line[:50]}...")
                i += 1
                continue
            
            # 3. 提取 URL 和 频道名
            url_match = re.search(r'(https?://[^\s,]+)', line)
            
            # 情况A：当前行就是 URL
            if url_match:
                url = url_match.group(1)
                if url not in seen_urls:
                    seen_urls.add(url)
                    channel_name = "未知频道"
                    
                    if i > 0 and lines[i-1].startswith('#EXTINF'):
                        if ',' in lines[i-1]:
                            channel_name = lines[i-1].split(',')[-1].strip()
                    
                    result.append(f"{channel_name},{url}")
                i += 1
            
            # 情况B：当前行是 #EXTINF，看下一行
            elif line.startswith('#EXTINF'):
                channel_name = line.split(',')[-1].strip() if ',' in line else "未知频道"
                if i + 1 < len(lines):
                    next_line = lines[i+1]
                    next_url_match = re.search(r'(https?://[^\s,]+)', next_line)
                    if next_url_match:
                        url = next_url_match.group(1)
                        if url not in seen_urls:
                            seen_urls.add(url)
                            result.append(f"{channel_name},{url}")
                        i += 2
                        continue
                i += 1
            else:
                i += 1
        
        print(f"内容过滤: 共 {filtered_count} 行被过滤")
        print(f"去重并转换格式后: 共 {len(result)} 行")
        return result

    def save_to_file(self, lines: list, filename: str, first_line: str):
        """保存到文件"""
        try:
            content = [first_line] + lines
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(content))
            file_size = os.path.getsize(filename)
            print(f"成功保存文件: {filename} (共 {len(content)} 行, 大小 {file_size} 字节)")
            return True
        except Exception as e:
            print(f"保存文件失败: {e}")
            return False

    def process(self):
        """主处理流程"""
        print("========== 开始处理直播源 ==========")
        
        urls = [
            "https://raw.githubusercontent.com/Jsnzkpg/Jsnzkpg/refs/heads/Jsnzkpg/Jsnzkpg1.m3u"
        ]
        
        try:
            if not self.fetch_multiple_urls(urls):
                print("警告: 没有获取到任何内容，将生成空文件。")
                # 即使没获取到内容，也生成一个空文件，方便排查
                self.save_to_file([], "Jsnzkpg1.txt", "Jsnzkpg1,#genre#")
                return False
            
            filtered = self.remove_excluded_sections()
            if not filtered:
                print("警告: 排除区域后没有剩余内容，将生成空文件。")
                self.save_to_file([], "Jsnzkpg1.txt", "Jsnzkpg1,#genre#")
                return False
            
            final = self.remove_genre_lines_and_deduplicate(filtered)
            
            if self.save_to_file(final, "Jsnzkpg1.txt", "Jsnzkpg1,#genre#"):
                print("========== 处理完成 ==========")
                return True
            else:
                return False
                
        except Exception as e:
            print(f"!!!!!!!!!! 程序运行发生严重错误: {e} !!!!!!!!!!")
            import traceback
            traceback.print_exc()
            return False


def main():
    processor = TVSourceProcessor()
    success = processor.process()
    
    if os.path.exists("Jsnzkpg1.txt"):
        print(f"最终文件绝对路径: {os.path.abspath('Jsnzkpg1.txt')}")
        
    if success:
        sys.exit(0)
    else:
        # 即使失败也返回0，防止 GitHub Actions 报错停止后续 git push 步骤
        # 这样即使没抓到数据，也会把空的或上次的 txt 推送到仓库
        print("程序处理未达预期，但将继续尝试推送文件...")
        sys.exit(0)


if __name__ == "__main__":
    main()
