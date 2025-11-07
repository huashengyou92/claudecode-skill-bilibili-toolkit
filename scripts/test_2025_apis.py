#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试2025年11月最新的B站API
包括WBI签名、搜索API、字幕API
"""

import json
from bilibili_search import BilibiliSearch
from bilibili_downloader import BilibiliDownloader

def main():
    print("=" * 60)
    print("测试 2025年11月 B站API更新")
    print("=" * 60)

    # 加载Cookie
    try:
        with open('../bilibili_cookies.json', 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        print("[OK] Cookie已加载")
    except:
        cookies = None
        print("[WARN] 未找到Cookie文件")

    # 测试1: WBI签名的搜索API
    print("\n[TEST 1] WBI签名搜索API")
    print("-" * 40)
    searcher = BilibiliSearch(cookies=cookies)
    videos = searcher.search_videos("测试", page=1, page_size=2)

    if videos:
        print(f"[OK] 搜索成功，找到 {len(videos)} 个视频")
        for i, v in enumerate(videos, 1):
            print(f"  {i}. {v['title'][:30]}...")
    else:
        print("[ERROR] 搜索失败")
        return

    # 测试2: 字幕API (使用第一个视频)
    print("\n[TEST 2] 字幕API (/x/player/wbi/v2)")
    print("-" * 40)
    downloader = BilibiliDownloader(cookies=cookies)

    test_video = videos[0]
    bvid = test_video['bvid']
    print(f"测试视频: {test_video['title'][:30]}...")
    print(f"BV号: {bvid}")

    # 获取视频信息
    info = downloader.get_video_info(bvid)
    if not info:
        print("[ERROR] 无法获取视频信息")
        return

    print(f"[OK] 视频信息获取成功")
    print(f"  CID: {info['cid']}")

    # 获取字幕
    subtitles = downloader.get_subtitles(bvid, info['cid'])

    if subtitles:
        print(f"[OK] 字幕获取成功")
        print(f"  语言数量: {len(subtitles)}")
        for sub in subtitles:
            print(f"  - {sub.get('lan_doc', 'unknown')}")
    else:
        print("[INFO] 该视频没有字幕（正常情况，不是所有视频都有字幕）")

    # 测试3: 多个视频查找有字幕的
    print("\n[TEST 3] 查找有字幕的视频")
    print("-" * 40)
    test_videos = searcher.search_videos("Python教程", page=1, page_size=5)

    found_subtitle = False
    for video in test_videos[:5]:
        bvid = video['bvid']
        info = downloader.get_video_info(bvid)
        if not info:
            continue

        subtitles = downloader.get_subtitles(bvid, info['cid'], max_api_retries=1)
        if subtitles:
            print(f"[OK] 找到有字幕的视频:")
            print(f"  标题: {video['title']}")
            print(f"  BV号: {bvid}")
            print(f"  字幕: {len(subtitles)} 种语言")
            found_subtitle = True
            break

    if not found_subtitle:
        print("[INFO] 前5个视频都没有字幕")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    print("\n[OK] 所有更新已应用:")
    print("  1. WBI签名机制 (/scripts/wbi_signer.py)")
    print("  2. 搜索API: /x/web-interface/wbi/search/type")
    print("  3. 字幕API: /x/player/wbi/v2")
    print("\n[INFO] Skill描述已更新为中文，应该更容易触发")

if __name__ == '__main__':
    main()
