#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClockBase Agent 自动监控脚本
功能：每周检查 ClockBase Agent 更新，生成简报
"""

import requests
import json
from datetime import datetime
from pathlib import Path

# ClockBase Agent URL
CLOCKBASE_URL = "https://clockbase.io"
CLOCKBASE_PAPER_URL = "https://www.biorxiv.org/content/10.1101/2023.02.28.530532"

# PubMed API
PUBMED_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"

# 输出文件
CONTENT_FILE = Path(__file__).parent.parent / "content" / "clockbase.md"
BRIEFING_FILE = Path(__file__).parent.parent / "data" / "clockbase_briefing.json"


def check_clockbase_updates():
    """
    检查 ClockBase Agent 是否有更新
    
    Returns:
        dict: 更新信息
    """
    updates = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "platform_status": "unknown",
        "new_interventions": [],
        "new_papers": [],
        "summary": ""
    }
    
    # 检查平台可访问性
    try:
        response = requests.get(CLOCKBASE_URL, timeout=10)
        if response.status_code == 200:
            updates["platform_status"] = "available"
            updates["summary"] += "✅ ClockBase Agent 平台可访问\n"
        else:
            updates["platform_status"] = "error"
            updates["summary"] += f"⚠️ ClockBase Agent 返回状态码：{response.status_code}\n"
    except Exception as e:
        updates["platform_status"] = "unavailable"
        updates["summary"] += f"❌ 无法访问 ClockBase Agent: {str(e)}\n"
    
    # 检查 PubMed 新文献
    try:
        params = {
            "db": "pubmed",
            "term": "ClockBase Agent OR ClockBase aging intervention",
            "retmax": 5,
            "sort": "pub+date",
            "retmode": "json"
        }
        response = requests.get(PUBMED_ESEARCH, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            pmids = data.get("esearchresult", {}).get("idlist", [])
            if pmids:
                updates["new_papers"] = pmids[:3]
                updates["summary"] += f"📄 发现 {len(pmids)} 篇相关文献\n"
    except Exception as e:
        updates["summary"] += f"⚠️ 无法检查 PubMed: {str(e)}\n"
    
    return updates


def load_last_briefing():
    """
    加载上次简报
    
    Returns:
        dict: 上次简报数据
    """
    if BRIEFING_FILE.exists():
        with open(BRIEFING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"last_check": None, "briefings": []}


def save_briefing(data):
    """
    保存简报数据
    
    Args:
        data: 要保存的数据
    """
    BRIEFING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BRIEFING_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def update_content_file(updates):
    """
    更新内容文件
    
    Args:
        updates: 更新信息
    """
    if not CONTENT_FILE.exists():
        print(f"内容文件不存在：{CONTENT_FILE}")
        return
    
    content = CONTENT_FILE.read_text(encoding='utf-8')
    
    # 更新最后更新时间
    today = datetime.now().strftime("%Y-%m-%d")
    content = content.replace(
        "**最后更新**：2026-04-18",
        f"**最后更新**：{today}"
    )
    
    # 添加最新简报
    if updates["new_papers"] or updates["platform_status"] == "available":
        briefing = f"""
#### 最新简报 ({today})

{updates["summary"]}

"""
        # 在"最新简报"部分前添加
        content = content.replace(
            "#### 最新简报\n\n> ⏳ **正在等待首次自动监控**",
            briefing
        )
    
    CONTENT_FILE.write_text(content, encoding='utf-8')
    print(f"✅ 已更新内容文件：{CONTENT_FILE}")


def sync_clockbase():
    """
    主同步函数
    """
    print("=" * 60)
    print("ClockBase Agent 监控")
    print("=" * 60)
    
    # 检查更新
    print("正在检查 ClockBase Agent 更新...")
    updates = check_clockbase_updates()
    
    print(updates["summary"])
    
    # 保存简报
    briefing_data = load_last_briefing()
    briefing_data["last_check"] = datetime.now().isoformat()
    briefing_data["briefings"].append(updates)
    save_briefing(briefing_data)
    
    # 更新内容文件
    update_content_file(updates)
    
    print("=" * 60)
    print("监控完成！")
    print("=" * 60)


if __name__ == "__main__":
    sync_clockbase()
