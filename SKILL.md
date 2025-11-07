---
name: bilibili-toolkit
description: Comprehensive toolkit for working with Bilibili (哔哩哔哩/B站) videos. Enables keyword search on Bilibili, video URL extraction, and automatic subtitle download. Use this skill when the user mentions Bilibili, B站, wants to search videos, extract video links, download subtitles, or process Chinese video content. Particularly useful for batch processing video subtitles, content analysis, and video research workflows.
---

# Bilibili Toolkit

## What I Can Do

I can help you work with Bilibili (B站) videos in the following ways:

### 1. Video Search
- Search Bilibili using keywords
- Find videos by topic, author, or title
- Filter and sort results by popularity, date, or duration
- Display video metadata (views, author, publish date)

### 2. URL Extraction
- Extract BV IDs from Bilibili URLs
- Process single videos or batch lists
- Validate video accessibility

### 3. Subtitle Download & Processing
- Automatically download Chinese subtitles (AI or manual)
- Export as clean text files (named as `{BV号}_{标题}.txt`)
- Batch process multiple videos
- Handles Bilibili's API with retry mechanisms

### 4. Content Analysis
- Analyze subtitle content for keywords and themes
- Generate usage reports and statistics
- Create comprehensive analysis documents

## When to Use This Skill

Activate when the user mentions:
- "Bilibili", "B站", or "哔哩哔哩"
- Searching or discovering videos (e.g., "search Bilibili for Python tutorials")
- Downloading subtitles (e.g., "get the subtitle for this video")
- Batch processing videos (e.g., "download subtitles from these 10 videos")
- Analyzing video content (e.g., "what do these videos discuss?")
- Research workflows (e.g., "analyze discussion about AI on Bilibili")

## Typical Workflows

### Quick Search & Download
1. Search for videos by keyword
2. Select relevant videos
3. Download their subtitles
4. Analyze content

### URL Processing
1. Provide Bilibili video URLs or BV IDs
2. Extract video information
3. Download and process subtitles
4. Generate reports

### Batch Analysis
1. Search multiple keywords
2. Filter top videos
3. Batch download all subtitles
4. Create comprehensive analysis report

## Output Location

All output files are saved to the workspace directory:
- **Subtitles**: `bilibili-workspace/subtitles/{BV号}_{标题}.txt`
- **Reports**: `bilibili-workspace/reports/`
- **Articles**: `bilibili-workspace/articles/`

## Requirements

- Python 3.7+
- Bilibili cookies (SESSDATA) for subtitle access
- See SETUP.md for configuration instructions

## Technical Notes

- Uses 2025 Bilibili WBI signature mechanism
- Automatic retry with verification for unreliable APIs
- Filename format includes BV号 for source traceability
- Supports both manual and AI-generated Chinese subtitles
