import pandas as pd
from datetime import datetime, timedelta
from config.settings import ORIGINAL_DUTY_EXCEL, bug_persons
from src.services.dingtalk import send_dingtalk_message
from src.utils.logger import get_logger, log_execution_time, LogContext
import os

# 获取日志器
logger = get_logger('excel_handler')


def get_today_date():
    """获取今天日期（格式：YYYY-MM-DD）"""
    today = datetime.now().strftime("%Y-%m-%d")
    logger.debug(f"获取今天日期: {today}")
    return today


@log_execution_time
def get_bug_assignment_person(test_data=None):
    """
    获取指定日期的禅道指派人员
    使用简单的轮换逻辑：根据日期计算应该指派的人员

    参数:
        test_data: 测试日期字符串，格式"YYYY-MM-DD"，默认为今天

    返回:
        指派人员的姓名，如果没有配置则返回None
    """
    logger.info(f"开始获取禅道指派人员，测试数据: {test_data}")

    if not bug_persons:
        logger.warning("⚠️ 禅道指派人员列表为空")
        return None

    try:
        # 如果没有指定日期，使用今天
        if test_data is None:
            target_date = datetime.now()
            logger.debug("使用今天作为目标日期")
        else:
            target_date = datetime.strptime(test_data, "%Y-%m-%d")
            logger.debug(f"使用指定日期: {test_data}")

        # 使用日期作为种子进行轮换
        # 从2025-01-01开始计算天数差，确保轮换的一致性
        base_date = datetime(2025, 1, 1)
        days_diff = (target_date - base_date).days
        logger.debug(f"距离基准日期({base_date.strftime('%Y-%m-%d')})的天数差: {days_diff}")

        # 根据天数差和人员数量进行轮换
        person_index = days_diff % len(bug_persons)
        assigned_person = bug_persons[person_index]["name"]

        logger.info(f"✅ 禅道指派人员计算完成: {assigned_person} (索引: {person_index}, 总人数: {len(bug_persons)})")
        return assigned_person

    except Exception as e:
        logger.error(f"❌ 获取禅道指派人员失败: {str(e)}")
        return None


@log_execution_time
def replace_dates(df, start_date_str=None):
    """
    替换DataFrame中的日期列，从指定日期开始按顺序排列

    参数:
        df: 包含姓名和日期的DataFrame
        start_date_str: 起始日期字符串，格式"YYYY-MM-DD"，默认为今天

    返回:
        更新日期后的DataFrame
    """
    logger.info(f"开始更新DataFrame日期，起始日期: {start_date_str}")

    if start_date_str is None:
        current_date = datetime.now()
        logger.debug("使用今天作为起始日期")
    else:
        current_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        logger.debug(f"使用指定起始日期: {start_date_str}")

    # 遍历数据框的每一行，更新日期
    for i in range(len(df)):
        old_date = df.at[i, '日期']
        new_date = current_date.strftime('%Y-%m-%d')
        df.at[i, '日期'] = new_date
        logger.debug(f"更新第{i + 1}行日期: {old_date} -> {new_date}")
        current_date += timedelta(days=1)

    logger.info(f"✅ DataFrame日期更新完成，共更新{len(df)}行")
    return df


