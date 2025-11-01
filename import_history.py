import os
import logging
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.services.realtime_data_manager import RealtimeDataManager
from app.models.stock_basic import StockBasic
import baostock as bs

# --- 配置日志 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 主程序 ---
def main():
    app = create_app()
    with app.app_context():
        logger.info("--- 开始执行历史数据导入任务 ---")

        data_manager = RealtimeDataManager()

        # 1. 获取所有A股列表并存入stock_basic表
        logger.info("正在从Baostock获取所有A股列表...")
        lg = bs.login()
        if lg.error_code != '0':
            logger.error(f"Baostock登录失败: {lg.error_msg}")
            bs.logout()
            return

        rs = bs.query_stock_basic()
        stock_list = []
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            # 只选择A股（sh或sz开头），且状态为1（上市）
            if (row[0].startswith('sh') or row[0].startswith('sz')) and row[2] == '1':
                stock_list.append(row)
        bs.logout()
        logger.info(f"成功获取 {len(stock_list)} 只A股股票信息。")

        logger.info("正在清空并重新写入 stock_basic 表...")
        try:
            StockBasic.query.delete()
            db.session.commit()
            for stock_data in stock_list:
                stock_basic = StockBasic(
                    ts_code=stock_data[0],
                    name=stock_data[1],
                    area='',
                    industry='',
                    market='',
                    list_date=stock_data[3]
                )
                db.session.add(stock_basic)
            db.session.commit()
            logger.info("stock_basic 表更新完成！")
        except Exception as e:
            db.session.rollback()
            logger.error(f"更新 stock_basic 表时出错: {e}", exc_info=True)
            return

        # 2. 获取所有股票的历史分钟数据
        all_ts_codes = [stock[0] for stock in stock_list]
        logger.info(f"将为 {len(all_ts_codes)} 只股票导入历史分钟数据...")

        # 定义历史数据范围（例如，从2020年1月1日至今）
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = "2020-01-01"
        logger.info(f"历史数据导入范围: {start_date} 到 {end_date}")

        try:
            update_result = data_manager.sync_multiple_stocks_data(
                all_ts_codes,
                period_type="1min",
                start_date=start_date,
                end_date=end_date,
                use_baostock=True
            )
            logger.info(f"历史数据导入操作完成: {update_result}")
        except Exception as e:
            logger.error(f"历史数据导入过程中发生严重错误: {e}", exc_info=True)

        logger.info("--- 历史数据导入任务执行完毕 ---")

if __name__ == "__main__":
    main()
