#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bilibili 视频搜索工具
支持关键词搜索并获取视频信息
"""

import requests
import json
import sys
from typing import List, Dict, Optional
from wbi_signer import WBISigner


class BilibiliSearch:
    def __init__(self, cookies: Optional[Dict] = None):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Origin': 'https://www.bilibili.com',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        # 合并用户提供的cookies和基础cookies
        self.cookies = {
            'buvid3': 'B1E5F8D7-C8E5-4F6B-A9D3-1234567890AB',
            'buvid4': 'B1E5F8D7-C8E5-4F6B-A9D3-1234567890AB',
            'b_nut': '1234567890'
        }
        if cookies:
            self.cookies.update(cookies)

        # 使用新版WBI搜索API (2025最新)
        self.search_api = "https://api.bilibili.com/x/web-interface/wbi/search/type"
        self.session = requests.Session()

        # 初始化WBI签名器
        self.wbi_signer = WBISigner(cookies=self.cookies)

    def search_videos(self, keyword: str, page: int = 1, page_size: int = 20, order: str = "totalrank") -> Optional[List[Dict]]:
        """
        搜索B站视频

        Args:
            keyword: 搜索关键词
            page: 页码（从1开始）
            page_size: 每页结果数量（最大50）
            order: 排序方式
                - totalrank: 综合排序（默认）
                - click: 播放量
                - pubdate: 发布时间
                - dm: 弹幕数
                - stow: 收藏数

        Returns:
            视频列表，每个视频包含：title, bvid, author, play, duration, pubdate等
        """
        params = {
            'search_type': 'video',
            'keyword': keyword,
            'page': page,
            'page_size': page_size,
            'order': order
        }

        # 使用WBI签名
        signed_params = self.wbi_signer.sign_params(params.copy())

        try:
            response = self.session.get(self.search_api, params=signed_params, headers=self.headers, cookies=self.cookies)

            # 添加详细的错误处理
            if response.status_code != 200:
                print(f"[ERROR] HTTP错误: {response.status_code}")
                print(f"[ERROR] 响应内容: {response.text[:200]}")
                return None

            try:
                data = response.json()
            except json.JSONDecodeError as e:
                print(f"[ERROR] JSON解析失败: {str(e)}")
                print(f"[ERROR] 响应内容: {response.text[:200]}")
                return None

            if data['code'] != 0:
                print(f"[ERROR] 搜索失败: {data.get('message', '未知错误')}")
                return None

            result_data = data.get('data', {})
            videos = result_data.get('result', [])

            if not videos:
                print(f"[INFO] 没有找到关于 '{keyword}' 的视频")
                return []

            # 处理视频数据
            processed_videos = []
            for video in videos:
                processed = {
                    'title': video.get('title', '').replace('<em class="keyword">', '').replace('</em>', ''),
                    'bvid': video.get('bvid', ''),
                    'author': video.get('author', ''),
                    'play': video.get('play', 0),
                    'video_review': video.get('video_review', 0),  # 弹幕数
                    'favorites': video.get('favorites', 0),
                    'duration': video.get('duration', ''),
                    'pubdate': video.get('pubdate', 0),
                    'description': video.get('description', ''),
                    'url': f"https://www.bilibili.com/video/{video.get('bvid', '')}"
                }
                processed_videos.append(processed)

            return processed_videos

        except Exception as e:
            print(f"[ERROR] 搜索出错: {e}")
            import traceback
            traceback.print_exc()
            return None

    def search_and_display(self, keyword: str, max_results: int = 10):
        """搜索并格式化显示结果"""
        print(f"\n正在搜索: {keyword}")
        print("=" * 80)

        videos = self.search_videos(keyword, page_size=max_results)

        if not videos:
            return

        print(f"\n找到 {len(videos)} 个结果：\n")

        for i, video in enumerate(videos, 1):
            print(f"{i}. {video['title']}")
            print(f"   BV号: {video['bvid']}")
            print(f"   UP主: {video['author']}")
            print(f"   播放: {self._format_number(video['play'])} | 弹幕: {self._format_number(video['video_review'])} | 收藏: {self._format_number(video['favorites'])}")
            print(f"   时长: {video['duration']}")
            print(f"   链接: {video['url']}")
            print()

    def _format_number(self, num: int) -> str:
        """格式化数字显示（万、亿）"""
        if num >= 100000000:
            return f"{num / 100000000:.1f}亿"
        elif num >= 10000:
            return f"{num / 10000:.1f}万"
        else:
            return str(num)

    def export_to_json(self, keyword: str, output_file: str = "search_results.json", max_results: int = 50):
        """搜索并导出为JSON"""
        videos = self.search_videos(keyword, page_size=max_results)

        if not videos:
            return

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'keyword': keyword,
                'total_results': len(videos),
                'videos': videos
            }, f, ensure_ascii=False, indent=2)

        print(f"\n[OK] 搜索结果已保存到: {output_file}")
        print(f"共 {len(videos)} 个视频")

    def get_bvids(self, keyword: str, max_results: int = 10) -> List[str]:
        """只返回BV号列表"""
        videos = self.search_videos(keyword, page_size=max_results)
        if not videos:
            return []
        return [video['bvid'] for video in videos]


def main():
    """命令行入口"""
    print("=" * 80)
    print("Bilibili 视频搜索工具")
    print("=" * 80)

    if len(sys.argv) > 1:
        keyword = ' '.join(sys.argv[1:])
    else:
        keyword = input("\n请输入搜索关键词: ").strip()

    if not keyword:
        print("[ERROR] 关键词不能为空")
        return

    searcher = BilibiliSearch()

    # 询问操作
    print("\n选择操作:")
    print("1. 显示搜索结果")
    print("2. 导出为JSON")
    print("3. 只显示BV号列表")

    choice = input("\n请选择 (1/2/3，默认1): ").strip() or "1"

    if choice == "1":
        max_results = input("显示多少个结果？(默认10): ").strip()
        max_results = int(max_results) if max_results.isdigit() else 10
        searcher.search_and_display(keyword, max_results)

    elif choice == "2":
        max_results = input("导出多少个结果？(默认50): ").strip()
        max_results = int(max_results) if max_results.isdigit() else 50
        output_file = input("输出文件名 (默认search_results.json): ").strip() or "search_results.json"
        searcher.export_to_json(keyword, output_file, max_results)

    elif choice == "3":
        max_results = input("获取多少个BV号？(默认10): ").strip()
        max_results = int(max_results) if max_results.isdigit() else 10
        bvids = searcher.get_bvids(keyword, max_results)
        print(f"\n找到 {len(bvids)} 个视频的BV号:")
        for i, bvid in enumerate(bvids, 1):
            print(f"{i}. {bvid}")


if __name__ == "__main__":
    main()
