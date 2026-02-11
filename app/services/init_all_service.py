import baostock as bs
import pandas as pd
from datetime import datetime
from app.extensions import db
from app.models import StockBasic, StockDailyHistory, StockDailyBasic
from app.services.factor_engine import FactorEngine
from app.services.stock_scoring import StockScoringEngine
from loguru import logger
import threading

class InitAllService:
    _is_running = False
    _progress = "未开始"

    @classmethod
    def run_async(cls, start_date="2025-01-01"):
        if cls._is_running:
            return False
        thread = threading.Thread(target=cls._run_sync, args=(start_date,))
        thread.start()
        return True

    @classmethod
    def get_status(cls):
        return {"is_running": cls._is_running, "progress": cls._progress}

    @classmethod
    def _run_sync(cls, start_date):
        cls._is_running = True
        try:
            bs.login()
            cls._progress = "正在获取股票列表..."
            rs = bs.query_all_stock(day=datetime.now().strftime("%Y-%m-%d"))
            stocks = []
            while (rs.error_code == '0') & rs.next():
                stocks.append(rs.get_row_data())
            
            df = pd.DataFrame(stocks, columns=['code', 'tradeStatus', 'code_name'])
            df = df[df['code'].str.contains(r'^sh\.60|^sz\.00|^sz\.30|^sh\.68')]
            target_stocks = df['code'].tolist()
            
            total = len(target_stocks)
            for i, code in enumerate(target_stocks):
                code_parts = code.split('.')
                ts_code = f"{code_parts[1]}.{code_parts[0].upper()}"
                cls._progress = f"正在同步 {ts_code} ({i+1}/{total})"
                
                # 1. 下载行情
                k_rs = bs.query_history_k_data_plus(
                    code, "date,code,open,high,low,close,preclose,volume,amount,pctChg",
                    start_date=start_date, frequency="d", adjustflag="3"
                )
                
                rows = []
                while k_rs.next():
                    rows.append(k_rs.get_row_data())
                
                if rows:
                    # 写入数据库
                    for data in rows:
                        # 写入行情
                        hist = StockDailyHistory.query.filter_by(ts_code=ts_code, trade_date=data[0]).first()
                        if not hist:
                            hist = StockDailyHistory(ts_code=ts_code, trade_date=data[0])
                        hist.open, hist.high, hist.low, hist.close = data[2], data[3], data[4], data[5]
                        hist.pre_close, hist.pct_chg = data[6], data[9]
                        hist.vol = float(data[7]) / 100
                        hist.amount = float(data[8]) / 1000
                        db.session.add(hist)
                        
                        # 写入基础表（用于列表显示）
                        basic = StockDailyBasic.query.filter_by(ts_code=ts_code, trade_date=data[0]).first()
                        if not basic:
                            basic = StockDailyBasic(ts_code=ts_code, trade_date=data[0])
                        basic.close = data[5]
                        db.session.add(basic)
                    
                    db.session.commit()
                    
                    # 2. 计算因子 (每同步完一只股票计算一次)
                    try:
                        FactorEngine.calculate_factors(ts_code)
                    except Exception as fe:
                        logger.error(f"因子计算失败 {ts_code}: {fe}")
                
                # 每 100 只股票进行一次打分更新
                if (i + 1) % 100 == 0:
                    try:
                        StockScoringEngine.update_all_scores()
                    except: pass

            cls._progress = "全部同步完成！"
        except Exception as e:
            cls._progress = f"发生错误: {str(e)}"
            logger.error(cls._progress)
        finally:
            cls._is_running = False
            bs.logout()
