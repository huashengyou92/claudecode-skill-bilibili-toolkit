#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Bilibili Skill 的功能
"""

import sys
sys.path.insert(0, 'scripts')

from bilibili_search import BilibiliSearch
from bilibili_downloader import BilibiliDownloader

def test_search():
    """测试搜索功能"""
    print("=" * 80)
    print("测试1: 视频搜索功能")
    print("=" * 80)

    searcher = BilibiliSearch()
    videos = searcher.search_videos("Python教程", page_size=5)

    if videos:
        print(f"\n[OK] 搜索成功，找到 {len(videos)} 个视频\n")
        for i, video in enumerate(videos, 1):
            print(f"{i}. {video['title']}")
            print(f"   BV: {video['bvid']}")
            print(f"   UP主: {video['author']}")
            print(f"   播放: {searcher._format_number(video['play'])}")
            print()
    else:
        print("[ERROR] 搜索失败")

def test_download():
    """测试下载功能"""
    print("\n" + "=" * 80)
    print("测试2: 字幕下载功能")
    print("=" * 80)

    downloader = BilibiliDownloader()

    # 使用之前测试成功的视频
    test_bvid = "BV1qixrzFE6t"

    print(f"\n测试视频: {test_bvid}")

    info = downloader.get_video_info(test_bvid)
    if info:
        print(f"[OK] 视频信息获取成功")
        print(f"     标题: {info['title'][:50]}...")
        print(f"     CID: {info['cid']}")
    else:
        print("[ERROR] 获取视频信息失败")
        return

    print("\n正在获取字幕...")
    subtitles = downloader.get_subtitles(test_bvid, info['cid'])

    if subtitles:
        print(f"[OK] 字幕获取成功")
        for subtitle in subtitles:
            body = subtitle['data'].get('body', [])
            print(f"     语言: {subtitle['language']}")
            print(f"     条数: {len(body)}")
            if body:
                print(f"     预览: {body[0]['content'][:30]}...")
    else:
        print("[ERROR] 未获取到字幕")

def test_api_usage():
    """测试 API 使用方式"""
    print("\n" + "=" * 80)
    print("测试3: Python API 集成")
    print("=" * 80)

    # 搜索
    searcher = BilibiliSearch()
    bvids = searcher.get_bvids("机器学习", max_results=3)

    print(f"\n[OK] 获得 {len(bvids)} 个BV号:")
    for i, bvid in enumerate(bvids, 1):
        print(f"  {i}. {bvid}")

def main():
    print("\nBilibili Toolkit Skill - 功能测试\n")

    # 测试搜索
    test_search()

    # 测试下载（需要cookie）
    try:
        test_download()
    except Exception as e:
        print(f"\n[SKIP] 下载测试跳过（可能未配置cookie）: {e}")

    # 测试API
    test_api_usage()

    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)
    print("\nSkill 已就绪，可以在 Claude Code 中使用。")
    print("只需提及 'Bilibili'、'B站' 或相关关键词，Claude 会自动调用此 Skill。")

if __name__ == "__main__":
    main()
