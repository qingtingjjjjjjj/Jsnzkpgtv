import requests
from urllib.parse import urlparse

def convert_m3u_to_txt(urls, exclude_chars=None, output_file="TMP/temp.txt"):
    """
    将指定URL列表中的M3U内容转换为TXT格式并保存到文件
    
    Args:
        urls (list): M3U文件的URL列表
        exclude_chars (list): 需要排除的字符列表，包含这些字符的行会被过滤掉
        output_file (str): 输出文件路径，默认为"TMP/hw.txt"
    """
    output = []
    group_set = set()
    
    # 默认排除字符为空列表
    if exclude_chars is None:
        exclude_chars = []
    
    for url in urls:
        try:
            # 获取M3U文件内容
            response = requests.get(url)
            response.raise_for_status()  # 检查请求是否成功
            content = response.text
            lines = content.split('\n')
            
            for i in range(len(lines)):
                line = lines[i].strip()
                if line.startswith('#EXTINF'):
                    # 提取分组信息
                    import re
                    group_match = re.search(r'group-title="([^"]+)"', line)
                    name_start = line.rfind(',') + 1
                    name = line[name_start:] if name_start < len(line) else ""
                    
                    group_name = group_match.group(1) if group_match else '未分类'
                    
                    # 检查是否需要排除
                    should_exclude = False
                    for char in exclude_chars:
                        if char in name or char in group_name:
                            should_exclude = True
                            break
                    
                    if should_exclude:
                        continue  # 跳过需要排除的行
                    
                    # 添加分组（去重）
                    if group_name not in group_set:
                        output.append(f"{group_name},#genre#")
                        group_set.add(group_name)
                    
                    # 处理下一行的URL
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and next_line.startswith('http'):
                            # 检查URL是否需要排除
                            url_should_exclude = False
                            for char in exclude_chars:
                                if char in next_line:
                                    url_should_exclude = True
                                    break
                            
                            if not url_should_exclude:
                                output.append(f"{name},{next_line}")
                            i += 1  # 跳过已处理的URL行
                            
        except Exception as e:
            print(f"处理URL {url} 时出错: {e}")
    
    # 确保输出目录存在
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output))
    
    print(f"转换完成，结果已保存到 {output_file}")

# 示例用法
if __name__ == "__main__":
    # 替换为你需要处理的M3U URL列表
    m3u_urls = [
        #"https://raw.githubusercontent.com/xJEYDAin/iptv-scraper/refs/heads/master/output/all_merged.m3u",   
        #"https://xoxo.cn.mt/Lonely.m3u",
        "https://github.com/joaquinito2036-rgb/iptvfast/blob/main/output/all.m3u",
    ]
    
    # 需要排除的字符列表
    exclude_chars = ["wns.live","cloudfront.net","stevosure123","visionplus.id"]
    
    convert_m3u_to_txt(m3u_urls, exclude_chars)
