#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bilibili 完整工作流程脚本
Complete Workflow: Search → Filter → Download Subtitles → Analyze → Report

使用方法:
    python workflow.py "关键词" --max-videos 10
"""

import os
import sys
import json
import argparse
from datetime import datetime
from collections import Counter
from typing import List, Dict, Optional
import re

# 导入其他模块
from bilibili_search import BilibiliSearch
from bilibili_downloader import BilibiliDownloader


class BilibiliWorkflow:
    """B站视频分析完整工作流程"""

    def __init__(self, cookies: Optional[Dict] = None):
        """
        初始化工作流程

        Args:
            cookies: Bilibili cookies (可选，从配置文件自动加载)
        """
        self.searcher = BilibiliSearch()
        self.downloader = BilibiliDownloader(cookies=cookies)
        self.results = {
            'keyword': '',
            'search_time': '',
            'videos': [],
            'subtitles': [],
            'analysis': {},
            'report_path': ''
        }

    def search_videos(self, keyword: str, max_results: int = 20) -> List[Dict]:
        """
        搜索视频

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数

        Returns:
            视频列表
        """
        print(f"\n[INFO] 正在搜索关键词: {keyword}")
        print(f"[INFO] 获取前 {max_results} 个结果...")

        videos = self.searcher.search_videos(keyword, page=1, page_size=max_results)

        if not videos:
            print(f"[WARN] 没有找到相关视频")
            return []

        print(f"[OK] 找到 {len(videos)} 个视频\n")

        # 显示搜索结果
        for idx, video in enumerate(videos, 1):
            print(f"{idx}. {video['title']}")
            print(f"   UP主: {video['author']} | 播放: {video['play']:,} | 时长: {video['duration']}")
            print(f"   链接: {video['url']}")
            print()

        self.results['keyword'] = keyword
        self.results['search_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.results['videos'] = videos

        return videos

    def filter_videos(self, videos: List[Dict], auto_select: bool = True,
                     top_n: Optional[int] = None) -> List[Dict]:
        """
        筛选视频

        Args:
            videos: 视频列表
            auto_select: 是否自动选择
            top_n: 自动选择前N个（按播放量排序）

        Returns:
            筛选后的视频列表
        """
        if not videos:
            return []

        if auto_select:
            if top_n:
                # 按播放量排序并选择前N个
                sorted_videos = sorted(videos, key=lambda x: x['play'], reverse=True)
                selected = sorted_videos[:top_n]
                print(f"[INFO] 自动选择播放量最高的 {len(selected)} 个视频")
            else:
                selected = videos
                print(f"[INFO] 选择所有 {len(selected)} 个视频")
        else:
            # 手动选择模式（交互式）
            print("\n[INFO] 请输入要下载字幕的视频序号（用逗号分隔，如: 1,3,5）")
            print("[INFO] 或输入 'all' 选择所有视频")

            choice = input("选择: ").strip()

            if choice.lower() == 'all':
                selected = videos
            else:
                try:
                    indices = [int(x.strip()) for x in choice.split(',')]
                    selected = [videos[i-1] for i in indices if 0 < i <= len(videos)]
                except (ValueError, IndexError):
                    print("[WARN] 无效的选择，将选择所有视频")
                    selected = videos

        return selected

    def download_subtitles(self, videos: List[Dict]) -> List[Dict]:
        """
        下载视频字幕

        Args:
            videos: 视频列表

        Returns:
            成功下载的字幕信息列表
        """
        print(f"\n[INFO] 开始下载 {len(videos)} 个视频的字幕...")

        # 使用工作区目录
        workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'bilibili-workspace'))
        subtitles_dir = os.path.join(workspace_dir, 'subtitles')
        os.makedirs(subtitles_dir, exist_ok=True)

        successful_downloads = []

        for idx, video in enumerate(videos, 1):
            print(f"\n[{idx}/{len(videos)}] 处理: {video['title']}")

            try:
                # 提取BV ID
                bvid = self.downloader.extract_bvid(video['url'])
                if not bvid:
                    print(f"[WARN] 无法提取BV ID")
                    continue

                # 获取视频信息
                info = self.downloader.get_video_info(bvid)
                if not info:
                    print(f"[WARN] 无法获取视频信息")
                    continue

                cid = info['cid']
                title = info['title']

                # 获取字幕
                print(f"[INFO] 正在获取字幕（带验证机制）...")
                subtitles = self.downloader.get_subtitles(bvid, cid)

                if not subtitles:
                    print(f"[WARN] 该视频没有字幕")
                    continue

                # 只处理中文字幕
                chinese_subtitle = None
                for sub in subtitles:
                    if 'zh' in sub.get('lan', '').lower() or 'chi' in sub.get('lan', '').lower():
                        chinese_subtitle = sub
                        break

                if not chinese_subtitle:
                    print(f"[WARN] 没有找到中文字幕")
                    continue

                # 保存字幕为纯文本（格式：BV号_标题.txt）
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_title = safe_title[:50]  # 限制文件名长度
                output_path = os.path.join(subtitles_dir, f"{bvid}_{safe_title}.txt")

                self.downloader.save_subtitle_as_text(chinese_subtitle, output_path)

                # 读取字幕内容用于分析
                with open(output_path, 'r', encoding='utf-8') as f:
                    subtitle_text = f.read()

                successful_downloads.append({
                    'video': video,
                    'bvid': bvid,
                    'subtitle_path': output_path,
                    'subtitle_text': subtitle_text,
                    'word_count': len(subtitle_text)
                })

                print(f"[OK] 字幕已保存: {output_path}")

            except Exception as e:
                print(f"[ERROR] 下载失败: {str(e)}")
                continue

        print(f"\n[INFO] 成功下载 {len(successful_downloads)}/{len(videos)} 个视频的字幕")

        self.results['subtitles'] = successful_downloads

        return successful_downloads

    def analyze_content(self, subtitles: List[Dict]) -> Dict:
        """
        分析字幕内容

        Args:
            subtitles: 字幕信息列表

        Returns:
            分析结果
        """
        print(f"\n[INFO] 正在分析 {len(subtitles)} 个视频的字幕内容...")

        if not subtitles:
            return {}

        # 合并所有字幕文本
        all_text = ""
        for sub in subtitles:
            all_text += sub['subtitle_text'] + "\n"

        # 基础统计
        total_chars = len(all_text)
        total_lines = all_text.count('\n')

        # 分词并统计词频（简单的中文分词 - 2-3字词）
        words = []
        for line in all_text.split('\n'):
            line = line.strip()
            if not line:
                continue
            # 提取2-3字的中文词组
            for i in range(len(line) - 1):
                if '\u4e00' <= line[i] <= '\u9fff':  # 中文字符
                    # 2字词
                    if i + 1 < len(line) and '\u4e00' <= line[i+1] <= '\u9fff':
                        words.append(line[i:i+2])
                    # 3字词
                    if i + 2 < len(line) and '\u4e00' <= line[i+1] <= '\u9fff' and '\u4e00' <= line[i+2] <= '\u9fff':
                        words.append(line[i:i+3])

        # 词频统计（排除单字和过于常见的词）
        stop_words = {'这个', '一个', '我们', '你们', '他们', '什么', '怎么', '可以', '就是', '因为', '所以', '但是', '然后', '如果', '这样', '那么', '已经', '没有', '不是', '还是'}
        word_freq = Counter([w for w in words if len(w) >= 2 and w not in stop_words])
        top_keywords = word_freq.most_common(30)

        # 视频时长统计
        total_duration_mins = sum(
            self._parse_duration(sub['video']['duration'])
            for sub in subtitles
        )

        # 播放量统计
        total_plays = sum(sub['video']['play'] for sub in subtitles)
        avg_plays = total_plays // len(subtitles) if subtitles else 0

        analysis = {
            'video_count': len(subtitles),
            'total_chars': total_chars,
            'total_lines': total_lines,
            'total_duration_mins': total_duration_mins,
            'total_plays': total_plays,
            'avg_plays': avg_plays,
            'top_keywords': top_keywords,
            'videos_summary': [
                {
                    'title': sub['video']['title'],
                    'author': sub['video']['author'],
                    'play': sub['video']['play'],
                    'duration': sub['video']['duration'],
                    'word_count': sub['word_count'],
                    'url': sub['video']['url']
                }
                for sub in subtitles
            ]
        }

        self.results['analysis'] = analysis

        print(f"[OK] 分析完成")
        print(f"    - 总字符数: {total_chars:,}")
        print(f"    - 总行数: {total_lines:,}")
        print(f"    - 总时长: {total_duration_mins:.1f} 分钟")
        print(f"    - 总播放量: {total_plays:,}")
        print(f"    - 平均播放量: {avg_plays:,}")

        return analysis

    def _parse_duration(self, duration_str: str) -> float:
        """解析时长字符串为分钟数"""
        try:
            parts = duration_str.split(':')
            if len(parts) == 2:
                return int(parts[0]) + int(parts[1]) / 60
            elif len(parts) == 3:
                return int(parts[0]) * 60 + int(parts[1]) + int(parts[2]) / 60
        except:
            pass
        return 0

    def generate_report(self, output_dir: str = None) -> str:
        """
        生成分析报告

        Args:
            output_dir: 报告输出目录（默认使用工作区目录）

        Returns:
            报告文件路径
        """
        # 使用工作区目录
        if output_dir is None:
            workspace_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'bilibili-workspace'))
            output_dir = os.path.join(workspace_dir, 'reports')
        print(f"\n[INFO] 正在生成分析报告...")

        os.makedirs(output_dir, exist_ok=True)

        # 生成报告文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        keyword_safe = "".join(c for c in self.results['keyword'] if c.isalnum() or c in (' ', '-', '_')).strip()
        keyword_safe = keyword_safe.replace(' ', '_')[:20]
        report_filename = f"bilibili_report_{keyword_safe}_{timestamp}.md"
        report_path = os.path.join(output_dir, report_filename)

        # 生成Markdown报告
        analysis = self.results.get('analysis', {})
        subtitles = self.results.get('subtitles', [])

        with open(report_path, 'w', encoding='utf-8') as f:
            # 标题
            f.write(f"# Bilibili 视频分析报告\n\n")
            f.write(f"**关键词:** {self.results['keyword']}\n\n")
            f.write(f"**分析时间:** {self.results['search_time']}\n\n")
            f.write("---\n\n")

            # 摘要
            f.write("## 📊 数据摘要\n\n")
            if analysis:
                f.write(f"- **视频数量:** {analysis['video_count']} 个\n")
                f.write(f"- **总字幕字符数:** {analysis['total_chars']:,} 字\n")
                f.write(f"- **总字幕行数:** {analysis['total_lines']:,} 行\n")
                f.write(f"- **总视频时长:** {analysis['total_duration_mins']:.1f} 分钟\n")
                f.write(f"- **总播放量:** {analysis['total_plays']:,}\n")
                f.write(f"- **平均播放量:** {analysis['avg_plays']:,}\n")
            f.write("\n")

            # 热门关键词
            f.write("## 🔥 热门关键词（Top 30）\n\n")
            if analysis and 'top_keywords' in analysis:
                f.write("| 排名 | 关键词 | 出现次数 |\n")
                f.write("|------|--------|----------|\n")
                for idx, (word, count) in enumerate(analysis['top_keywords'], 1):
                    f.write(f"| {idx} | {word} | {count} |\n")
            f.write("\n")

            # 视频列表
            f.write("## 📹 视频列表\n\n")
            if analysis and 'videos_summary' in analysis:
                for idx, video in enumerate(analysis['videos_summary'], 1):
                    f.write(f"### {idx}. {video['title']}\n\n")
                    f.write(f"- **UP主:** {video['author']}\n")
                    f.write(f"- **播放量:** {video['play']:,}\n")
                    f.write(f"- **时长:** {video['duration']}\n")
                    f.write(f"- **字幕字数:** {video['word_count']:,}\n")
                    f.write(f"- **链接:** [{video['url']}]({video['url']})\n")
                    f.write("\n")

            # 字幕文件
            f.write("## 📝 字幕文件\n\n")
            if subtitles:
                f.write("所有字幕已保存到以下文件：\n\n")
                for idx, sub in enumerate(subtitles, 1):
                    f.write(f"{idx}. `{sub['subtitle_path']}`\n")
            f.write("\n")

            # 页脚
            f.write("---\n\n")
            f.write("*本报告由 Bilibili Toolkit 自动生成*\n")

        self.results['report_path'] = report_path

        print(f"[OK] 报告已生成: {report_path}")

        return report_path

    def run(self, keyword: str, max_videos: int = 10, auto_select: bool = True) -> Dict:
        """
        运行完整工作流程

        Args:
            keyword: 搜索关键词
            max_videos: 最大视频数
            auto_select: 是否自动选择视频

        Returns:
            完整的结果字典
        """
        print("=" * 60)
        print("Bilibili 视频分析工作流程")
        print("=" * 60)

        # 1. 搜索视频
        videos = self.search_videos(keyword, max_results=max_videos * 2)
        if not videos:
            print("[ERROR] 搜索失败，工作流程终止")
            return self.results

        # 2. 筛选视频
        selected_videos = self.filter_videos(videos, auto_select=auto_select, top_n=max_videos)
        if not selected_videos:
            print("[ERROR] 没有选择任何视频，工作流程终止")
            return self.results

        # 3. 下载字幕
        subtitles = self.download_subtitles(selected_videos)
        if not subtitles:
            print("[WARN] 没有成功下载任何字幕")
            return self.results

        # 4. 分析内容
        analysis = self.analyze_content(subtitles)

        # 5. 生成报告
        report_path = self.generate_report()

        print("\n" + "=" * 60)
        print("工作流程完成!")
        print("=" * 60)
        print(f"[OK] 分析报告: {report_path}")
        print(f"[OK] 字幕文件: ./subtitles/")

        return self.results


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description='Bilibili 视频分析完整工作流程',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 搜索关键词并分析前10个视频
  python workflow.py "Python编程"

  # 指定最大视频数
  python workflow.py "人工智能" --max-videos 5

  # 手动选择视频
  python workflow.py "机器学习" --manual
        """
    )

    parser.add_argument('keyword', help='搜索关键词')
    parser.add_argument('--max-videos', type=int, default=10, help='最大视频数量（默认: 10）')
    parser.add_argument('--manual', action='store_true', help='手动选择视频（默认: 自动选择）')

    args = parser.parse_args()

    # 运行工作流程
    workflow = BilibiliWorkflow()

    try:
        results = workflow.run(
            keyword=args.keyword,
            max_videos=args.max_videos,
            auto_select=not args.manual
        )

        # 显示结果摘要
        if results.get('report_path'):
            print(f"\n[INFO] 查看完整报告: {results['report_path']}")

    except KeyboardInterrupt:
        print("\n[INFO] 用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] 工作流程失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
