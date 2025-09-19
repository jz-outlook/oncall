from datetime import datetime, timedelta
import pandas as pd
import math  # 用于计算最小公倍数
from config import duty_persons  # 从配置文件导入值班人员列表


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
            date_str = current_date.strftime("%Y-%m-%d")
            weekday = current_date.weekday()  # 0=周一, 6=周日
            weekday_str = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][weekday]

            # 通用轮值逻辑：无论人数多少，都按“当前天数%人数”分配（间隔=人数，天然≥5天）
            person_index = i % people_count
            person_name = duty_persons[person_index]["name"]

            schedule_data.append({
                "日期": date_str,
                "周几": weekday_str,
                "姓名": person_name
            })

        return pd.DataFrame(schedule_data)

    except Exception as e:
        print(f"生成值班计划失败：{e}")
        return None


def check_duty_schedule(schedule_df):
    """
    检查值班计划是否符合规则（完全适配人数动态变化）
    规则：1.每天有值班 2.间隔≥5天 3.周末分布差异≤1天
    """
    if schedule_df is None or schedule_df.empty:
        return {"passed": False, "message": "值班计划为空"}

    try:
        result = {
            "passed": True,
            "message": "值班计划符合所有规则",
            "details": [],
            "statistics": {}  # 每人统计：总天数、周末天数、间隔范围/平均
        }

        # 1. 检查每天是否有值班（无“休息”）
        no_duty = schedule_df[schedule_df["姓名"].isin(["休息", ""])]
        if not no_duty.empty:
            result["passed"] = False
            result["details"].append(f"发现{len(no_duty)}天未安排值班，不符合规则")

        # 2. 收集每人值班日期并统计（适配任意人数）
        person_dates = {}
        for _, row in schedule_df.iterrows():
            name = row["姓名"]
            if name not in ["休息", ""]:
                if name not in person_dates:
                    person_dates[name] = []
                person_dates[name].append(datetime.strptime(row["日期"], "%Y-%m-%d"))

        # 3. 初始化统计信息
        for person in person_dates.keys():
            result["statistics"][person] = {
                "total_days": 0,
                "min_interval": None,
                "max_interval": None,
                "avg_interval": 0.0,
                "weekend_days": 0
            }

        # 4. 检查间隔+补充统计（适配任意人数）
        for person, dates in person_dates.items():
            dates_sorted = sorted(dates)
            intervals = []

            # 统计总值班天数
            result["statistics"][person]["total_days"] = len(dates_sorted)

            # 统计周末值班天数（周六=5，周日=6）
            for date in dates_sorted:
                if date.weekday() >= 5:
                    result["statistics"][person]["weekend_days"] += 1

            # 计算间隔（相邻两次值班的天数差）
            for i in range(1, len(dates_sorted)):
                days_diff = (dates_sorted[i] - dates_sorted[i - 1]).days
                intervals.append(days_diff)

                # 检查间隔是否≥5天
                if days_diff < 5:
                    result["passed"] = False
                    result["details"].append(
                        f"{person}的值班间隔不足5天：{dates_sorted[i - 1].strftime('%Y-%m-%d')}与{dates_sorted[i].strftime('%Y-%m-%d')}，间隔{days_diff}天"
                    )

            # 补充间隔统计（最小值/最大值/平均值）
            if intervals:
                result["statistics"][person]["min_interval"] = min(intervals)
                result["statistics"][person]["max_interval"] = max(intervals)
                result["statistics"][person]["avg_interval"] = round(sum(intervals) / len(intervals), 1)

        # 5. 检查周末值班分布是否均衡（差异≤1天）
        if person_dates:  # 避免空列表报错
            weekend_counts = [stats["weekend_days"] for stats in result["statistics"].values()]
            max_weekend = max(weekend_counts)
            min_weekend = min(weekend_counts)

            if max_weekend - min_weekend > 1:
                result["passed"] = False
                result["details"].append(f"周末值班分布不均：最多{max_weekend}天，最少{min_weekend}天")

        # 整理结果信息
        if not result["passed"]:
            result["message"] = "值班计划存在不符合规则的地方，请查看详情"
        else:
            result["message"] = f"值班计划符合所有规则（当前{len(person_dates)}人，周期{len(schedule_df)}天）"

        return result

    except Exception as e:
        return {"passed": False, "message": f"检查值班计划失败：{e}"}


# 使用示例（适配任意人数）
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

        # 检查计划
        check_result = check_duty_schedule(schedule)
        print("\n=== 检查结果 ===")
        print(f"是否通过：{'✅ 是' if check_result['passed'] else '❌ 否'}")
        print(f"说明：{check_result['message']}")

        # 打印问题详情（如有）
        if check_result["details"]:
            print("\n❌ 详细问题：")
            for idx, detail in enumerate(check_result["details"], 1):
                print(f"  {idx}. {detail}")

        # 打印每人统计信息
        print("\n=== 值班统计信息 ===")
        for person, stats in check_result["statistics"].items():
            print(f"{person}：总值班{stats['total_days']}天 | 周末{stats['weekend_days']}天 | "
                  f"间隔{stats['min_interval']}-{stats['max_interval']}天（平均{stats['avg_interval']}天）")

        # 预览前N天计划（N=人数，方便快速查看轮值逻辑）
        preview_days = min(people_count * 2, 20)  # 预览“2倍人数”或最多20天
        print(f"\n=== 前{preview_days}天计划预览 ===")
        print(schedule.head(preview_days).to_string(index=False))
