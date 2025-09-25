from app import create_app
from app.services.realtime_data_manager import RealtimeDataManager
from app.models.stock_basic import StockBasic
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

with app.app_context():
    logger.info("开始执行每日数据更新任务...")
    
    # 实例化数据管理器
    # 注意：这里假设Tushare token已通过环境变量设置，否则将使用Baostock
    data_manager = RealtimeDataManager()
    
    # 从数据库获取所有股票代码
    stock_basics = StockBasic.query.all()
    ts_codes = [stock.ts_code for stock in stock_basics]
    
    if not ts_codes:
        logger.warning("数据库中没有找到股票基本信息，请先导入股票基本数据。")
    else:
        logger.info(f"将更新 {len(ts_codes)} 只股票的数据。")
        
        # 定义数据更新的日期范围（例如，更新最近7天的数据）
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        # 批量同步分钟数据 (使用Baostock)
        update_result = data_manager.sync_multiple_stocks_data(
            ts_codes,
            period_type='1min',
            start_date=start_date,
            end_date=end_date,
            use_baostock=True
        )
        
        logger.info(f"每日数据更新任务完成: {update_result}")

    logger.info("每日数据更新任务执行完毕。")

