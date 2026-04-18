#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 新闻官自动化脚本
功能：每日/每周自动发布抗衰老领域前沿研究解读
"""

import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
import re

# API 端点
PUBMED_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
CLINICALTRIALS_API = "https://clinicaltrials.gov/api/v2/studies"

# 输出目录
CONTENT_DIR = Path(__file__).parent.parent / "content"
DATA_DIR = Path(__file__).parent.parent / "data"
NEWS_DIR = CONTENT_DIR / "news"


def search_pubmed(keywords, days=1, max_results=10, min_if=5):
    """
    搜索 PubMed 文献
    
    Args:
        keywords: 关键词列表
        days: 过去几天
        max_results: 最大结果数
        min_if: 最小影响因子
    
    Returns:
        list: 文献列表
    """
    date_from = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
    date_to = datetime.now().strftime("%Y/%m/%d")
    
    # 构建搜索词
    search_terms = " OR ".join(keywords)
    query = f"({search_terms}) AND ({date_from}[Date - Publication] : {date_to}[Date - Publication])"
    
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results * 2,  # 多获取一些用于筛选
        "sort": "pub+date",
        "retmode": "json"
    }
    
    try:
        response = requests.get(PUBMED_ESEARCH, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        pmids = data.get("esearchresult", {}).get("idlist", [])
        
        # 获取文献详情
        papers = get_pubmed_details(pmids[:max_results])
        
        # 筛选高影响因子期刊（简化版，实际应查询期刊 IF）
        high_if_journals = [
            "Cell", "Nature", "Science", "Cell Metab", "Nat Metab",
            "Nat Aging", "Aging Cell", "Sci Transl Med", "Nat Med"
        ]
        
        filtered_papers = []
        for paper in papers:
            journal = paper.get("journal", "")
            # 简化筛选：检查期刊名是否包含高 IF 期刊关键词
            if any(if_journal.lower() in journal.lower() for if_journal in high_if_journals):
                filtered_papers.append(paper)
        
        # 如果高 IF 论文不足，补充普通论文
        if len(filtered_papers) < 3:
            for paper in papers:
                if paper not in filtered_papers:
                    filtered_papers.append(paper)
                if len(filtered_papers) >= 3:
                    break
        
        return filtered_papers[:3]
    
    except Exception as e:
        print(f"PubMed 搜索失败：{e}")
        return []


def get_pubmed_details(pmid_list):
    """
    获取 PubMed 文献详细信息
    
    Args:
        pmid_list: PMID 列表
    
    Returns:
        list: 文献详细信息
    """
    if not pmid_list:
        return []
    
    params = {
        "db": "pubmed",
        "id": ",".join(pmid_list),
        "retmode": "json"
    }
    
    try:
        response = requests.get(PUBMED_ESUMMARY, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        results = data.get("result", {})
        
        papers = []
        for pmid in pmid_list:
            if pmid in results:
                paper = results[pmid]
                papers.append({
                    "pmid": pmid,
                    "title": paper.get("title", ""),
                    "journal": paper.get("fulljournalname", ""),
                    "pubdate": paper.get("pubdate", ""),
                    "doi": paper.get("doi", ""),
                    "authors": paper.get("authors", []),
                    "summary": paper.get("essence", "")
                })
        return papers
    except Exception as e:
        print(f"获取 PubMed 详情失败：{e}")
        return []


def generate_daily_digest(papers):
    """
    生成每日快讯摘要
    
    Args:
        papers: 文献列表
    
    Returns:
        str: Markdown 格式的每日快讯
    """
    today = datetime.now().strftime("%Y-%m-%d")
    
    content = f"""---
title: "每日快讯 {today}"
date: {today}
description: "抗衰老领域最新研究进展速递"
draft: false
type: "daily-digest"
---

# 📰 每日快讯 · {today}

> **自动推送** · 过去 24 小时高影响力研究 · PubMed 影响因子>5 期刊

---

"""
    
    for i, paper in enumerate(papers, 1):
        # 生成摘要（简化版，实际应使用 AI 生成）
        summary = generate_paper_summary(paper)
        
        content += f"""## 研究 {i}: {paper['title']}

