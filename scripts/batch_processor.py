#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bilibili 批量处理工具
整合搜索和字幕下载功能
"""

import sys
import os
import time
from bilibili_search import BilibiliSearch
from bilibili_downloader import BilibiliDownloader


class BatchProcessor:
    def __init__(self):
        self.searcher = BilibiliSearch()
        self.downloader = BilibiliDownloader()

    def search_and_download_subtitles(self, keyword: str, max_videos: int = 10, delay: float = 2.0):
        """
        搜索视频并批量下载字幕

        Args:
            keyword: 搜索关键词
            max_videos: 最多处理多少个视频
            delay: 每个视频之间的延迟（秒），避免请求过快
        """
        print(f"\n[1/3] 搜索关键词: {keyword}")
        print("=" * 80)

        videos = self.searcher.search_videos(keyword, page_size=max_videos)

        if not videos:
            print("[ERROR] 没有找到视频")
            return

        print(f"[OK] 找到 {len(videos)} 个视频\n")

        # 创建输出目录
        output_dir = f"./subtitles/{keyword}"
        os.makedirs(output_dir, exist_ok=True)

        print(f"[2/3] 开始下载字幕...")
        print(f"字幕将保存到: {output_dir}")
        print("=" * 80 + "\n")

        success_count = 0
        no_subtitle_count = 0
        error_count = 0

        for i, video in enumerate(videos, 1):
            print(f"[{i}/{len(videos)}] 处理: {video['title'][:50]}")
            print(f"         BV号: {video['bvid']}")

            try:
                # 获取视频信息
                info = self.downloader.get_video_info(video['bvid'])
                if not info:
                    print(f"         [SKIP] 无法获取视频信息\n")
                    error_count += 1
                    continue

                # 获取字幕
                subtitles = self.downloader.get_subtitles(video['bvid'], info['cid'])

                if not subtitles:
                    print(f"         [SKIP] 没有字幕\n")
                    no_subtitle_count += 1
                    continue

                # 找到中文字幕
                chinese_subtitle = None
                for subtitle in subtitles:
                    if 'zh' in subtitle['language_code'].lower():
                        chinese_subtitle = subtitle
                        break

                if chinese_subtitle:
                    # 保存字幕
                    import re
                    safe_title = re.sub(r'[<>:"/\\|?*]', '_', info['title'])
                    output_file = os.path.join(output_dir, f"{safe_title}.txt")

                    self.downloader.save_subtitle_as_text(chinese_subtitle['data'], output_file)
                    print(f"         [OK] 字幕已保存\n")
                    success_count += 1
                else:
                    print(f"         [SKIP] 未找到中文字幕\n")
                    no_subtitle_count += 1

                # 延迟，避免请求过快
                if i < len(videos):
                    time.sleep(delay)

            except Exception as e:
                print(f"         [ERROR] 处理失败: {e}\n")
                error_count += 1

        # 统计结果
        print("\n" + "=" * 80)
        print(f"[3/3] 处理完成！")
        print("=" * 80)
        print(f"总共处理: {len(videos)} 个视频")
        print(f"成功下载: {success_count} 个字幕")
        print(f"没有字幕: {no_subtitle_count} 个")
        print(f"处理失败: {error_count} 个")
        print(f"\n字幕保存位置: {output_dir}")

    def download_from_list(self, bvid_list: list, delay: float = 2.0):
        """从BV号列表批量下载字幕"""
        print(f"\n批量下载 {len(bvid_list)} 个视频的字幕")
        print("=" * 80)

        output_dir = "./subtitles/batch"
        os.makedirs(output_dir, exist_ok=True)

        success_count = 0

        for i, bvid in enumerate(bvid_list, 1):
            print(f"\n[{i}/{len(bvid_list)}] 处理 {bvid}")

            try:
                info = self.downloader.get_video_info(bvid)
                if not info:
                    print("  [SKIP] 无法获取视频信息")
                    continue

                print(f"  标题: {info['title'][:50]}")

                subtitles = self.downloader.get_subtitles(bvid, info['cid'])
                if not subtitles:
                    print("  [SKIP] 没有字幕")
                    continue

                # 保存中文字幕
                for subtitle in subtitles:
                    if 'zh' in subtitle['language_code'].lower():
                        import re
                        safe_title = re.sub(r'[<>:"/\\|?*]', '_', info['title'])
                        output_file = os.path.join(output_dir, f"{safe_title}.txt")
                        self.downloader.save_subtitle_as_text(subtitle['data'], output_file)
                        print(f"  [OK] 字幕已保存")
                        success_count += 1
                        break

                if i < len(bvid_list):
                    time.sleep(delay)

            except Exception as e:
                print(f"  [ERROR] 处理失败: {e}")

        print(f"\n完成！成功下载 {success_count}/{len(bvid_list)} 个字幕")


def main():
    """命令行入口"""
    print("=" * 80)
    print("Bilibili 批量处理工具")
    print("=" * 80)

    processor = BatchProcessor()

    print("\n选择操作:")
    print("1. 搜索关键词并下载字幕")
    print("2. 从BV号列表下载字幕")

    choice = input("\n请选择 (1/2): ").strip()

    if choice == "1":
        keyword = input("请输入搜索关键词: ").strip()
        if not keyword:
            print("[ERROR] 关键词不能为空")
            return

        max_videos = input("最多处理多少个视频？(默认10): ").strip()
        max_videos = int(max_videos) if max_videos.isdigit() else 10

        processor.search_and_download_subtitles(keyword, max_videos)

    elif choice == "2":
        print("\n请输入BV号列表（每行一个，输入空行结束）:")
        bvid_list = []
        while True:
            line = input().strip()
            if not line:
                break
            # 提取BV号
            if line.startswith('BV'):
                bvid_list.append(line)
            elif 'BV' in line:
                import re
                match = re.search(r'BV[a-zA-Z0-9]+', line)
                if match:
                    bvid_list.append(match.group(0))

        if not bvid_list:
            print("[ERROR] 没有有效的BV号")
            return

        print(f"\n将处理 {len(bvid_list)} 个视频")
        processor.download_from_list(bvid_list)


if __name__ == "__main__":
    main()
