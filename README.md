# Bilibili 工具包 - Claude Code 技能

B站（哔哩哔哩）视频研究和内容分析的完整工作流工具

## 功能介绍

此技能让 Claude 可以帮你：

1. **搜索视频** - 使用关键词搜索 B 站视频，获取视频元数据
2. **提取链接** - 批量提取 BV 号和视频 URL
3. **下载字幕** - 自动提取和保存中文字幕（AI 生成或人工上传）
4. **分析内容** - 提取关键词、统计数据、分析视频主题
5. **生成报告** - 创建详细的 Markdown 分析报告

所有操作都针对 AI 工作流优化，使用纯文本输出和智能重试机制。

## 快速开始

### 第一步：安装依赖

```bash
cd .claude/skills/bilibili-toolkit
pip install -r requirements.txt
```

### 第二步：配置 Cookie（一次性设置）

B站需要登录认证才能访问字幕。运行配置向导：

```bash
python scripts/setup_cookies.py
```

按照提示输入你的 B 站 Cookie。详细配置方法见 [配置指南.md](./配置指南.md)

### 第三步：开始使用

直接用自然语言向 Claude 提问，技能会自动激活：

**使用示例：**
- "搜索 B 站上关于 Python 的视频并下载字幕"
- "帮我下载这个 B 站视频的字幕：BV1xxx"
- "分析一下 B 站上关于三角洲行动的讨论"
- "找出哔哩哔哩上播放量最高的 10 个机器学习视频"

## 一键完整工作流

配置好 Cookie 后，可以直接运行完整工作流：

```bash
python scripts/workflow.py "关键词" --max-videos 10
```

这一条命令会自动完成：
1. 搜索视频
2. 按播放量筛选
3. 批量下载字幕
4. 内容分析
5. 生成报告

所有输出文件保存在 `bilibili-workspace/` 目录：
- **字幕文件**: `bilibili-workspace/subtitles/{BV号}_{标题}.txt`
- **分析报告**: `bilibili-workspace/reports/`
- **生成文章**: `bilibili-workspace/articles/`

## 文件结构

```
bilibili-toolkit/              # 技能定义
├── SKILL.md                   # 技能描述（Claude 读取）
├── 配置指南.md                 # 详细配置说明
├── README.md                  # 本文件
├── requirements.txt           # Python 依赖
├── bilibili_cookies.json.template  # Cookie 模板
├── scripts/                   # 实现脚本
│   ├── workflow.py           # 完整工作流
│   ├── bilibili_search.py    # 视频搜索
│   ├── bilibili_downloader.py # 字幕下载
│   ├── wbi_signer.py         # 2025 WBI 签名机制
│   ├── batch_processor.py    # 批处理工具
│   └── setup_cookies.py      # Cookie 配置向导
└── test_skill.py              # 测试脚本

bilibili-workspace/            # 输出数据（独立目录）
├── bilibili_cookies.json     # 你的 Cookie 配置
├── subtitles/                # 字幕文件
├── reports/                  # 分析报告
├── articles/                 # 生成的文章
└── downloads/                # 下载数据
```

## 主要功能详解

### 🔍 视频搜索

通过关键词搜索 B 站视频：

```python
from scripts.bilibili_search import BilibiliSearch

searcher = BilibiliSearch()
results = searcher.search("Python编程", max_results=20)
```

返回信息包括：
- 视频标题和 URL
- BV 号（视频 ID）
- 播放量、点赞数、投币数
- UP 主信息
- 发布时间
- 视频时长

### 📥 字幕下载

自动下载并处理中文字幕：

```python
from scripts.bilibili_downloader import BilibiliDownloader

downloader = BilibiliDownloader()
subtitles = downloader.download_subtitle("BV1xxx")
```

特性：
- 自动识别中文字幕（AI 生成或人工）
- 保存为纯文本格式（无时间戳）
- 文件名格式：`{BV号}_{标题}.txt`（便于溯源）
- 智能重试机制（应对 B 站不稳定的 API）
- 支持批量处理

### 🔄 批量处理

批量下载多个视频的字幕：

