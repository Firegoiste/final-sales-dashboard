# professional_dashboard.py (最终完整版 - 修复所有已知错误)

import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from prophet import Prophet
import altair as alt
import math
from io import BytesIO
import matplotlib.pyplot as plt

# --- 数据库文件名 ---
DATABASE_FILE = 'sales_database.db'

# --- 页面配置 ---
st.set_page_config(layout="wide", page_title="专业销售数据仪表盘")


# --- 数据加载函数 ---
@st.cache_data(ttl=600)
def load_data_from_db():
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        df = pd.read_sql_query("SELECT * FROM sales", conn)
        conn.close()
        df['日期 (Date)'] = pd.to_datetime(df['日期 (Date)'])
        return df
    except Exception:
        return pd.DataFrame()


df_all = load_data_from_db()


# --- 辅助函数：导出Excel ---
@st.cache_data
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()


# --- 自然语言理解 (NLU) 核心 ---
def parse_query(query, data_df):
    query_lower = query.lower().strip()
    if query_lower == '你好' or query_lower == 'hello': return "你好呀！我是您的专属销售数据分析助手~ ( ´ ▽ ` )ﾉ"
    if '不是哥们' in query_lower: return "哎呀，别在意这些细节嘛！我们还是聊聊销售数据吧~ O(∩_∩)O"
    all_reps = [str(rep).lower() for rep in data_df['销售代表 (Rep)'].unique()]
    all_regions = [str(region).lower() for region in data_df['销售区域 (Region)'].unique()]
    all_categories = [str(cat).lower() for cat in data_df['产品大类 (Category)'].unique()]
    found_entities = []
    found_rep = [rep for rep in all_reps if rep in query_lower]
    if found_rep: found_entities.extend(found_rep)
    found_region = [region for region in all_regions if region in query_lower]
    if found_region: found_entities.extend(found_region)
    found_category = [cat for cat in all_categories if cat in query_lower]
    if found_category: found_entities.extend(found_category)
    if not found_entities: return f"抱歉，您的问题中不包含可识别的关键词（如销售代表、区域、产品大类等），请换个问法试试吧 (T_T)"
    if found_rep and not found_region and not found_category:
        rep_name_original = [rep for rep in data_df['销售代表 (Rep)'].unique() if rep.lower() in found_rep][0]
        rep_df = data_df[data_df['销售代表 (Rep)'] == rep_name_original]
        if rep_df.empty: return f"数据库中没有找到销售代表 **{rep_name_original}** 的记录。 (T_T)"
        total_sales = rep_df['销售额 (Sales)'].sum()
        region_sales = rep_df.groupby('销售区域 (Region)')['销售额 (Sales)'].sum().sort_values(ascending=False)
        region_text = "\n#### **大区业绩分布:**\n"
        for region, sales in region_sales.items(): region_text += f"- **{region}:** ¥ {sales:,.2f}\n"
        top_products = rep_df.groupby('产品名称 (Product)')['销售额 (Sales)'].sum().nlargest(3)
        product_text = "\n#### **Top 3 畅销产品:**\n"
        for i, (product, sales) in enumerate(top_products.items(),
                                             1): product_text += f"**{i}. {product}:** ¥ {sales:,.2f}\n"
        top_region = region_sales.index[0]
        top_category = rep_df.groupby('产品大类 (Category)')['销售额 (Sales)'].sum().idxmax()
        analysis_text = (f"\n#### **简要分析:**\n"
                         f"**{rep_name_original}** 的业绩主要集中在 **{top_region}** 区域。"
                         f"从产品来看，他/她最擅长销售 **{top_category}** 类的产品。")
        return (f"为您生成销售代表 **{rep_name_original}** 的业绩报告：\n"
                f"### **总销售额: ¥ {total_sales:,.2f}**\n"
                f"{region_text}{product_text}{analysis_text}")
    filtered_df = data_df.copy()
    if found_rep:
        original_reps = [rep for rep in data_df['销售代表 (Rep)'].unique() if str(rep).lower() in found_rep]
        filtered_df = filtered_df[filtered_df['销售代表 (Rep)'].isin(original_reps)]
    if found_region:
        original_regions = [region for region in data_df['销售区域 (Region)'].unique() if
                            str(region).lower() in found_region]
        filtered_df = filtered_df[filtered_df['销售区域 (Region)'].isin(original_regions)]
    if found_category:
        original_categories = [cat for cat in data_df['产品大类 (Category)'].unique() if str(cat).lower() in found_category]
        filtered_df = filtered_df[filtered_df['产品大类 (Category)'].isin(original_categories)]
    if filtered_df.empty: return f"虽然您的问题我听懂了，但在数据库里暂未查询到完全匹配的记录哦 (T_T)"
    if '订单' in query_lower or '卖了多少笔' in query_lower:
        count = len(filtered_df)
        return f"查询到 **{count}** 笔相关订单。"
    else:
        total_sales = filtered_df['销售额 (Sales)'].sum()
        return f"查询到的相关总销售额为: **¥ {total_sales:,.2f}**"


