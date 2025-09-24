"""
日志工具模块
提供各种便捷的日志记录功能
"""

import functools
import time
from typing import Any, Callable, Optional
from .logger import get_logger, LogContext


def log_performance(threshold_seconds: float = 1.0):
    """性能监控装饰器

    Args:
        threshold_seconds: 超过此时间才记录警告
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            func_name = f"{func.__module__}.{func.__name__}"

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                if execution_time > threshold_seconds:
                    get_logger().warning(
                        f"性能警告: {func_name} 执行时间 {execution_time:.3f}秒 "
                        f"(超过阈值 {threshold_seconds}秒)"
                    )
                else:
                    get_logger().debug(f"{func_name} 执行时间: {execution_time:.3f}秒")

                return result
            except Exception as e:
                execution_time = time.time() - start_time
                get_logger().error(
                    f"函数执行异常: {func_name}, 耗时: {execution_time:.3f}秒, "
                    f"错误: {str(e)}"
                )
                raise

        return wrapper

    return decorator


def log_retry(max_retries: int = 3, delay: float = 1.0):
    """重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            func_name = f"{func.__module__}.{func.__name__}"

            for attempt in range(max_retries + 1):
                try:
                    if attempt > 0:
                        get_logger().info(f"重试 {attempt}/{max_retries}: {func_name}")
                        time.sleep(delay)

                    result = func(*args, **kwargs)
                    if attempt > 0:
                        get_logger().info(f"重试成功: {func_name}")
                    return result

                except Exception as e:
                    if attempt == max_retries:
                        get_logger().error(
                            f"重试失败: {func_name}, 已重试 {max_retries} 次, "
                            f"最终错误: {str(e)}"
                        )
                        raise
                    else:
                        get_logger().warning(
                            f"重试 {attempt + 1}/{max_retries}: {func_name}, "
                            f"错误: {str(e)}"
                        )

        return wrapper

    return decorator


class LogTimer:
    """日志计时器"""

    def __init__(self, message: str, level: str = 'info'):
        self.message = message
        self.level = level
        self.start_time = None
        self.logger = get_logger()

    def start(self):
        """开始计时"""
        self.start_time = time.time()
        getattr(self.logger, self.level)(f"开始: {self.message}")

    def stop(self, success: bool = True):
        """停止计时"""
        if self.start_time is None:
            return

        execution_time = time.time() - self.start_time
        status = "完成" if success else "失败"
        getattr(self.logger, self.level)(
            f"{status}: {self.message}, 耗时: {execution_time:.3f}秒"
        )

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        success = exc_type is None
        self.stop(success)
        return False


def log_data_operation(operation_type: str, data_source: str, record_count: Optional[int] = None):
    """记录数据操作

    Args:
        operation_type: 操作类型 (read, write, update, delete)
        data_source: 数据源 (文件路径、数据库表等)
        record_count: 记录数量
    """
    logger = get_logger()
    message = f"数据操作: {operation_type} - {data_source}"

    if record_count is not None:
        message += f" (记录数: {record_count})"

    logger.info(message)


def log_external_api_call(api_name: str, url: str, method: str = "GET",
                          status_code: Optional[int] = None, response_time: Optional[float] = None):
    """记录外部API调用

    Args:
        api_name: API名称
        url: 请求URL
        method: HTTP方法
        status_code: 响应状态码
        response_time: 响应时间（秒）
    """
    logger = get_logger()
    message = f"外部API调用: {api_name} - {method} {url}"

    if status_code is not None:
        message += f" (状态码: {status_code})"

    if response_time is not None:
        message += f" (响应时间: {response_time:.3f}秒)"

    if status_code and status_code >= 400:
        logger.error(message)
    else:
        logger.info(message)


def log_business_event(event_type: str, details: str, user: Optional[str] = None):
    """记录业务事件

    Args:
        event_type: 事件类型
        details: 事件详情
        user: 操作用户
    """
    logger = get_logger()
    message = f"业务事件: {event_type} - {details}"

    if user:
        message += f" (用户: {user})"

    logger.info(message)


def log_system_status(component: str, status: str, details: str = ""):
    """记录系统状态

    Args:
        component: 组件名称
        status: 状态 (running, stopped, error, warning)
        details: 详细信息
    """
    logger = get_logger()
    message = f"系统状态: {component} - {status}"

    if details:
        message += f" ({details})"

    if status in ['error', 'stopped']:
        logger.error(message)
    elif status == 'warning':
        logger.warning(message)
    else:
        logger.info(message)