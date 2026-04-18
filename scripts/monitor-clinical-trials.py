#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
临床试验监控脚本
功能：每日搜索 ClinicalTrials.gov 和 PubMed，追踪抗衰老临床试验进展
"""

import requests
import json
from datetime import datetime
from pathlib import Path

# API 端点
CLINICALTRIALS_API = "https://clinicaltrials.gov/api/v2/studies"
PUBMED_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

# 输出文件
CONTENT_FILE = Path(__file__).parent.parent / "content" / "clinical-trials.md"
DATA_FILE = Path(__file__).parent.parent / "data" / "clinical_trials_monitor.json"
EMAIL_LIST_FILE = Path(__file__).parent.parent / "data" / "email_subscribers.json"


def search_clinicaltrials(condition, page_size=10):
    """
    搜索 ClinicalTrials.gov
    
    Args:
        condition: 搜索条件
        page_size: 每页结果数
    
    Returns:
        list: 试验列表
    """
    params = {
        "query.cond": condition,
        "pageSize": page_size,
        "sort": "StartDate:desc"
    }
    
    try:
        response = requests.get(CLINICALTRIALS_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("studies", [])
    except Exception as e:
        print(f"ClinicalTrials.gov 搜索失败：{e}")
        return []


def search_pubmed(query, max_results=10):
    """
    搜索 PubMed
    
    Args:
        query: 搜索词
        max_results: 最大结果数
    
    Returns:
        list: PMID 列表
    """
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "sort": "pub+date",
        "retmode": "json"
    }
    
    try:
        response = requests.get(PUBMED_ESEARCH, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"PubMed 搜索失败：{e}")
        return []


def evaluate_rpr_for_trial(trial):
    """
    基于 TranslAGE RPR 框架评估试验使用的生物标志物
    
    Args:
        trial: 试验信息
    
    Returns:
        float: RPR 评分
    """
    # 简化的评估逻辑
    protocol = trial.get("protocolSection", {})
    outcome_measures = protocol.get("outcomeMeasuresSection", [])
    
    # 检查是否使用高质量生物标志物
    high_quality_biomarkers = [
        "epigenetic clock", "DNA methylation", "telomere",
        "frailty", "cognitive", "mortality", "cardiovascular"
    ]
    
    score = 5.0  # 基础分
    
    for outcome in outcome_measures:
        title = outcome.get("measure", {}).get("title", "").lower()
        for biomarker in high_quality_biomarkers:
            if biomarker in title:
                score += 0.5
    
    return min(10.0, score)


def load_email_subscribers():
    """
    加载邮件订阅者列表
    
    Returns:
        list: 订阅者列表
    """
    if EMAIL_LIST_FILE.exists():
        with open(EMAIL_LIST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"subscribers": []}


def send_email_briefing(subscribers, briefing):
    """
    发送邮件简报
    
    Args:
        subscribers: 订阅者列表
        briefing: 简报内容
    """
    # 实际实现需要配置邮件服务
    # 这里仅做示例
    print(f"准备发送 {len(subscribers)} 封邮件简报...")
    for subscriber in subscribers:
        print(f"  - 发送至：{subscriber['email']} ({subscriber['interest']})")


def monitor_clinical_trials():
    """
    主监控函数
    """
    print("=" * 60)
    print("临床试验监控")
    print("=" * 60)
    
    # 搜索关键词
    keywords = [
        "aging clinical trial",
        "senolytics",
        "NAD+ longevity",
        "metformin longevity",
        "rapamycin aging",
        "senescence intervention"
    ]
    
    briefing = {
        "date": datetime.now().isoformat(),
        "new_trials": [],
        "updated_trials": [],
        "new_publications": []
    }
    
    # 搜索临床试验
    print("正在搜索 ClinicalTrials.gov...")
    for keyword in keywords:
        trials = search_clinicaltrials(keyword)
        if trials:
            briefing["new_trials"].extend(trials[:5])  # 每个关键词最多 5 个
            print(f"  - {keyword}: 找到 {len(trials)} 个试验")
    
    # 搜索 PubMed 文献
    print("正在搜索 PubMed...")
    for keyword in keywords:
        pmids = search_pubmed(f"{keyword} AND clinical trial", max_results=5)
        if pmids:
            briefing["new_publications"].extend(pmids)
            print(f"  - {keyword}: 找到 {len(pmids)} 篇文献")
    
    # 保存简报
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(briefing, f, ensure_ascii=False, indent=2)
    
    # 加载订阅者并发送邮件
    subscribers_data = load_email_subscribers()
    if subscribers_data.get("subscribers"):
        send_email_briefing(subscribers_data["subscribers"], briefing)
    
    print("=" * 60)
    print("监控完成！")
    print("=" * 60)


if __name__ == "__main__":
    monitor_clinical_trials()
