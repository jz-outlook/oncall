import pandas as pd
import os


def analyze_name_weekdays_dates(file_path):
    """
    分析表格中每个姓名出现的次数、对应的周几及具体日期

    参数:
        file_path: 表格文件的路径

    返回:
        包含姓名、出现次数、周几及对应日期的字典
    """
    try:
        # 判断文件类型并读取
        file_ext = os.path.splitext(file_path)[1].lower()

        if file_ext == '.csv':
            df = pd.read_csv(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        else:
            print(f"不支持的文件格式: {file_ext}")
            return None

        # 检查是否包含所需列
        required_columns = ["姓名", "周几", "日期"]
        for col in required_columns:
            if col not in df.columns:
                print(f"表格中未找到'{col}'列，请检查表格结构")
                return None

        # 初始化结果字典
        result = {}

        # 周几的排序顺序
        weekday_order = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        # 遍历数据行
        for _, row in df.iterrows():
            name = row["姓名"]
            weekday = str(row["周几"])
            date = str(row["日期"])

            # 跳过空值
            if pd.isna(name) or pd.isna(weekday) or pd.isna(date):
                continue

            # 确保姓名在结果中存在
            if name not in result:
                result[name] = {
                    "count": 0,
                    "weekdays": {}  # 格式: {"周一": {"dates": set(), "order": 0}, ...}
                }
                # 初始化所有周几的条目
                for idx, wd in enumerate(weekday_order):
                    result[name]["weekdays"][wd] = {"dates": set(), "order": idx}

            # 更新计数和日期信息
            result[name]["count"] += 1
            result[name]["weekdays"][weekday]["dates"].add(date)

        return result

    except FileNotFoundError:
        print(f"错误: 未找到文件 {file_path}")
        return None
    except Exception as e:
        print(f"处理文件时发生错误: {str(e)}")
        return None


def print_results(results):
    """打印统计结果"""
    if not results:
        print("没有可显示的统计结果")
        return

    print("\n姓名出现情况统计结果:")
    print("-" * 80)

    # 按出现次数降序排列
    for name, data in sorted(results.items(), key=lambda x: x[1]["count"], reverse=True):
        # 收集并排序周几信息
        weekday_entries = []
        for wd, info in data["weekdays"].items():
            if info["dates"]:  # 只处理有记录的周几
                # 格式化日期
                dates_str = "、".join(sorted(info["dates"]))
                # 每个周几的完整字符串
                weekday_str = f"{wd}（{dates_str}）"
                weekday_entries.append((info["order"], weekday_str))

        # 按周几顺序排序并拼接
        weekday_entries.sort()
        weekdays_str = "、".join([entry[1] for entry in weekday_entries])

        # 打印结果
        print(f"{name}：{weekdays_str}，共出现 {data['count']} 次")

    print("-" * 80)
    print(f"总记录数: {sum(data['count'] for data in results.values())}")
    print(f"不同姓名总数: {len(results)}")


if __name__ == "__main__":
    # 替换为你的表格文件路径
    file_path = "20250912_63天值班计划表.xlsx"  # 可以是CSV或Excel文件

    # 分析姓名、周几和日期信息
    results = analyze_name_weekdays_dates(file_path)

    # 打印结果
    if results:
        print_results(results)