@log_execution_time
def get_original_duty_person(test_data):
    """从原始值班表获取指定日期的值班人员"""
    logger.info(f"开始查询值班人员，测试数据: {test_data}")

    # 如果没有指定日期，使用今天
    if test_data is None:
        date = get_today_date()
        logger.debug("使用今天作为查询日期")
    else:
        date = test_data
        logger.debug(f"使用指定查询日期: {date}")

    required_columns = ["日期", "姓名"]  # 必需的列名
    logger.debug(f"Excel文件路径: {ORIGINAL_DUTY_EXCEL}")

    try:
        # 读取Excel文件
        logger.info(" 开始读取Excel文件")
        df = pd.read_excel(ORIGINAL_DUTY_EXCEL)
        logger.info(f"✅ Excel文件读取成功，共{len(df)}行数据")

        # 检查必需的列是否存在
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            # 打印实际存在的列名，方便排查
            actual_columns = ", ".join(df.columns.tolist())
            logger.error(f"❌ Excel文件中缺少必需的列: {', '.join(missing_columns)}")
            logger.error(f"Excel文件中实际存在的列: {actual_columns}")
            return None

        logger.debug(f"Excel文件列名检查通过: {list(df.columns)}")

        # 处理日期列（兼容多种格式）
        def parse_date(x):
            # 数值型（Excel日期序列）
            if isinstance(x, (int, float)):
                return (datetime(1899, 12, 30) + timedelta(days=x)).strftime("%Y-%m-%d")
            # 字符串型（尝试常见格式）
            elif isinstance(x, str):
                for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%m/%d/%Y",
                            "%Y年%m月%d日", "%m月%d日%Y年"]:
                    try:
                        return datetime.strptime(x, fmt).strftime("%Y-%m-%d")
                    except ValueError:
                        continue
                return x  # 无法解析的格式返回原始值
            else:
                return str(x)  # 其他类型转字符串

        logger.debug("开始解析日期列")
        df['日期'] = df['日期'].apply(parse_date)
        logger.debug("日期列解析完成")

        # 查找目标日期的值班信息
        logger.info(f"🔍 查找日期 {date} 的值班信息")
        duty_info = df[df["日期"] == date]

        if not duty_info.empty:
            duty_person = duty_info["姓名"].values[0]
            result = str(duty_person).strip() if pd.notna(duty_person) else None
            logger.info(f"✅ 找到值班人员: {result}")
            return result
        else:
            logger.warning(f"⚠️ 未在值班表中找到{date}的值班记录，开始更新值班计划")

            # 使用replace_dates方法更新日期
            with LogContext("更新值班计划表"):
                updated_df = replace_dates(df.copy(), start_date_str=date)
                if updated_df is not None:
                    # 保存更新后的Excel文件到正确路径
                    filename = "./data/值班计划表.xlsx"
                    logger.info(f"💾 保存更新后的值班计划到: {filename}")
                    updated_df.to_excel(filename, index=False)
                    logger.info(f"✅ 值班计划已保存: {filename}")

                    # 发送Excel文件到钉钉群
                    push_message = f"📋 值班计划表已更新\n更新日期：{date}\n下载地址：http://myai.myds.me:5008/api/download_duty_schedule"
                    send_dingtalk_message(push_message)

                    # 重新读取更新后的文件
                    logger.info(" 重新读取更新后的文件")
                    df = pd.read_excel(ORIGINAL_DUTY_EXCEL)
                    df['日期'] = df['日期'].apply(parse_date)

                    # 再次查找目标日期的值班信息
                    logger.info(f"🔍 重新查找日期 {date} 的值班信息")
                    duty_info = df[df["日期"] == date]
                    if not duty_info.empty:
                        duty_person = duty_info["姓名"].values[0]
                        result = str(duty_person).strip() if pd.notna(duty_person) else None
                        logger.info(f"✅ 更新后找到值班人员: {result}")
                        return result
                    else:
                        logger.error(f"❌ 更新后仍未找到{date}的值班信息")
                        return None
                else:
                    logger.error("❌ 更新值班计划失败")
                    return None

    except FileNotFoundError:
        logger.error(f"❌ Excel文件不存在: {ORIGINAL_DUTY_EXCEL}")
        return None
    except Exception as e:
        logger.error(f"❌ 读取原始值班表失败: {str(e)}")
        return None


# 便捷函数：记录Excel操作
def log_excel_operation(operation: str, file_path: str, success: bool = True, details: str = ""):
    """记录Excel操作日志"""
    status = "成功" if success else "失败"
    message = f"Excel操作{status}: {operation} - {file_path}"
    if details:
        message += f" ({details})"

    if success:
        logger.info(message)
    else:
        logger.error(message)