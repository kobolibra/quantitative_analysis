#!/usr/bin/env python3
"""
一键更新脚本 - update_now.py
用途：从 Baostock 获取最新行情数据并更新到数据库
使用方法：python update_now.py
"""

import baostock as bs
import pandas as pd
import pymysql
import os
import sys
from datetime import datetime, timedelta
import time

# 数据库配置
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'mysql2.sqlpub.com'),
    'port': int(os.environ.get('DB_PORT', 3307)),
    'user': os.environ.get('DB_USER', 'liquidity'),
    'password': os.environ.get('DB_PASSWORD', 'ZvdbAoGQGX0Pki1b'),
    'database': os.environ.get('DB_NAME', 'quantitativeanalysis'),
    'charset': 'utf8mb4',
    'connect_timeout': 30,
    'read_timeout': 30,
    'write_timeout': 30
}

def get_trading_days(start_date, end_date):
    """获取交易日期范围"""
    print(f"[INFO] 获取 {start_date} 到 {end_date} 的交易日期...")
    rs = bs.query_trade_dates(start_date=start_date, end_date=end_date)
    dates = []
    while (rs.error_code == '0') & rs.next():
        row = rs.get_row_data()
        if row[1] == '1':  # is_open = 1 表示交易日
            dates.append(row[0])
    return dates

def get_last_update_date(ts_code):
    """获取某只股票的最后更新日期"""
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT MAX(trade_date) FROM stock_business WHERE ts_code = %s",
                (ts_code,)
            )
            result = cursor.fetchone()
            conn.close()
            return result[0] if result[0] else None
    except Exception as e:
        print(f"[ERROR] 获取 {ts_code} 的最后更新日期失败: {e}")
        return None

def fetch_stock_data(ts_code, start_date):
    """从 Baostock 获取股票数据"""
    try:
        rs = bs.query_history_k_data_plus(
            code=ts_code,
            start_date=start_date,
            end_date=datetime.now().strftime("%Y-%m-%d"),
            frequency="d"  # 日线
        )
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        return pd.DataFrame(data_list, columns=rs.fields) if data_list else None
    except Exception as e:
        print(f"[ERROR] 获取 {ts_code} 数据失败: {e}")
        return None

def insert_stock_data(df, ts_code):
    """将股票数据插入数据库"""
    if df is None or df.empty:
        return 0
    
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            inserted = 0
            for _, row in df.iterrows():
                try:
                    sql = """
                    INSERT INTO stock_business 
                    (ts_code, stock_name, trade_date, daily_close, factor_vol, factor_pct_change)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    daily_close=VALUES(daily_close), factor_vol=VALUES(factor_vol), factor_pct_change=VALUES(factor_pct_change)
                    """
                    cursor.execute(sql, (
                        ts_code,
                        row.get('code_name', ''),
                        row.get('trade_date', ''),
                        float(row.get('close', 0)),
                        int(row.get('volume', 0)),
                        float(row.get('pctChg', 0))
                    ))
                    inserted += 1
                except Exception as e:
                    print(f"[WARN] 插入数据失败: {e}")
                    continue
            
            conn.commit()
            conn.close()
            return inserted
    except Exception as e:
        print(f"[ERROR] 数据库连接失败: {e}")
        return 0

def run_update():
    """主更新流程"""
    print("=" * 60)
    print("股票行情数据一键更新工具")
    print("=" * 60)
    
    # 登录 Baostock
    print("\n[1/4] 连接到 Baostock...")
    lg = bs.login()
    if lg.error_code != '0':
        print(f"[ERROR] Baostock 登录失败: {lg.error_msg}")
        return False
    print("[OK] Baostock 登录成功")
    
    # 获取股票列表
    print("\n[2/4] 获取股票列表...")
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("SELECT ts_code FROM stock_basic LIMIT 5000")
            stocks = [row[0] for row in cursor.fetchall()]
            conn.close()
        print(f"[OK] 获取到 {len(stocks)} 只股票")
    except Exception as e:
        print(f"[ERROR] 获取股票列表失败: {e}")
        bs.logout()
        return False
    
    # 更新数据
    print("\n[3/4] 更新行情数据...")
    total_inserted = 0
    for idx, ts_code in enumerate(stocks):
        # 转换格式：600000.SH -> sh.600000
        parts = ts_code.split('.')
        baostock_code = f"{parts[1].lower()}.{parts[0]}"
        
        # 获取最后更新日期
        last_date = get_last_update_date(ts_code)
        start_date = (datetime.strptime(last_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d") if last_date else "2024-01-01"
        
        # 获取并插入数据
        df = fetch_stock_data(baostock_code, start_date)
        inserted = insert_stock_data(df, ts_code)
        total_inserted += inserted
        
        if (idx + 1) % 100 == 0:
            print(f"[PROGRESS] 已处理 {idx + 1}/{len(stocks)} 只股票，已插入 {total_inserted} 条记录")
        
        # 避免请求过于频繁
        time.sleep(0.1)
    
    print(f"[OK] 数据更新完成，共插入 {total_inserted} 条记录")
    
    # 登出
    print("\n[4/4] 清理资源...")
    bs.logout()
    print("[OK] 完成")
    
    print("\n" + "=" * 60)
    print("更新成功！请刷新您的 Render 页面查看最新数据。")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = run_update()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断了更新操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 发生未预期的错误: {e}")
        sys.exit(1)
