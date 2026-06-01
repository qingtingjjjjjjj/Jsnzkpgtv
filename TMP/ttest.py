import re
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# 全局排除关键词定义（用于分类排除）
EXCLUDE_KEYWORDS = ["移动", "联通","私密","少儿","体育","记录","听书","老年","解说","监控","DJ","加入","(内)","韩剧","专用",
                    "动漫","非诚","向前冲","百分百","集结号","好野","行不行","更新","国际影院","专用","上海综合","江西综合",
                    "虎牙","斗鱼","轮播","电台","定制","综艺","电视剧","广场舞","戏曲","风景","游戏","梯","TG","三网2","NBA","直播","四季","内网","测试"]

# 新增：行内容过滤关键词（只要行中包含任意一个关键词，该行即被过滤）
CONTENT_FILTER_KEYWORDS = ["ottiptv","盗源","DJ","P2p","shorturl","更新","group","颜人中","打赏","购买","河南网",
                           "阜阳","野草","少儿","广东体育","\\","iill.top","111.56.90.5","47.92.252.72","合集",
                           "rihou.cc","huya","douyu","iptv.852851.xyz","catvod"]  # 请根据实际需求修改

class TVSourceProcessor:
    def __init__(self):
        self.all_lines = []
        # 配置 Chrome 无头模式
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        self.driver = webdriver.Chrome(options=chrome_options)

    def fetch_url_content(self, url: str):
        """使用 Selenium 获取URL内容"""
        try:
            print(f"获取: {url}")
            self.driver.get(url)
            
            # 等待页面加载完成
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "pre"))
            )
            
            # 获取页面内容
            content = self.driver.find_element(By.TAG_NAME, "pre").text
            
            # 清理并分割行
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            print(f" 成功: {len(lines)} 行")
            return lines
        except Exception as e:
            print(f" 失败: {e}")
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
        """
        删除genre行，并按URL去重。
        同时根据 CONTENT_FILTER_KEYWORDS 过滤掉包含指定关键词的行。
        """
        result = []
        seen_urls = set()
        filtered_count = 0
        for line in lines:
            if "#genre#" in line:
                continue
            if not line.strip():
                continue
            
            # 新增：内容过滤（不区分大小写）
            line_lower = line.lower()
            if any(keyword.lower() in line_lower for keyword in CONTENT_FILTER_KEYWORDS):
                filtered_count += 1
                continue  # 过滤掉该行
            
            # 提取URL去重
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
        # 只使用指定的URL
        urls = [
        "https://raw.githubusercontent.com/Jsnzkpg/Jsnzkpg/Jsnzkpg/Jsnzkpg1",
        "https://raw.githubusercontent.com/fafa002/yf2025/refs/heads/main/yiyifafa.txt",
        "https://raw.githubusercontent.com/zxmlxw520/5566/refs/heads/main/sfzb2.txt",
        ]
        print(f"源URL: {len(urls)}个")
        
        # 1. 获取内容
        if not self.fetch_multiple_urls(urls):
            print("无内容可处理")
            self.driver.quit()
            return False
        
        # 2. 排除处理
        filtered = self.remove_excluded_sections()
        if not filtered:
            print("排除后无内容")
            self.driver.quit()
            return False
        
        # 3. 去重及内容过滤处理
        final = self.remove_genre_lines_and_deduplicate(filtered)
        if not final:
            print("去重后无内容")
            self.driver.quit()
            return False
        
        # 4. 保存文件
        if self.save_to_file(final, "ttest.txt", "test,#genre#"):
            print("处理完成")
            self.driver.quit()
            return True
        else:
            self.driver.quit()
            return False

def main():
    """主函数"""
    processor = TVSourceProcessor()
    success = processor.process()
    
    # 退出状态码
    if success and os.path.exists("ttest.txt"): 
        print(f"文件位置: {os.path.abspath('ttest.txt')}")
        sys.exit(0)
    else:
        print("处理失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