# --- 仪表盘主界面 ---
st.title("🚀 专业销售数据智能仪表盘")

if df_all.empty:
    st.warning("数据库中尚无数据。请先运行 `update_database.py` 来添加数据。")
    st.stop()

# --- 智能问答区域 ---
st.markdown("---")
st.header("💡 智能问答引擎")
st.write("您可以像聊天一样提问，例如：“张三在华东的总业绩是多少？” 或 “软件产品有多少笔订单？”")
with st.form(key='qna_form'):
    user_query = st.text_input("请在这里输入您的问题:", key='query_input')
    submit_button = st.form_submit_button(label='提交问题')
if submit_button and user_query:
    with st.spinner("正在分析您的问题并查询数据..."):
        answer = parse_query(user_query, df_all)
    st.info(f"**问:** {user_query}\n\n**答:**\n{answer}")
st.markdown("---")

# --- 侧边栏筛选器 ---
st.sidebar.header("筛选与导航")
selected_date = st.sidebar.date_input("选择查看日期", value=df_all['日期 (Date)'].max(), min_value=df_all['日期 (Date)'].min(),
                                      max_value=df_all['日期 (Date)'].max())
all_reps_list = df_all['销售代表 (Rep)'].unique()
all_categories_list = df_all['产品大类 (Category)'].unique()
selected_reps = st.sidebar.multiselect("选择销售代表", options=all_reps_list, default=all_reps_list)
selected_categories = st.sidebar.multiselect("选择产品大类", options=all_categories_list, default=all_categories_list)

# --- 数据筛选逻辑 ---
selected_date = pd.to_datetime(selected_date)
df_selected_day_unfiltered = df_all[df_all['日期 (Date)'].dt.date == selected_date.date()]
df_selected = df_selected_day_unfiltered[
    (df_selected_day_unfiltered['销售代表 (Rep)'].isin(selected_reps)) &
    (df_selected_day_unfiltered['产品大类 (Category)'].isin(selected_categories))
    ]
df_previous = df_all[df_all['日期 (Date)'].dt.date == (selected_date - timedelta(days=1)).date()]
df_last_week = df_all[df_all['日期 (Date)'].dt.date == (selected_date - timedelta(days=7)).date()]

# --- 主界面 ---
st.header(f"{selected_date.strftime('%Y-%m-%d')} 常规仪表盘")

if df_selected.empty:
    st.warning(f"在当前筛选条件下， {selected_date.strftime('%Y-%m-%d')} 没有找到销售数据。")
