import os
import logging
from datetime import datetime, timedelta
from app import create_app
from app.services.realtime_data_manager import RealtimeDataManager
from app.models.stock_basic import StockBasic

# --- 配置日志 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 主程序 ---
def main():
    app = create_app()
    with app.app_context():
        logger.info("--- 开始执行每日数据更新任务 ---")

        period_type = os.getenv("PERIOD_TYPE", "1min")
        logger.info(f"使用的数据周期类型: {period_type}")

        data_manager = RealtimeDataManager()
        
        stock_basics = StockBasic.query.all()
        if not stock_basics:
            logger.warning("数据库中没有找到股票基本信息，任务终止。请先导入历史数据。")
            return

        ts_codes = [stock.ts_code for stock in stock_basics]
        logger.info(f"将为 {len(ts_codes)} 只股票更新数据。")

        # 每日更新只获取最近一天的数据
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        logger.info(f"数据更新范围: {start_date} 到 {end_date}")

        try:
            update_result = data_manager.sync_multiple_stocks_data(
                ts_codes,
                period_type=period_type,
                start_date=start_date,
                end_date=end_date,
                use_baostock=True
            )
            logger.info(f"数据同步操作完成: {update_result}")
        except Exception as e:
            logger.error(f"数据同步过程中发生严重错误: {e}", exc_info=True)
        
        logger.info("--- 每日数据更新任务执行完毕 ---")

if __name__ == "__main__":
    main()
