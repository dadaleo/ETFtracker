import requests
import json
import datetime
import os

# ================= 配置区域 =================
# 你的基金列表
MY_FUNDS = [
    "sh510300", "sh510310", "sz159919", "sh510330", 
    "sh510050", "sz159915", "sz159949", "sh510500", 
    "sh588000", "sz159629", "sh512100"
]

# 2025年底基准 (作为历史数据的锚点)
BASE_2025 = {
    "date": "2025-12-31",
    "totalShares": 4539.19,
    "totalCap": 17678.74,
    "marketCap": 108.86,
    "details": {} # 基准可能没有明细，设为空
}
# ===========================================

def fetch_data():
    # 构造腾讯接口 URL
    codes_str = ",".join(MY_FUNDS + ["sh000001", "sz399106"])
    url = f"https://qt.gtimg.cn/q={codes_str}"
    
    try:
        res = requests.get(url)
        return res.text
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def main():
    raw_text = fetch_data()
    if not raw_text:
        return

    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 1. 解析数据
    today_shares = 0.0
    today_amt = 0.0
    current_details = {}

    lines = raw_text.strip().split(';')
    data_map = {}
    
    # 先把原始数据转成 map 方便查找
    for line in lines:
        if '="' in line:
            key = line.split('="')[0].split('_')[-1] # v_sh510300 -> sh510300
            val = line.split('="')[1].replace('"', '')
            data_map[key] = val.split('~')

    # 计算基金总数
    for code in MY_FUNDS:
        if code in data_map:
            data = data_map[code]
            price = float(data[3])
            cap = float(data[45])
            shares = cap / price if price > 0 else 0
            
            today_shares += shares
            today_amt += cap
            
            current_details[code] = {
                "shares": round(shares, 2),
                "cap": round(cap, 2)
            }

    # 计算全市场市值 (万亿)
    mkt_cap = 0.0
    if "sh000001" in data_map:
        mkt_cap += float(data_map["sh000001"][45] or 0)
    if "sz399106" in data_map:
        mkt_cap += float(data_map["sz399106"][45] or 0)
    mkt_cap = round(mkt_cap / 10000, 2)

    # 2. 读取/创建 history.json
    filename = 'history.json'
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = {}

    # 3. 更新今日数据
    # 只有当今天不是周末(金额>0)才保存，这里简单判断
    if today_amt > 0:
        history[today_str] = {
            "date": today_str,
            "totalShares": round(today_shares, 2),
            "totalCap": round(today_amt, 2),
            "marketCap": mkt_cap,
            "details": current_details
        }
        print(f"✅ Data for {today_str} prepared.")

    # 4. 写入文件
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    print("✅ history.json updated.")

if __name__ == "__main__":
    main()