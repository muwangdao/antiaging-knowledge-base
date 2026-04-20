#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
衰老研究趋势分析脚本
功能：分析 PubMed 文献关键词频率，生成趋势简报
"""

import requests
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

# PubMed API
PUBMED_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# 输出文件
CONTENT_FILE = Path(__file__).parent.parent / "content" / "recent.md"
DATA_FILE = Path(__file__).parent.parent / "data" / "trend_analysis.json"

# 关键词列表
KEYWORDS = [
    "Senolytics", "NAD+", "NMN", "NR", "Epigenetic Clock", 
    "DNA Methylation", "Telomere", "Senescence", "SASP",
    "Mitophagy", "Autophagy", "mTOR", "Rapamycin", "Metformin",
    "Sirtuins", "Resveratrol", "Spermidine", "Urolithin A",
    "Stem Cell", "Microbiome", "Gut Microbiota", "Inflammation",
    "Oxidative Stress", "Mitochondria", "Proteostasis"
]


def search_pubmed_count(keyword, days=30):
    """
    搜索 PubMed 文献数量
    
    Args:
        keyword: 关键词
        days: 过去几天
    
    Returns:
        int: 文献数量
    """
    date_from = (datetime.now() - timedelta(days=days)).strftime("%Y/%m/%d")
    date_to = datetime.now().strftime("%Y/%m/%d")
    
    query = f"({keyword}) AND (aging OR longevity OR senescence) AND ({date_from}[Date - Publication] : {date_to}[Date - Publication])"
    
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": 0,
        "retmode": "json"
    }
    
    try:
        response = requests.get(PUBMED_ESEARCH, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        count = int(data.get("esearchresult", {}).get("count", 0))
        return count
    except Exception as e:
        print(f"搜索失败 {keyword}: {e}")
        return 0


def calculate_growth_rate(current_count, previous_count):
    """
    计算增长率
    
    Args:
        current_count: 当前数量
        previous_count: 前期数量
    
    Returns:
        float: 增长率百分比
    """
    if previous_count == 0:
        return 100.0 if current_count > 0 else 0.0
    
    return ((current_count - previous_count) / previous_count) * 100


def get_trend_label(growth_rate):
    """
    获取趋势标签
    
    Args:
        growth_rate: 增长率
    
    Returns:
        str: 趋势标签
    """
    if growth_rate >= 50:
        return "🚀 爆发增长"
    elif growth_rate >= 25:
        return "📈 快速上升"
    elif growth_rate >= 10:
        return "📈 上升"
    elif growth_rate >= -10:
        return "➡️ 稳定"
    else:
        return "📉 下降"


def analyze_trends():
    """
    主分析函数
    """
    print("=" * 60)
    print("衰老研究趋势分析")
    print("=" * 60)
    
    # 搜索当前月份数据
    print("正在分析当前月份数据...")
    current_counts = {}
    for keyword in KEYWORDS:
        count = search_pubmed_count(keyword, days=30)
        current_counts[keyword] = count
        print(f"  {keyword}: {count} 篇")
    
    # 搜索上个月数据
    print("\n正在分析上个月数据...")
    previous_counts = {}
    for keyword in KEYWORDS:
        count = search_pubmed_count(keyword, days=60) - current_counts[keyword]
        previous_counts[keyword] = count
        print(f"  {keyword}: {count} 篇")
    
    # 计算增长率
    print("\n计算增长率...")
    growth_rates = {}
    for keyword in KEYWORDS:
        growth_rate = calculate_growth_rate(
            current_counts[keyword],
            previous_counts[keyword]
        )
        growth_rates[keyword] = growth_rate
    
    # 排序
    sorted_by_count = sorted(current_counts.items(), key=lambda x: x[1], reverse=True)
    sorted_by_growth = sorted(growth_rates.items(), key=lambda x: x[1], reverse=True)
    
    # 生成简报
    briefing = {
        "date": datetime.now().isoformat(),
        "top_keywords": sorted_by_count[:10],
        "top_growth": sorted_by_growth[:5],
        "emerging_topics": sorted_by_growth[:3],
        "current_counts": current_counts,
        "previous_counts": previous_counts,
        "growth_rates": growth_rates
    }
    
    # 保存数据
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(briefing, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 已保存趋势分析数据：{DATA_FILE}")
    print("=" * 60)
    print("分析完成！")
    print("=" * 60)
    
    return briefing


if __name__ == "__main__":
    analyze_trends()
