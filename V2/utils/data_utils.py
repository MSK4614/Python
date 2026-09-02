import json
import os
from datetime import datetime

# 使用绝对路径，防止因运行目录不同导致找不到文件
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'partners.json')

# 初始化默认数据
DEFAULT_DATA = [
    {
        "id": 1,
        "title": "周末图书馆考研搭子",
        "location": "市图书馆3楼",
        "time": "周六 09:00",
        "category": "学习",
        "description": "互相监督打卡",
        "status": "招募中"
    },
    {
        "id": 2,
        "title": "夜跑减肥搭子",
        "location": "奥体中心",
        "time": "每晚 19:30",
        "category": "运动",
        "description": "配速6分左右",
        "status": "招募中"
    }
]


def load_partners():
    """读取搭子列表"""
    # 如果文件不存在，自动创建并写入默认数据
    if not os.path.exists(DATA_FILE):
        save_partners(DEFAULT_DATA)
        return DEFAULT_DATA

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 兼容性检查：如果旧数据没有 status 字段，自动补上
            for item in data:
                if 'status' not in item:
                    item['status'] = '招募中'
            return data
    except (json.JSONDecodeError, Exception) as e:
        print(f"读取文件出错: {e}")
        return []


def save_partners(data):
    """保存搭子列表到 JSON 文件"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_partner(partner_dict):
    """添加新搭子并自动分配 ID"""
    partners = load_partners()
    # 计算新 ID：取现有最大 ID + 1，如果列表为空则为 1
    new_id = max([p.get('id', 0) for p in partners], default=0) + 1

    partner_dict['id'] = new_id
    partner_dict['status'] = '招募中'  # 设置默认状态
    partner_dict['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')

    partners.append(partner_dict)
    save_partners(partners)


def get_partner_by_id(partner_id):
    """根据 ID 获取单个搭子信息"""
    partners = load_partners()
    for p in partners:
        # 使用 str() 转换以兼容字符串或整数类型的 ID
        if str(p.get('id')) == str(partner_id):
            return p
    return None


def update_partner_status(partner_id, new_status):
    """更新指定 ID 的搭子状态"""
    partners = load_partners()
    for p in partners:
        if str(p.get('id')) == str(partner_id):
            p['status'] = new_status
            save_partners(partners)
            return True
    return False


def delete_partner(partner_id):
    """删除指定 ID 的搭子"""
    partners = load_partners()
    # 过滤掉要删除的 ID
    new_partners = [p for p in partners if str(p.get('id')) != str(partner_id)]

    # 只有当数量确实减少时才保存（说明找到了该 ID）
    if len(new_partners) < len(partners):
        save_partners(new_partners)
        return True
    return False