# update_database.py

import pandas as pd
import sqlite3
from datetime import datetime

# --- 配置 ---
# 我们要读取的 Excel 文件名
EXCEL_FILE = 'sales_data.xlsx'
# 我们要创建或更新的数据库文件名
DATABASE_FILE = 'sales_database.db'


def update_database():
    """读取指定的Excel文件，并将数据追加到SQLite数据库中"""

    try:
        # 读取 Excel 数据
        df_new = pd.read_excel(EXCEL_FILE)
        # 将“日期”列转换为标准的日期时间格式，以便后续处理
        df_new['日期 (Date)'] = pd.to_datetime(df_new['日期 (Date)'])
        print(f"成功读取 '{EXCEL_FILE}'，包含 {len(df_new)} 条新数据。")

    except FileNotFoundError:
        print(f"错误：找不到数据文件 '{EXCEL_FILE}'。请确保它和本脚本在同一个文件夹下。")
        return
    except Exception as e:
        print(f"读取Excel时发生错误: {e}")
        return

    try:
        # 连接到SQLite数据库 (如果文件不存在，会自动创建)
        conn = sqlite3.connect(DATABASE_FILE)

        # 将新数据写入数据库的 'sales' 表中
        # if_exists='replace' 意味着每次运行都会用最新的Excel数据完全替换旧的数据库
        # 这对于我们从头开始填充一个月的完整数据是最佳选择
        df_new.to_sql('sales', conn, if_exists='replace', index=False)

        conn.close()
        print(f"成功将 {len(df_new)} 条数据写入数据库 '{DATABASE_FILE}' 中。")

    except Exception as e:
        print(f"更新数据库时发生错误: {e}")


# --- 主程序入口 ---
if __name__ == '__main__':
    print(f"--- 开始执行数据更新 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    update_database()
    print("--- 数据更新流程结束 ---")