import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional
from config.settings import LOG_CONFIG


class ColoredFormatter(logging.Formatter):
    """带颜色的日志格式化器（仅用于控制台）"""

    # 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',  # 青色
        'INFO': '\033[32m',  # 绿色
        'WARNING': '\033[33m',  # 黄色
        'ERROR': '\033[31m',  # 红色
        'CRITICAL': '\033[35m',  # 紫色
        'RESET': '\033[0m'  # 重置
    }

    def format(self, record):
        # 创建记录的副本，避免修改原始记录
        record_copy = logging.makeLogRecord(record.__dict__)

        # 添加颜色
        if record_copy.levelname in self.COLORS:
            record_copy.levelname = f"{self.COLORS[record_copy.levelname]}{record_copy.levelname}{self.COLORS['RESET']}"

        return super().format(record_copy)


class OnCallLogger:
    """OnCall系统日志管理器"""

    _instance = None
    _logger = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OnCallLogger, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if self._logger is None:
            self._setup_logger()

    def _setup_logger(self):
        """设置日志器"""
        # 创建日志器
        self._logger = logging.getLogger('oncall')
        self._logger.setLevel(getattr(logging, LOG_CONFIG['level']))

        # 清除已有的处理器
        self._logger.handlers.clear()

        # 确保日志目录存在
        log_dir = LOG_CONFIG['log_dir']
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # 设置格式器
        formatter = logging.Formatter(
            LOG_CONFIG['format'],
            datefmt=LOG_CONFIG['date_format']
        )

        # 彩色控制台格式器
        colored_formatter = ColoredFormatter(
            LOG_CONFIG['format'],
            datefmt=LOG_CONFIG['date_format']
        )

        # 控制台处理器
        if LOG_CONFIG['console_output']:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, LOG_CONFIG['console_level']))
            console_handler.setFormatter(colored_formatter)
            self._logger.addHandler(console_handler)

        # 文件处理器
        if LOG_CONFIG['file_output']:
            # 主日志文件
            log_file = os.path.join(log_dir, LOG_CONFIG['log_file'])
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=LOG_CONFIG['max_bytes'],
                backupCount=LOG_CONFIG['backup_count'],
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, LOG_CONFIG['file_level']))
            file_handler.setFormatter(formatter)  # 使用普通格式器，确保无颜色
            self._logger.addHandler(file_handler)

            # 错误日志文件
            error_log_file = os.path.join(log_dir, LOG_CONFIG['error_log_file'])
            error_handler = logging.handlers.RotatingFileHandler(
                error_log_file,
                maxBytes=LOG_CONFIG['max_bytes'],
                backupCount=LOG_CONFIG['backup_count'],
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)  # 使用普通格式器，确保无颜色
            self._logger.addHandler(error_handler)

    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """获取日志器"""
        if name:
            return logging.getLogger(f'oncall.{name}')
        return self._logger

    def debug(self, message: str, *args, **kwargs):
        """调试日志"""
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """信息日志"""
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """警告日志"""
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """错误日志"""
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """严重错误日志"""
        self._logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        """异常日志（包含堆栈跟踪）"""
        self._logger.exception(message, *args, **kwargs)


# 创建全局日志实例
logger = OnCallLogger()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """获取日志器的便捷函数"""
    return logger.get_logger(name)


# 装饰器：记录函数执行时间
def log_execution_time(func):
    """记录函数执行时间的装饰器"""

    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        func_name = f"{func.__module__}.{func.__name__}"

        logger.info(f"开始执行函数: {func_name}")

        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"函数执行完成: {func_name}, 耗时: {execution_time:.3f}秒")
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"函数执行失败: {func_name}, 耗时: {execution_time:.3f}秒, 错误: {str(e)}")
            raise

    return wrapper


# 装饰器：记录API请求
def log_api_request(func):
    """记录API请求的装饰器"""

    def wrapper(*args, **kwargs):
        func_name = f"{func.__module__}.{func.__name__}"
        logger.info(f"API请求: {func_name}")

        try:
            result = func(*args, **kwargs)
            logger.info(f"API响应成功: {func_name}")
            return result
        except Exception as e:
            logger.error(f"API响应失败: {func_name}, 错误: {str(e)}")
            raise

    return wrapper


# 上下文管理器：记录代码块执行
class LogContext:
    """日志上下文管理器"""

    def __init__(self, message: str, level: str = 'info'):
        self.message = message
        self.level = level
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        getattr(logger, self.level)(f"开始: {self.message}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = (datetime.now() - self.start_time).total_seconds()

        if exc_type is None:
            getattr(logger, self.level)(f"完成: {self.message}, 耗时: {execution_time:.3f}秒")
        else:
            logger.error(f"失败: {self.message}, 耗时: {execution_time:.3f}秒, 错误: {str(exc_val)}")

        return False  # 不抑制异常


# 便捷函数
def log_function_call(func_name: str, args: tuple = None, kwargs: dict = None):
    """记录函数调用"""
    args_str = str(args) if args else "()"
    kwargs_str = str(kwargs) if kwargs else "{}"
    logger.debug(f"调用函数: {func_name}{args_str}{kwargs_str}")


def log_dingtalk_message(content: str, success: bool = True):
    """记录钉钉消息发送"""
    status = "成功" if success else "失败"
    logger.info(f"钉钉消息发送{status}: {content[:50]}...")


def log_excel_operation(operation: str, file_path: str, success: bool = True):
    """记录Excel操作"""
    status = "成功" if success else "失败"
    logger.info(f"Excel操作{status}: {operation} - {file_path}")


def log_schedule_task(task_name: str, success: bool = True, details: str = ""):
    """记录定时任务"""
    status = "成功" if success else "失败"
    message = f"定时任务{status}: {task_name}"
    if details:
        message += f" - {details}"
    logger.info(message)