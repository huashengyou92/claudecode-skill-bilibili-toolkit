#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie配置助手
帮助用户轻松配置B站Cookie
"""

import json
import os


def main():
    print("=" * 60)
    print("B站字幕提取工具 - Cookie配置助手")
    print("=" * 60)
    print()
    print("本工具将帮助你配置B站Cookie，以便获取视频字幕。")
    print()
    print("请按照以下步骤操作：")
    print("1. 在浏览器中登录 bilibili.com")
    print("2. 按F12打开开发者工具")
    print("3. 点击 Application（应用程序）标签")
    print("4. 展开 Cookies → https://www.bilibili.com")
    print("5. 找到并复制 SESSDATA 的值")
    print()
    print("详细图文教程请查看: COOKIE_GUIDE.md")
    print()
    print("=" * 60)
    print()

    # 获取SESSDATA
    sessdata = input("请粘贴你的 SESSDATA (必需): ").strip()

    if not sessdata:
        print("[ERROR] SESSDATA不能为空！")
        return

    # 验证SESSDATA格式（基本检查）
    if len(sessdata) < 20:
        print("[WARNING] SESSDATA长度似乎太短，请确认是否复制完整")
        confirm = input("是否继续？(y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            return

    # 获取其他可选的cookie
    print()
    print("以下Cookie是可选的，可以直接按Enter跳过：")
    print()

    bili_jct = input("请粘贴你的 bili_jct (可选，按Enter跳过): ").strip()
    buvid3 = input("请粘贴你的 buvid3 (可选，按Enter跳过): ").strip()

    # 创建cookie配置
    cookies = {
        "SESSDATA": sessdata
    }

    if bili_jct:
        cookies["bili_jct"] = bili_jct

    if buvid3:
        cookies["buvid3"] = buvid3

    # 保存到文件
    config_file = "bilibili_cookies.json"

    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        print()
        print("=" * 60)
        print("[OK] Cookie配置已保存到:", config_file)
        print("=" * 60)
        print()
        print("配置内容:")
        print(f"  - SESSDATA: {sessdata[:20]}...{sessdata[-10:]}")
        if bili_jct:
            print(f"  - bili_jct: {bili_jct[:10]}...")
        if buvid3:
            print(f"  - buvid3: {buvid3[:10]}...")

        print()
        print("现在可以运行工具提取字幕了！")
        print("示例: python bilibili_downloader.py BV1qixrzFE6t")
        print()

        # 询问是否测试
        test = input("是否现在测试Cookie配置？(y/n): ").strip().lower()
        if test == 'y':
            print()
            print("正在测试Cookie配置...")
            test_cookies(cookies)

    except Exception as e:
        print(f"[ERROR] 保存配置文件失败: {e}")


def test_cookies(cookies):
    """测试Cookie是否有效"""
    try:
        from bilibili_downloader import BilibiliDownloader

        downloader = BilibiliDownloader(cookies=cookies)

        # 测试一个已知的视频
        test_bvid = input("\n请输入一个测试视频的BV号 (或按Enter使用默认): ").strip()
        if not test_bvid:
            test_bvid = "BV1qixrzFE6t"

        print(f"\n正在测试视频 {test_bvid}...")

        # 获取视频信息
        info = downloader.get_video_info(test_bvid)
        if not info:
            print("[ERROR] 无法获取视频信息，请检查BV号是否正确")
            return

        print(f"[OK] 视频标题: {info['title']}")

        # 尝试获取字幕
        subtitles = downloader.get_subtitles(test_bvid, info['cid'])

        if subtitles:
            print(f"[OK] 成功获取字幕！找到 {len(subtitles)} 个字幕")
            for sub in subtitles:
                print(f"  - {sub['language']}")
            print()
            print("Cookie配置测试通过！")
        else:
            print("[INFO] 该视频可能没有字幕，或Cookie无法访问字幕")
            print("[INFO] 请尝试其他有字幕的视频")

    except ImportError:
        print("[ERROR] 无法导入 bilibili_downloader 模块")
        print("请确保在正确的目录下运行此脚本")
    except Exception as e:
        print(f"[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