else:
    # --- KPI 和同比环比分析 ---
    total_sales_selected = df_selected['销售额 (Sales)'].sum()
    total_sales_previous = df_previous['销售额 (Sales)'].sum()
    daily_growth_rate = ((
                                     total_sales_selected - total_sales_previous) / total_sales_previous) * 100 if total_sales_previous > 0 else 0
    total_sales_last_week = df_last_week['销售额 (Sales)'].sum()
    weekly_growth_rate = ((
                                      total_sales_selected - total_sales_last_week) / total_sales_last_week) * 100 if total_sales_last_week > 0 else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="总销售额 (筛选后)", value=f"¥ {total_sales_selected:,.2f}", delta=f"{daily_growth_rate:.2f}% vs 昨日全量")
        st.caption(f"与上周同期全量对比: **{weekly_growth_rate:+.2f}%**")

    col2.metric("订单数 (筛选后)", f"{len(df_selected)} 单")
    col3.metric("平均客单价 (筛选后)", f"¥ {df_selected['销售额 (Sales)'].mean():,.2f}")

    st.markdown("---")

    st.subheader("本日 Top 10 明星分析 (筛选后)")
    col_rep, col_prod = st.columns(2)
    with col_rep:
        st.markdown("##### 🏆 **Top 10 销售代表**")
        top_reps = df_selected.groupby('销售代表 (Rep)')['销售额 (Sales)'].sum().nlargest(10)
        st.dataframe(top_reps)
    with col_prod:
        st.markdown("##### 🚀 **Top 10 畅销产品**")
        top_products = df_selected.groupby('产品名称 (Product)')['销售额 (Sales)'].sum().nlargest(10)
        st.dataframe(top_products)

    st.markdown("---")

    st.subheader("业绩贡献度分析 (帕累托分析)")
    all_reps_sales = df_selected.groupby('销售代表 (Rep)')['销售额 (Sales)'].sum().sort_values(ascending=False)
    if len(all_reps_sales) > 0:
        num_top_20_percent = math.ceil(len(all_reps_sales) * 0.2)
        top_20_percent_reps = all_reps_sales.head(num_top_20_percent)
        top_reps_names = ', '.join(top_20_percent_reps.index.tolist())
        sales_from_top_20 = top_20_percent_reps.sum()
        contribution_percentage = (sales_from_top_20 / total_sales_selected) * 100
        st.info(f"业绩排名前 **20%** 的明星销售 (**{top_reps_names}**)，总共贡献了 **{contribution_percentage:.2f}%** 的销售额。")
    else:
        st.info("当前筛选条件下无销售数据，无法进行贡献度分析。")

    st.markdown("---")

    st.subheader("📥 数据导出")
    df_to_export = df_selected
    excel_data = to_excel(df_to_export)
    st.download_button(label="📄 下载当日筛选后明细数据", data=excel_data,
                       file_name=f"sales_details_{selected_date.strftime('%Y%m%d')}.xlsx")

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📊 **图表联动分析 (筛选后)**", "📈 历史趋势 (全量)", "🔮 销售预测 (全量)"])

    with tab1:
        st.subheader("各维度销售额详情 (点击图表进行联动筛选)")

        # --- 核心修改：确保所有列名都使用数据表中的完整名称 ---

        selection = alt.selection_multi(fields=['销售区域 (Region)'], empty='all')  # 使用正确列名

        chart_region = alt.Chart(df_selected).mark_bar().encode(
            x=alt.X('销售区域 (Region):N', title='销售区域'),  # 使用正确列名
            y=alt.Y('sum(销售额 (Sales)):Q', title='总销售额 (元)'),
            color=alt.condition(selection, alt.value('orange'), alt.value('steelblue')),
            tooltip=[alt.Tooltip('销售区域 (Region):N', title='大区'), alt.Tooltip('sum(销售额 (Sales)):Q', format=',.2f')]
            # 使用正确列名
        ).add_selection(selection).properties(title='各大区销售额')

        chart_category = alt.Chart(df_selected).mark_bar().encode(
            x=alt.X('产品大类 (Category):N', title='产品大类'),
            y=alt.Y('sum(销售额 (Sales)):Q', title='总销售额 (元)'),
            tooltip=[alt.Tooltip('产品大类 (Category):N'), alt.Tooltip('sum(销售额 (Sales)):Q', format=',.2f')]
        ).transform_filter(selection).properties(title='各产品大类销售额 (可被区域筛选)')

        st.altair_chart(chart_region | chart_category, use_container_width=False)

    with tab2:
        st.subheader("历史销售总额趋势 (可交互)")
        daily_sales_history = df_all.groupby(df_all['日期 (Date)'].dt.date)['销售额 (Sales)'].sum().reset_index()
        daily_sales_history.rename(columns={'日期 (Date)': '日期', '销售额 (Sales)': '销售额'}, inplace=True)
        chart = alt.Chart(daily_sales_history).mark_line(point=True, strokeWidth=2).encode(
            x=alt.X('日期:T', title='日期'),
            y=alt.Y('销售额:Q', title='总销售额 (元)'),
            tooltip=[alt.Tooltip('日期:T', format='%Y-%m-%d'), alt.Tooltip('销售额:Q', format=',.2f')]
        ).interactive()
        st.altair_chart(chart, use_container_width=True)

    with tab3:
        st.subheader("未来销售额预测 (Prophet 模型)")
        history_df = df_all[df_all['日期 (Date)'].dt.date <= selected_date.date()].copy()
        daily_history = history_df.groupby(history_df['日期 (Date)'].dt.date)['销售额 (Sales)'].sum().reset_index()
        prophet_df = daily_history.rename(columns={'日期 (Date)': 'ds', '销售额 (Sales)': 'y'})
        if len(prophet_df) < 14:
            st.warning("历史数据不足14天，Prophet 预测可能不准确。")
        else:
            plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False
            model = Prophet(interval_width=0.95)
            model.fit(prophet_df)
            future = model.make_future_dataframe(periods=30)
            forecast = model.predict(future)
            st.write("模型基于至今为止的所有历史数据，预测未来30天的销售趋势：")
            fig = model.plot(forecast)
            ax = fig.gca()
            ax.set_xlabel("日期", fontsize=12)
            ax.set_ylabel("预测销售额 (元)", fontsize=12)
            ax.set_title("未来30天销售额预测趋势", fontsize=16)
            st.pyplot(fig)
            st.write("详细预测数据：")
            future_data = forecast.tail(30)
            display_forecast = future_data[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
            display_forecast.rename(
                columns={'ds': '日期', 'yhat': '预测值', 'yhat_lower': '预测下限 (95%置信)', 'yhat_upper': '预测上限 (95%置信)'},
                inplace=True)
            display_forecast['日期'] = display_forecast['日期'].dt.strftime('%Y-%m-%d')
            st.dataframe(display_forecast)