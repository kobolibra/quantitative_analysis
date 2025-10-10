import os
from dotenv import load_dotenv
from datetime import timedelta
from urllib.parse import urlparse, parse_qs

# 加载环境变量
load_dotenv()

class Config:
    """基础配置类"""
    
    # 数据库配置
    # 优先从环境变量 DATABASE_URL 中读取完整的数据库连接字符串
    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL:
        # 如果 DATABASE_URL 存在，则解析它来设置 DB_HOST, DB_USER 等
        parsed_uri = urlparse(DATABASE_URL)
        
        DB_USER = parsed_uri.username
        DB_PASSWORD = parsed_uri.password
        DB_HOST = parsed_uri.hostname
        DB_PORT = parsed_uri.port if parsed_uri.port else 3306 # 默认MySQL端口
        DB_NAME = parsed_uri.path.lstrip("/")
        
        query_params = parse_qs(parsed_uri.query)
        DB_CHARSET = query_params.get("charset", ["utf8mb4"])[0]
        
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # 如果 DATABASE_URL 不存在，则使用原来的方式从单独的环境变量或默认值获取
        DB_HOST = os.getenv("DB_HOST", "mysql2.sqlpub.com")
        DB_USER = os.getenv("DB_USER", "liquidity")
        DB_PASSWORD = os.getenv("DB_PASSWORD", "ZvdbAoGQGX0Pki1b")
        DB_NAME = os.getenv("DB_NAME", "quantitativeanalysis")
        DB_CHARSET = os.getenv("DB_CHARSET", "utf8mb4")
        DB_PORT = int(os.getenv("DB_PORT", 3307)) # 确保端口号也被设置
        
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset={DB_CHARSET}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Redis配置
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    
    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/stock_analysis.log')
    
    # 数据更新配置
    DATA_UPDATE_HOUR = int(os.getenv('DATA_UPDATE_HOUR', 18))  # 每日18点更新数据
    DATA_UPDATE_MINUTE = int(os.getenv('DATA_UPDATE_MINUTE', 0))
    
    # 预警配置
    EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.qq.com')
    EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', 587))
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', '')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
    
    # 分页配置
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # 大模型配置
    LLM_CONFIG = {
        'provider': 'ollama',  # 支持 'ollama', 'openai', 'azure'
        'ollama': {
            'base_url': 'http://localhost:11434',
            'model': 'qwen2.5-coder:latest',
            'timeout': 60,
            'temperature': 0.1,
            'max_tokens': 2048
        },
        'openai': {
            'api_key': os.environ.get('OPENAI_API_KEY' ),
            'model': 'gpt-3.5-turbo',
            'base_url': 'https://api.openai.com/v1',
            'timeout': 60,
            'temperature': 0.1,
            'max_tokens': 2048
        }
    }

class DevelopmentConfig(Config ):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False

# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
