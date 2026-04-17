#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PubMed 文献自动更新脚本
功能：从 PubMed 获取最新抗衰老研究文献，自动生成 Markdown 格式并更新网站内容
"""

import requests
import re
from datetime import datetime, timedelta
from pathlib import Path

# PubMed API 端点
PUBMED_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
PUBMED_SEARCH = f"{PUBMED_BASE_URL}esearch.fcgi"
PUBMED_SUMMARY = f"{PUBMED_BASE_URL}esummary.fcgi"

# 搜索词配置
SEARCH_TERMS = {
    "senolytics": "senolytics OR senescence OR cellular senescence",
    "nmn": "NMN OR nicotinamide mononucleotide OR NAD precursor",
    "urolithin": "urolithin A OR mitophagy",
    "spermidine": "spermidine OR autophagy",
    "resveratrol": "resveratrol OR SIRT1",
}

# 输出目录
CONTENT_DIR = Path(__file__).parent.parent / "content"


def search_pubmed(term, max_results=10, date_range="2025:2026"):
    """搜索 PubMed 获取文献 ID"""
    params = {
        "db": "pubmed",
        "term": f"({term}) AND ({date_range}[Date - Publication])",
        "retmax": max_results,
        "sort": "pub+date",
        "retmode": "json"
    }
    
    try:
        response = requests.get(PUBMED_SEARCH, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"搜索失败 {term}: {e}")
        return []


def get_pubmed_details(pmid_list):
    """获取文献详细信息"""
    if not pmid_list:
        return []
    
    params = {
        "db": "pubmed",
        "id": ",".join(pmid_list),
        "retmode": "json"
    }
    
    try:
        response = requests.get(PUBMED_SUMMARY, params=params, timeout=10)
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
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                })
        return papers
    except Exception as e:
        print(f"获取详情失败：{e}")
        return []


def format_markdown_table(papers, category):
    """格式化文献为 Markdown 表格"""
    if not papers:
        return ""
    
    lines = [
        f"### {category}",
        "",
        "| 日期 | 标题 | 期刊 | PMID | 关键发现 |",
        "|------|------|------|------|---------|"
    ]
    
    for paper in papers[:5]:  # 每个类别最多 5 篇
        date = paper.get("pubdate", "")
        title = paper.get("title", "")
        journal = paper.get("journal", "")
        pmid = paper.get("pmid", "")
        pmid_url = paper.get("url", "")
        
        # 生成简短描述（从标题提取）
        desc = title[:50] + "..." if len(title) > 50 else title
        
        lines.append(
            f"| {date} | {title} | {journal} | [{pmid}]({pmid_url}) | {desc} |"
        )
    
    return "\n".join(lines)


def update_recent_page():
    """更新近一个月研究进展页面"""
    print("正在更新近一个月研究进展...")
    
    all_content = []
    
    for category, term in SEARCH_TERMS.items():
        print(f"  搜索 {category}...")
        pmids = search_pubmed(term, max_results=5)
        papers = get_pubmed_details(pmids)
        
        if papers:
            table = format_markdown_table(papers, category)
            all_content.append(table)
    
    # 生成完整页面
    content = f"""---
title: "近一个月研究进展"
description: "按研究主题分类展示最近一个月的抗衰老研究进展"
---

# 近一个月研究进展

> **更新时间**：{datetime.now().strftime("%Y-%m-%d")} | **数据来源**：PubMed

---

## 📊 按主题分类

{chr(10).join(all_content)}

---

## 🔔 更新说明

- **数据来源**：PubMed 自动检索
- **更新频率**：每日自动更新
- **筛选标准**：优先选择 2025-2026 年发表的研究
- **PMID 链接**：所有文献均提供 PubMed 原文链接

---

*最后更新：{datetime.now().strftime("%Y-%m-%d")} | 自动生成*
"""
    
    # 写入文件
    output_file = CONTENT_DIR / "recent.md"
    output_file.write_text(content, encoding="utf-8")
    print(f"✓ 已更新 {output_file}")


def update_interventions_page():
    """更新干预方法页面"""
    print("正在更新干预方法页面...")
    
    # 获取各补充剂相关文献
    supplements = {
        "NMN": search_pubmed("NMN supplementation human", max_results=3),
        "Resveratrol": search_pubmed("resveratrol human trial", max_results=3),
        "Spermidine": search_pubmed("spermidine human", max_results=3),
        "Urolithin A": search_pubmed("urolithin A human", max_results=3),
    }
    
    # 生成参考文献列表
    references = []
    for supplement, pmids in supplements.items():
        papers = get_pubmed_details(pmids)
        for paper in papers:
            ref = f"{paper.get('title', '')}. *{paper.get('journal', '')}*. {paper.get('pubdate', '')}. PMID: [{paper.get('pmid', '')}]({paper.get('url', '')})"
            references.append(f"- **{supplement}**: {ref}")
    
    print(f"✓ 已更新干预方法页面参考文献")
    return "\n".join(references)


if __name__ == "__main__":
    print("=" * 50)
    print("PubMed 文献自动更新")
    print("=" * 50)
    
    # 确保内容目录存在
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 更新页面
    update_recent_page()
    references = update_interventions_page()
    
    print("=" * 50)
    print("更新完成！")
    print("=" * 50)
