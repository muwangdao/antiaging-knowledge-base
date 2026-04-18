#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exBAClock 数据库自动同步脚本
功能：每周检查 exBAClock 是否有新增时钟模型，自动更新页面内容
"""

import requests
import json
from datetime import datetime
from pathlib import Path

# exBAClock 数据库 URL
EXBACLOCK_URL = "https://akob.shinyapps.io/exbaclock/"
EXBACLOCK_API = "https://akob.shinyapps.io/exbaclock/data/clocks"  # 假设的 API 端点

# 输出文件
CONTENT_FILE = Path(__file__).parent.parent / "content" / "aging-clocks.md"
LAST_SYNC_FILE = Path(__file__).parent.parent / "data" / "exbaclock_last_sync.json"


def fetch_exbaclock_data():
    """
    从 exBAClock 获取最新数据
    
    Returns:
        dict: 时钟数据，如果失败则返回 None
    """
    try:
        # 尝试从 API 获取数据
        response = requests.get(EXBACLOCK_API, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API 请求失败：{response.status_code}")
            return None
    except Exception as e:
        print(f"获取数据失败：{e}")
        return None


def load_last_sync():
    """
    加载上次同步的数据
    
    Returns:
        dict: 上次同步的数据
    """
    if LAST_SYNC_FILE.exists():
        with open(LAST_SYNC_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"clocks": [], "date": None}


def save_last_sync(data):
    """
    保存同步数据
    
    Args:
        data: 要保存的数据
    """
    LAST_SYNC_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LAST_SYNC_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def check_for_updates(current_data, last_data):
    """
    检查是否有新时钟
    
    Args:
        current_data: 当前数据
        last_data: 上次同步的数据
    
    Returns:
        list: 新增的时钟列表
    """
    if not current_data or not last_data.get("clocks"):
        return []
    
    current_names = {clock.get("name") for clock in current_data}
    last_names = {clock.get("name") for clock in last_data.get("clocks", [])}
    
    new_clocks = current_names - last_names
    return list(new_clocks)


def update_content_file(new_clocks):
    """
    更新内容文件
    
    Args:
        new_clocks: 新增的时钟列表
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
    
    # 如果有新时钟，添加通知
    if new_clocks:
        notification = f"\n\n> 🆕 **新增 {len(new_clocks)} 个时钟模型**：{', '.join(new_clocks[:5])}{'...' if len(new_clocks) > 5 else ''}\n"
        # 在免责声明前添加通知
        content = content.replace(
            "## ⚠️ 免责声明",
            notification + "\n## ⚠️ 免责声明"
        )
    
    CONTENT_FILE.write_text(content, encoding='utf-8')
    print(f"✅ 已更新内容文件：{CONTENT_FILE}")


def sync_exbaclock():
    """
    主同步函数
    """
    print("=" * 60)
    print("exBAClock 数据库同步")
    print("=" * 60)
    
    # 获取最新数据
    print("正在从 exBAClock 获取数据...")
    current_data = fetch_exbaclock_data()
    
    if not current_data:
        print("⚠️ 无法获取 exBAClock 数据，跳过本次同步")
        return
    
    # 加载上次同步的数据
    last_sync = load_last_sync()
    
    # 检查更新
    new_clocks = check_for_updates(current_data, last_sync)
    
    if new_clocks:
        print(f"🆕 发现 {len(new_clocks)} 个新时钟：")
        for clock in new_clocks[:10]:
            print(f"  - {clock}")
        if len(new_clocks) > 10:
            print(f"  ... 还有 {len(new_clocks) - 10} 个")
        
        # 更新内容文件
        update_content_file(new_clocks)
    else:
        print("✅ 没有新时钟")
    
    # 保存同步数据
    save_last_sync({
        "clocks": current_data,
        "date": datetime.now().isoformat(),
        "count": len(current_data) if isinstance(current_data, list) else 0
    })
    
    print("=" * 60)
    print("同步完成！")
    print("=" * 60)


if __name__ == "__main__":
    sync_exbaclock()