```python
from scripts.batch_processor import BatchProcessor

processor = BatchProcessor()
# 方法1：从搜索结果批量下载
results = searcher.search("机器学习", max_results=10)
processor.batch_download(results)

# 方法2：从 BV 号列表下载
bv_list = ["BV1xxx", "BV1yyy", "BV1zzz"]
processor.batch_download_from_ids(bv_list)
```

### 📊 内容分析

分析字幕内容，提取关键信息：

```python
from scripts.workflow import BilibiliWorkflow

workflow = BilibiliWorkflow()
workflow.run("三角洲行动改枪", max_videos=5)
```

自动生成：
- 高频词统计
- 主题分析
- 视频元数据汇总
- Markdown 格式报告

## 实际应用案例

### 案例 1：游戏攻略收集

**需求**：收集 B 站上关于"三角洲行动 AUG 改枪"的视频攻略

**操作**：
```bash
python scripts/workflow.py "三角洲aug改枪" --max-videos 5
```

**输出**：
- 下载 5 个相关视频的字幕
- 提取配装方案、改枪码、价格信息
- 生成综合攻略文档

实际生成的攻略：`bilibili-workspace/articles/AUG_完整攻略_DFBUILD风格.md`

### 案例 2：技术学习

**需求**：了解 B 站上 Python 教程的热门内容

**操作**：
```bash
python scripts/workflow.py "Python教程" --max-videos 20
```

**分析结果**：
- 热门话题：数据分析、爬虫、机器学习
- 推荐 UP 主
- 学习路径建议

### 案例 3：内容研究

**需求**：研究某个话题在 B 站的讨论情况

**操作**：
1. 搜索关键词
2. 下载所有相关视频字幕
3. 分析高频词和讨论主题
4. 生成研究报告

## 技术特性

### 2025 年最新 API 支持

- ✅ 使用最新的 WBI 签名机制
- ✅ 智能重试和验证机制
- ✅ 应对 B 站 API 的各种限制

### 文件命名规范

字幕文件采用 `{BV号}_{标题}.txt` 格式：
- **优势**：可以直接从文件名追溯到源视频
- **便于**：验证内容可靠性和迭代工作流

### 工作区分离

- **技能目录**：只包含代码和配置模板
- **工作区目录**：包含所有输出和用户数据
- **好处**：升级技能时不会影响你的数据

## 常见问题

### 为什么需要 Cookie？

B 站的字幕 API 需要登录认证。Cookie 用于：
- 访问字幕接口
- 避免频率限制
- 获取更稳定的服务

### Cookie 安全吗？

- Cookie 存储在本地工作区目录
- 不会上传或分享
- 建议定期更新
- 视同密码保护

### 有些视频没有字幕怎么办？

不是所有视频都有字幕。一般来说：
- ✅ 官方账号的视频通常有字幕
- ✅ 播放量高的视频更可能有字幕
- ✅ B 站会为部分视频自动生成 AI 字幕
- ❌ 小 UP 主的视频可能没有字幕

### 如何处理 API 限制？

技能已内置应对机制：
- 自动重试失败的请求
- 智能等待和避免频繁请求
- 使用登录 Cookie 提高限额
- 大批量任务建议分批处理

### 字幕质量如何？

- 人工字幕：质量最高，但较少
- AI 字幕：覆盖面广，准确率 85-95%
- 建议结合视频内容使用

## 更新日志

### 2025年11月 - v2.0

- ✅ 符合 Claude Skills 官方标准
- ✅ 工作区和技能目录分离
- ✅ 文件名包含 BV 号便于溯源
- ✅ 更新 WBI 签名机制
- ✅ 完善的中文文档

### 2024年11月 - v1.0

- 初始版本发布
- 基础搜索和下载功能

## 支持与反馈

如有问题或建议：

1. 查看 [配置指南.md](./配置指南.md) 的故障排除部分
2. 确保 Cookie 有效且未过期
3. 检查网络连接和 B 站可访问性
4. 确认使用的是已登录的 B 站账号的 Cookie

## 许可证

本技能仅供学习和研究使用。请遵守 B 站的使用条款和相关法律法规。

---

**提示**：使用本技能时，请尊重内容创作者的版权。下载的字幕仅供个人学习研究使用。