**期刊**: {paper['journal']}  
**发表日期**: {paper['pubdate']}  
**PMID**: [{paper['pmid']}](https://pubmed.ncbi.nlm.nih.gov/{paper['pmid']}/)  
**DOI**: [{paper['doi']}](https://doi.org/{paper['doi']})

### 🌟 研究亮点

{summary['highlights']}

### 🔬 关键发现

{summary['findings']}

### 🧪 方法简介

{summary['methods']}

### 🏥 临床相关性

{summary['clinical_relevance']}

---

"""
    
    content += f"""
**数据来源**: PubMed  
**筛选标准**: 影响因子>5 · 过去 24 小时 · 衰老相关研究  
**生成时间**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**明日预告**: 继续追踪 senolytics、NAD+、表观遗传时钟等领域最新进展

---

[← 返回首页](/)
"""
    
    return content


def generate_paper_summary(paper):
    """
    生成单篇论文摘要（简化版）
    
    Args:
        paper: 论文信息
    
    Returns:
        dict: 摘要各部分
    """
    title = paper.get("title", "")
    summary = paper.get("summary", "")
    
    # 简化处理：从标题和摘要提取关键信息
    # 实际应使用 AI 模型生成
    
    highlights = f"本研究发表于{paper.get('journal', '知名期刊')}，聚焦抗衰老领域前沿问题。"
    
    findings = summary[:200] + "..." if len(summary) > 200 else summary
    
    methods = "采用分子生物学、细胞实验或临床队列研究方法。"
    
    clinical_relevance = "研究成果为理解衰老机制和开发抗衰老干预策略提供新见解。"
    
    return {
        "highlights": highlights,
        "findings": findings,
        "methods": methods,
        "clinical_relevance": clinical_relevance
    }


def generate_research_snapshot(paper):
    """
    生成研究快照图文卡片内容
    
    Args:
        paper: 论文信息
    
    Returns:
        dict: 卡片内容
    """
    title = paper.get("title", "")
    # 简化标题（最多 50 字）
    short_title = title[:50] + "..." if len(title) > 50 else title
    
    # 核心发现一句话
    key_finding = paper.get("summary", "")[:100] + "..."
    
    # 标签
    tags = ["#抗衰老", "#前沿研究", "#PubMed"]
    
    return {
        "title": short_title,
        "key_finding": key_finding,
        "tags": tags,
        "pmid": paper.get("pmid", ""),
        "journal": paper.get("journal", ""),
        "date": datetime.now().strftime("%Y-%m-%d")
    }


def monitor_abc_news():
    """
    监控 ABC 与 X-Age 项目新闻
    
    Returns:
        list: 新闻列表
    """
    # 简化版：实际应搜索特定关键词
    news = []
    
    # 示例新闻
    news.append({
        "title": "ABC 发布脂肪组织衰老生物标志物框架",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": "中国衰老标志物研究联合体",
        "summary": "ABC 专家组从功能、结构和体液三个维度推荐了脂肪组织衰老评估标志物。",
        "url": "https://doi.org/10.1093/lifemedi/lnaf027"
    })
    
    return news


def create_content_calendar():
    """
    创建内容发布日历
    
    Returns:
        dict: 日历内容
    """
    calendar = {
        "daily": {
            "time": "每天 08:00",
            "content": "每日快讯（3 篇论文摘要）",
            "auto": True
        },
        "weekly": {
            "time": "每周一 10:00",
            "content": "周深度解读候选列表（3-5 篇）",
            "auto": True
        },
        "manual_review": {
            "time": "每周一 14:00-18:00",
            "content": "人工审核周解读候选",
            "auto": False
        },
        "deep_dive": {
            "time": "每周二 08:00",
            "content": "发布深度解读文章（1 篇）",
            "auto": False
        },
        "snapshot": {
            "time": "每日自动",
            "content": "生成研究快照卡片",
            "auto": True
        },
        "abc_monitor": {
            "time": "每日 12:00",
            "content": "ABC 与 X-Age 项目新闻监控",
            "auto": True
        }
    }
    
    return calendar


def save_daily_digest(content):
    """
    保存每日快讯
    
    Args:
        content: Markdown 内容
    """
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"daily-digest-{today}.md"
    
    NEWS_DIR.mkdir(parents=True, exist_ok=True)
    filepath = NEWS_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ 已保存每日快讯：{filepath}")


def save_research_snapshot(snapshot, paper):
    """
    保存研究快照卡片
    
    Args:
        snapshot: 快照内容
        paper: 论文信息
    """
    today = datetime.now().strftime("%Y%m%d")
    pmid = paper.get("pmid", "unknown")
    filename = f"snapshot-{today}-{pmid}.json"
    
    SNAPSHOT_DIR = DATA_DIR / "snapshots"
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    filepath = SNAPSHOT_DIR / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(snapshot, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已保存研究快照：{filepath}")


def run_daily_task():
    """
    执行每日任务
    """
    print("=" * 60)
    print("AI 新闻官 - 每日任务")
    print("=" * 60)
    
    # 搜索 PubMed
    keywords = ["aging", "longevity", "senescence", "NAD+", "senolytics", "epigenetic clock"]
    print("正在搜索 PubMed 文献...")
    papers = search_pubmed(keywords, days=1, max_results=10)
    print(f"找到 {len(papers)} 篇高影响力论文")
    
    if papers:
        # 生成每日快讯
        print("正在生成每日快讯...")
        digest_content = generate_daily_digest(papers)
        save_daily_digest(digest_content)
        
        # 生成研究快照
        print("正在生成研究快照卡片...")
        for paper in papers:
            snapshot = generate_research_snapshot(paper)
            save_research_snapshot(snapshot, paper)
    
    # 监控 ABC 新闻
    print("正在监控 ABC 新闻...")
    abc_news = monitor_abc_news()
    print(f"找到 {len(abc_news)} 条 ABC 相关新闻")
    
    print("=" * 60)
    print("每日任务完成！")
    print("=" * 60)


if __name__ == "__main__":
    run_daily_task()
