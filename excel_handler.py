
import pandas as pd
from datetime import datetime, timedelta

from config import ORIGINAL_DUTY_EXCEL, bug_persons
from dingtalk import send_dingtalk_message
from test import generate_duty_schedule


def get_today_date():
    """获取今天日期（格式：YYYY-MM-DD）"""
    return datetime.now().strftime("%Y-%m-%d")


def get_bug_assignment_person(test_data=None):
    """
    获取指定日期的禅道指派人员
    使用简单的轮换逻辑：根据日期计算应该指派的人员

    参数:
        test_data: 测试日期字符串，格式"YYYY-MM-DD"，默认为今天

    返回:
        指派人员的姓名，如果没有配置则返回None
    """
    if not bug_persons:
        print("警告：禅道指派人员列表为空")
        return None

    try:
        # 如果没有指定日期，使用今天
        if test_data is None:
            target_date = datetime.now()
        else:
            target_date = datetime.strptime(test_data, "%Y-%m-%d")

        # 使用日期作为种子进行轮换
        # 从2025-01-01开始计算天数差，确保轮换的一致性
        base_date = datetime(2025, 1, 1)
        days_diff = (target_date - base_date).days

        # 根据天数差和人员数量进行轮换
        person_index = days_diff % len(bug_persons)
        assigned_person = bug_persons[person_index]["name"]

        return assigned_person

    except Exception as e:
        print(f"获取禅道指派人员失败：{str(e)}")
        return None


def replace_dates(df, start_date_str=None):
    """
    替换DataFrame中的日期列，从指定日期开始按顺序排列

    参数:
        df: 包含姓名和日期的DataFrame
        start_date_str: 起始日期字符串，格式"YYYY-MM-DD"，默认为今天

    返回:
        更新日期后的DataFrame
    """
    if start_date_str is None:
        current_date = datetime.now()
    else:
        current_date = datetime.strptime(start_date_str, '%Y-%m-%d')

    # 遍历数据框的每一行，更新日期
    for i in range(len(df)):
        df.at[i, '日期'] = current_date.strftime('%Y-%m-%d')
        current_date += timedelta(days=1)

    return df


def get_original_duty_person(test_data):
    """从原始值班表获取指定日期的值班人员"""
    date = get_today_date()  # 假设返回"YYYY-MM-DD"格式的字符串
    required_columns = ["日期", "姓名"]  # 必需的列名

    try:
        # 读取Excel文件
        df = pd.read_excel(ORIGINAL_DUTY_EXCEL)

        # 检查必需的列是否存在
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            # 打印实际存在的列名，方便排查
            actual_columns = ", ".join(df.columns.tolist())
            print(f"错误：Excel文件中缺少必需的列：{', '.join(missing_columns)}")
            print(f"Excel文件中实际存在的列：{actual_columns}")
            return None

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

        df['日期'] = df['日期'].apply(parse_date)

        # 查找目标日期的值班信息
        duty_info = df[df["日期"] == date]
        if not duty_info.empty:
            duty_person = duty_info["姓名"].values[0]
            return str(duty_person).strip() if pd.notna(duty_person) else None
        else:
            print(f"提示：未在值班表中找到{date}的值班记录")
            # 使用replace_dates方法更新日期
            updated_df = replace_dates(df.copy(), start_date_str=date)
            if updated_df is not None:
                # 保存更新后的Excel文件
                filename = f"值班计划表.xlsx"
                updated_df.to_excel(filename, index=False)
                print(f"\n值班计划已保存：{filename}")

                # 重新读取更新后的文件
                df = pd.read_excel(ORIGINAL_DUTY_EXCEL)
                df['日期'] = df['日期'].apply(parse_date)

                # 再次查找目标日期的值班信息
                duty_info = df[df["日期"] == date]
                if not duty_info.empty:
                    duty_person = duty_info["姓名"].values[0]
                    return str(duty_person).strip() if pd.notna(duty_person) else None

    except Exception as e:
        print(f"读取原始值班表失败：{str(e)}")
        return None