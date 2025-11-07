#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bilibili视频下载和字幕提取工具
支持：
1. 获取视频信息
2. 下载视频
3. 提取并保存字幕（支持中文、英文等多语言）
4. Cookie认证（获取字幕需要）
"""

import os
import sys
import json
import requests
import re
from typing import Optional, Dict, List


class BilibiliDownloader:
    def __init__(self, cookies: Optional[Dict[str, str]] = None):
        """
        初始化下载器

        Args:
            cookies: B站cookie字典，包含 SESSDATA, bili_jct, buvid3
                    如果为None，将尝试从环境变量或配置文件读取
        """
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com'
        }

        # 加载cookies
        self.cookies = cookies or self._load_cookies()

        if self.cookies:
            print("[INFO] 已加载Cookie凭证，可以访问需要登录的字幕")
        else:
            print("[WARNING] 未找到Cookie凭证，某些视频的字幕可能无法获取")
            print("[INFO] 请参考 COOKIE_GUIDE.md 获取Cookie配置方法")

    def _load_cookies(self) -> Optional[Dict[str, str]]:
        """从环境变量或配置文件加载cookies"""
        cookies = {}

        # 方法1: 从环境变量读取
        sessdata = os.environ.get('BILIBILI_SESSDATA')
        bili_jct = os.environ.get('BILIBILI_BILI_JCT')
        buvid3 = os.environ.get('BILIBILI_BUVID3')

        if sessdata:
            cookies['SESSDATA'] = sessdata
            if bili_jct:
                cookies['bili_jct'] = bili_jct
            if buvid3:
                cookies['buvid3'] = buvid3
            return cookies

        # 方法2: 从配置文件读取（优先从工作区目录）
        workspace_cookie = os.path.abspath(os.path.join(
            os.path.dirname(__file__), '..', '..', '..', '..',
            'bilibili-workspace', 'bilibili_cookies.json'
        ))

        # 尝试多个位置（向后兼容）
        possible_paths = [
            workspace_cookie,  # 工作区目录（优先）
            'bilibili_cookies.json',
            os.path.join(os.path.dirname(__file__), 'bilibili_cookies.json'),
            os.path.join(os.path.dirname(__file__), '..', 'bilibili_cookies.json')
        ]

        for config_file in possible_paths:
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        cookies = json.load(f)
                        if cookies.get('SESSDATA'):
                            return cookies
                except Exception as e:
                    print(f"[WARNING] 读取配置文件失败 ({config_file}): {e}")

        return None

    def set_cookies(self, sessdata: str, bili_jct: str = '', buvid3: str = ''):
        """
        手动设置cookies

        Args:
            sessdata: SESSDATA cookie值（必需）
            bili_jct: bili_jct cookie值（可选）
            buvid3: buvid3 cookie值（可选）
        """
        self.cookies = {
            'SESSDATA': sessdata,
        }
        if bili_jct:
            self.cookies['bili_jct'] = bili_jct
        if buvid3:
            self.cookies['buvid3'] = buvid3

        print("[OK] Cookie已设置")

    def extract_bvid(self, url: str) -> Optional[str]:
        """从URL中提取BV号"""
        patterns = [
            r'BV[a-zA-Z0-9]+',
            r'bilibili\.com/video/(BV[a-zA-Z0-9]+)',
            r'b23\.tv/(\w+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                bvid = match.group(1) if '(' in pattern else match.group(0)
                if bvid.startswith('BV'):
                    return bvid
                else:
                    # 处理短链接，需要请求获取真实链接
                    return self._resolve_short_url(url)
        return None

    def _resolve_short_url(self, url: str) -> Optional[str]:
        """解析短链接"""
        try:
            response = requests.get(url, headers=self.headers, allow_redirects=True)
            real_url = response.url
            return self.extract_bvid(real_url)
        except Exception as e:
            print(f"解析短链接失败: {e}")
            return None

    def get_video_info(self, bvid: str) -> Optional[Dict]:
        """获取视频信息"""
        api_url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        try:
            response = requests.get(api_url, headers=self.headers, cookies=self.cookies)
            data = response.json()

            if data['code'] == 0:
                video_data = data['data']
                info = {
                    'title': video_data['title'],
                    'author': video_data['owner']['name'],
                    'duration': video_data['duration'],
                    'desc': video_data['desc'],
                    'cid': video_data['cid'],
                    'bvid': bvid,
                    'aid': video_data['aid']
                }
                return info
            else:
                print(f"获取视频信息失败: {data['message']}")
                return None
        except Exception as e:
            print(f"请求视频信息出错: {e}")
            return None

    def _download_subtitle_with_retry(self, subtitle_url: str, max_retries: int = 10) -> Optional[Dict]:
        """
        带重试机制下载字幕内容
        B站AI字幕API有bug，同一个URL可能返回不同视频的字幕
        通过多次尝试和验证来获取正确的字幕
        """
        import hashlib
        import time

        subtitle_contents = []  # 存储每次下载的字幕内容

        for attempt in range(max_retries):
            try:
                # 每次请求之间稍微延迟，避免请求过快
                if attempt > 0:
                    time.sleep(0.5)

                response = requests.get(subtitle_url, headers=self.headers)
                subtitle_data = response.json()

                body = subtitle_data.get('body', [])
                if not body:
                    continue

                # 计算前10条字幕内容的哈希值作为指纹
                first_items = body[:min(10, len(body))]
                content_fingerprint = '|||'.join([item['content'] for item in first_items])
                content_hash = hashlib.md5(content_fingerprint.encode()).hexdigest()

                subtitle_contents.append({
                    'data': subtitle_data,
                    'hash': content_hash,
                    'preview': [item['content'] for item in first_items[:3]]
                })

                # 如果已经有3次或以上，检查是否有重复
                if len(subtitle_contents) >= 3:
                    # 统计每个哈希值出现的次数
                    hash_counts = {}
                    for item in subtitle_contents:
                        hash_val = item['hash']
                        if hash_val not in hash_counts:
                            hash_counts[hash_val] = []
                        hash_counts[hash_val].append(item)

                    # 如果某个哈希值出现3次或以上，认为是正确的
                    for hash_val, items in hash_counts.items():
                        if len(items) >= 3:
                            print(f"  [OK] 验证成功 (尝试{attempt + 1}次，获得{len(items)}次相同内容)")
                            print(f"  内容预览: {items[0]['preview'][:3]}")
                            return items[0]['data']

            except Exception as e:
                print(f"  [WARN] 下载字幕失败 (尝试{attempt + 1}/{max_retries}): {e}")
                continue

        # 如果所有尝试都没有找到重复的，返回出现最多的那个
        if subtitle_contents:
            hash_counts = {}
            for item in subtitle_contents:
                hash_val = item['hash']
                if hash_val not in hash_counts:
                    hash_counts[hash_val] = []
                hash_counts[hash_val].append(item)

            # 选择出现次数最多的
            most_common = max(hash_counts.values(), key=len)
            print(f"  [INFO] 无法完全验证，使用出现最多的版本 (出现{len(most_common)}次)")
            print(f"  预览: {most_common[0]['preview']}")
            return most_common[0]['data']

        return None

    def get_subtitles(self, bvid: str, cid: int, max_api_retries: int = 5) -> Optional[List[Dict]]:
        """
        获取视频字幕（带重试验证机制）

        Args:
            bvid: 视频BV号
            cid: 视频CID
            max_api_retries: 最大API请求重试次数（每次请求会获得新的subtitle_url）
        """
        import hashlib
        import time

        # 使用新版player/wbi/v2接口 (2025最新)
        # 注意：虽然路径包含wbi，但实际不需要WBI签名参数，只需要Cookie
        subtitle_api = f"https://api.bilibili.com/x/player/wbi/v2?bvid={bvid}&cid={cid}"

        # 存储所有尝试的结果
        all_attempts = []

        print(f"  正在尝试获取字幕 (最多尝试{max_api_retries}次API请求)...")

        for api_attempt in range(max_api_retries):
            try:
                if api_attempt > 0:
                    time.sleep(1)  # API请求之间延迟

                response = requests.get(subtitle_api, headers=self.headers, cookies=self.cookies)
                data = response.json()

                if data['code'] != 0:
                    print(f"  [WARN] API请求失败: {data.get('message', '未知错误')}")
                    continue

                player_data = data.get('data', {})

                # 注意：need_login_subtitle标志可能为True，但仍然可能返回字幕数据
                # 2025年的API行为：即使标志为True，如果Cookie有效，subtitle字段仍会包含数据
                # 所以我们不再直接返回None，而是尝试获取字幕
                subtitles_info = player_data.get('subtitle', {}).get('subtitles', [])

                if not subtitles_info:
                    if player_data.get('subtitle', {}).get('ai_subtitle'):
                        ai_subtitle = player_data['subtitle']['ai_subtitle']
                        subtitles_info = [ai_subtitle]
                    else:
                        print("该视频没有字幕")
                        return None

                # 处理所有字幕语言
                for subtitle in subtitles_info:
                    lang = subtitle.get('lan_doc', subtitle.get('lan', 'unknown'))
                    lang_code = subtitle.get('lan', 'unknown')
                    subtitle_url = subtitle.get('subtitle_url', '')

                    if not subtitle_url:
                        continue

                    # 确保URL是完整的
                    if subtitle_url.startswith('//'):
                        subtitle_url = 'https:' + subtitle_url

                    # 下载字幕内容
                    subtitle_response = requests.get(subtitle_url, headers=self.headers)
                    subtitle_data = subtitle_response.json()

                    body = subtitle_data.get('body', [])
                    if not body:
                        continue

                    # 计算前10条字幕内容的哈希值作为指纹
                    first_items = body[:min(10, len(body))]
                    content_fingerprint = '|||'.join([item['content'] for item in first_items])
                    content_hash = hashlib.md5(content_fingerprint.encode()).hexdigest()

                    all_attempts.append({
                        'lang': lang,
                        'lang_code': lang_code,
                        'data': subtitle_data,
                        'hash': content_hash,
                        'preview': [item['content'] for item in first_items[:5]]
                    })

                    print(f"  [尝试{api_attempt + 1}] {lang}: {first_items[0]['content'][:20]}...")

            except Exception as e:
                print(f"  [WARN] 尝试{api_attempt + 1}失败: {e}")
                continue

        # 分析所有尝试，找出最可靠的结果
        if not all_attempts:
            print("  [ERROR] 所有尝试都失败了")
            return None

        # 按语言分组
        by_lang = {}
        for attempt in all_attempts:
            lang_code = attempt['lang_code']
            if lang_code not in by_lang:
                by_lang[lang_code] = []
            by_lang[lang_code].append(attempt)

        # 处理每种语言
        all_subtitles = []
        for lang_code, attempts in by_lang.items():
            # 统计每个哈希值出现的次数
            hash_counts = {}
            for attempt in attempts:
                hash_val = attempt['hash']
                if hash_val not in hash_counts:
                    hash_counts[hash_val] = []
                hash_counts[hash_val].append(attempt)

            # 选择出现最多的版本
            most_common = max(hash_counts.values(), key=len)
            selected = most_common[0]

            print(f"\n  [结果] {selected['lang']}: 共{len(attempts)}次尝试，{len(most_common)}次获得相同内容")
            print(f"  预览: {selected['preview'][:3]}")

            # 只有获得至少2次相同内容才认为可靠
            if len(most_common) >= 2:
                # 创建兼容的字幕对象，包含元数据和内容
                subtitle_obj = selected['data'].copy()
                subtitle_obj['lan'] = selected['lang_code']  # 添加lan字段用于识别
                subtitle_obj['lan_doc'] = selected['lang']    # 添加lan_doc字段用于显示
                all_subtitles.append(subtitle_obj)
            else:
                print(f"  [WARN] {selected['lang']} 字幕可靠性不足（仅获得1次），跳过")

        return all_subtitles if all_subtitles else None

    def save_subtitle_as_srt(self, subtitle_data: Dict, output_path: str):
        """将字幕保存为SRT格式"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                body = subtitle_data.get('body', [])
                for i, item in enumerate(body, 1):
                    start_time = self._format_time(item['from'])
                    end_time = self._format_time(item['to'])
                    content = item['content']

                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{content}\n\n")

            print(f"字幕已保存到: {output_path}")
            return True
        except Exception as e:
            print(f"保存字幕失败: {e}")
            return False

    def save_subtitle_as_json(self, subtitle_data: Dict, output_path: str):
        """将字幕保存为JSON格式"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(subtitle_data, f, ensure_ascii=False, indent=2)
            print(f"字幕JSON已保存到: {output_path}")
            return True
        except Exception as e:
            print(f"保存字幕JSON失败: {e}")
            return False

    def save_subtitle_as_text(self, subtitle_data: Dict, output_path: str):
        """将字幕保存为纯文本格式（只保留字幕内容，不包含时间轴）"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                body = subtitle_data.get('body', [])
                for item in body:
                    content = item['content'].strip()
                    if content:  # 只写入非空内容
                        f.write(f"{content}\n")

            print(f"字幕文本已保存到: {output_path}")
            return True
        except Exception as e:
            print(f"保存字幕文本失败: {e}")
            return False

    def _format_time(self, seconds: float) -> str:
        """将秒数转换为SRT时间格式 HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def download_video_with_ytdlp(self, url: str, output_dir: str = './downloads'):
        """使用yt-dlp下载视频（需要安装yt-dlp）"""
        try:
            import yt_dlp

            os.makedirs(output_dir, exist_ok=True)

            ydl_opts = {
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'writesubtitles': True,
                'allsubtitles': True,
                'subtitleslangs': ['zh-CN', 'zh-Hans', 'en'],
                'merge_output_format': 'mp4',
            }

            # 如果有cookies，添加到yt-dlp
            if self.cookies:
                cookie_str = '; '.join([f"{k}={v}" for k, v in self.cookies.items()])
                ydl_opts['http_headers'] = {'Cookie': cookie_str}

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"开始下载视频: {url}")
                ydl.download([url])
                print("下载完成！")
                return True

        except ImportError:
            print("未安装yt-dlp，请运行: pip install yt-dlp")
            return False
        except Exception as e:
            print(f"下载视频失败: {e}")
            return False


def main():
    print("=" * 60)
    print("Bilibili 视频下载和字幕提取工具")
    print("=" * 60)

    if len(sys.argv) > 1:
        video_url = sys.argv[1]
    else:
        video_url = input("请输入B站视频URL (支持BV号、完整链接、短链接): ").strip()

    if not video_url:
        print("URL不能为空！")
        return

    downloader = BilibiliDownloader()

    # 提取BV号
    print("\n正在解析视频URL...")
    bvid = downloader.extract_bvid(video_url)
    if not bvid:
        print("无法从URL中提取BV号，请检查URL是否正确")
        return

    print(f"BV号: {bvid}")

    # 获取视频信息
    print("\n正在获取视频信息...")
    video_info = downloader.get_video_info(bvid)
    if not video_info:
        print("获取视频信息失败！")
        return

    print(f"\n视频标题: {video_info['title']}")
    print(f"UP主: {video_info['author']}")
    print(f"时长: {video_info['duration']}秒")

    # 获取字幕
    print("\n正在检查字幕...")
    subtitles = downloader.get_subtitles(bvid, video_info['cid'])

    if subtitles:
        # 创建输出目录
        output_dir = './subtitles'
        os.makedirs(output_dir, exist_ok=True)

        # 只保存中文字幕
        chinese_subtitle = None
        for subtitle in subtitles:
            lang_code = subtitle['language_code']
            # 查找中文字幕（包括 zh, zh-CN, ai-zh 等）
            if 'zh' in lang_code.lower():
                chinese_subtitle = subtitle
                break

        if chinese_subtitle:
            lang = chinese_subtitle['language']
            print(f"\n保存中文字幕: {lang}")

            # 清理文件名
            safe_title = re.sub(r'[<>:"/\\|?*]', '_', video_info['title'])

            # 只保存为纯文本格式（不含时间轴）
            txt_filename = f"{safe_title}.txt"
            txt_path = os.path.join(output_dir, txt_filename)
            downloader.save_subtitle_as_text(chinese_subtitle['data'], txt_path)
        else:
            print("\n未找到中文字幕")

    # 询问是否下载视频
    print("\n" + "=" * 60)
    download_choice = input("是否下载视频？(y/n): ").strip().lower()
    if download_choice == 'y':
        downloader.download_video_with_ytdlp(video_url)

    print("\n处理完成！")


if __name__ == "__main__":
    main()
