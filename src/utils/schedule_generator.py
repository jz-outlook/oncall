from datetime import datetime, timedelta
import pandas as pd
import math  # 用于计算最小公倍数
from config.settings import duty_persons  # 从配置文件导入值班人员列表


def calculate_lcm(a, b):
    """辅助函数：计算两个数的最小公倍数（LCM）"""
    # 最小公倍数 = 两数乘积 // 最大公约数（GCD），math.gcd返回非负整数
    return a * b // math.gcd(a, b)


def generate_duty_schedule(cycle_days=None, start_date_str=None):
    """
    生成间隔均衡的值班计划，支持人员数量动态变化
    核心优化：周期自动适配人数，人数不足时主动提示

    参数:
        cycle_days: 值班周期天数（可选，默认=人数与7的最小公倍数，保证长期均衡）
        start_date_str: 起始日期字符串（格式"YYYY-MM-DD"，默认=今天）
    返回:
        包含日期、周几、姓名的DataFrame，或None（人数不合法时）
    """
    # 1. 基础校验：人员列表非空
    if not duty_persons:
        print("错误：值班人员列表为空")
        return None

    people_count = len(duty_persons)  # 当前实际人数
    min_required_people = 5  # 最少需要5人（否则间隔无法≥5天）

    # 2. 人数合法性校验：确保间隔不小于5天
    if people_count < min_required_people:
        print(f"错误：当前仅{people_count}人，最少需要{min_required_people}人（否则值班间隔会小于5天）")
        return None

    try:
        # 3. 动态确定周期：默认=人数与7（一周）的最小公倍数（保证周末值班长期均衡）
        if cycle_days is None:
            cycle_days = calculate_lcm(people_count, 7)
            print(f"自动适配周期：{people_count}人与7天的最小公倍数={cycle_days}天")

        # 4. 解析起始日期（默认今天）
        if start_date_str is None:
            start_date = datetime.now()
        else:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")

        # 5. 生成排班数据（核心逻辑：i % 人数 适配任意人数）
        schedule_data = []
        for i in range(cycle_days):
            current_date = start_date + timedelta(days=i)
            weekday = current_date.strftime("%A")  # 英文星期名
            weekday_cn = {
                "Monday": "周一", "Tuesday": "周二", "Wednesday": "周三",
                "Thursday": "周四", "Friday": "周五", "Saturday": "周六", "Sunday": "周日"
            }[weekday]

            # 通用轮值逻辑：无论人数多少，都按"当前天数%人数"分配（间隔=人数，天然≥5天）
            person_index = i % people_count
            person_name = duty_persons[person_index]["name"]

            schedule_data.append({
                "日期": current_date.strftime("%Y-%m-%d"),
                "周几": weekday_cn,
                "姓名": person_name
            })

        # 6. 转换为DataFrame并返回
        schedule_df = pd.DataFrame(schedule_data)
        print(f"成功生成{cycle_days}天的值班计划（{people_count}人轮值，间隔{people_count}天）")
        return schedule_df

    except Exception as e:
        print(f"生成值班计划时发生错误：{str(e)}")
        return None


def analyze_schedule_balance(schedule_df):
    """
    分析值班计划的均衡性

    参数:
        schedule_df: 包含日期、周几、姓名的DataFrame

    返回:
        分析结果字典
    """
    if schedule_df is None or schedule_df.empty:
        return None

    # 统计每人值班次数
    person_counts = schedule_df["姓名"].value_counts()
    total_days = len(schedule_df)

    # 计算理论平均次数
    unique_persons = len(person_counts)
    avg_count = total_days / unique_persons

    # 分析结果
    analysis = {
        "total_days": total_days,
        "unique_persons": unique_persons,
        "avg_count": avg_count,
        "person_counts": person_counts.to_dict(),
        "max_count": person_counts.max(),
        "min_count": person_counts.min(),
        "balance_score": 1 - (person_counts.max() - person_counts.min()) / avg_count if avg_count > 0 else 0
    }

    return analysis


def print_schedule_analysis(analysis):
    """打印值班计划分析结果"""
    if not analysis:
        print("无法分析值班计划")
        return

    print("\n值班计划均衡性分析:")
    print("-" * 50)
    print(f"总天数: {analysis['total_days']}")
    print(f"参与人数: {analysis['unique_persons']}")
    print(f"理论平均次数: {analysis['avg_count']:.1f}")
    print(f"实际最高次数: {analysis['max_count']}")
    print(f"实际最低次数: {analysis['min_count']}")
    print(f"均衡度评分: {analysis['balance_score']:.2f} (1.0为完全均衡)")

    print("\n每人值班次数详情:")
    for person, count in sorted(analysis['person_counts'].items()):
        print(f"  {person}: {count}次")


if __name__ == "__main__":
    # 生成计划（无需手动指定周期，自动适配人数）
    schedule = generate_duty_schedule()

    if schedule is not None:
        # 保存Excel（文件名含当前日期和人数）
        today_str = datetime.now().strftime("%Y%m%d")
        people_count = len(duty_persons)
        filename = f"{today_str}_{people_count}人_{len(schedule)}天值班计划表.xlsx"
        schedule.to_excel(filename, index=False)
        print(f"\n值班计划已保存：{filename}")

        # 分析均衡性
        analysis = analyze_schedule_balance(schedule)
        print_schedule_analysis(analysis)

        # 显示前10天计划预览
        print(f"\n前10天值班计划预览:")
        print(schedule.head(10).to_string(index=False))
    else:
        print("值班计划生成失败")
