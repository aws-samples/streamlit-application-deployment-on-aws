import altair as alt
import pandas as pd
import urllib
import streamlit as st
from pyathena import connect
from rich import columns
import datetime
import base64
from io import BytesIO

from config import REGION, BUCKET, DATABASE, TABLE, INDEX_COLUMN_NAME


@st.cache
def query_database(
    table_name: str,
    date_range: tuple = ("2006-05-01", "2021-02-28"),
    index_colname: str = INDEX_COLUMN_NAME,
    database: str = DATABASE,
    region: str = REGION,
    partition: str = "partition_0",
    key_word: str = "AUDUSD",
    s3_staging_dir: str = f"s3://{BUCKET}/tmp/",
) -> pd.DataFrame:
    conn = connect(s3_staging_dir=s3_staging_dir, region_name=region)
    df = pd.read_sql(
        f"""SELECT * FROM "{database}"."{table_name}"
        WHERE {partition} LIKE '%{key_word}%' 
        AND 
        {index_colname} BETWEEN '{date_range[0]}' AND '{date_range[1]}';
        """,
        conn,
        index_col=index_colname,
        parse_dates=[index_colname],
    )
    df.sort_index(inplace=True)
    return df


@st.cache
def get_partitions(
    table_name: str,
    index_colname: str = INDEX_COLUMN_NAME,
    partition: str = "partition_0",
    database: str = DATABASE,
    region: str = REGION,
    s3_staging_dir: str = f"s3://{BUCKET}/tmp/",
) -> pd.DataFrame:
    conn = connect(s3_staging_dir=s3_staging_dir, region_name=region)
    df = pd.read_sql(
        f"""SELECT DISTINCT {partition} FROM "{database}"."{table_name}";""", conn
    )
    return df


@st.cache
def show_all_columns_per_table(
    table: str,
    database: str = DATABASE,
    region: str = REGION,
    s3_staging_dir: str = f"s3://{BUCKET}/tmp/",
) -> pd.DataFrame:
    conn = connect(s3_staging_dir=s3_staging_dir, region_name=region)
    df = pd.read_sql(
        f"""SELECT column_name FROM 
        information_schema.columns 
        WHERE table_schema = '{database}' 
        AND table_name = '{table}'""",
        conn,
    ).T
    df.set_index(pd.Series([table]), inplace=True)
    return df


def set_date_range() -> list:
    """Set Date Range

    Returns:
        list: ["2006-05-1", "2021-02-28"]
    """
    st.sidebar.write("## Date Range")
    default_date_range = [datetime.date(2006, 5, 1), datetime.date.today()]
    date_range = st.sidebar.date_input(
        "Selector",
        value=default_date_range,
        min_value=datetime.date(2006, 5, 1),
        max_value=datetime.date.today(),
    )
    if st.sidebar.button("Reset Date Range"):
        date_range = default_date_range
    date_range = list(date_range)
    date_range.sort()
    if len(date_range) == 2:
        return date_range
    else:
        return date_range + date_range


def page_config():
    st.set_page_config(
        page_title="Market Index", layout="centered", initial_sidebar_state="auto"
    )
    st.title("Market Index")


def plot_market_index(
    date_range: list, index_col_name: str = INDEX_COLUMN_NAME, table_name: str = TABLE
) -> pd.DataFrame:
    """Plot Market Index Data

    Args:
        date_range (list): ["2006-05-1", "2021-02-28"]
        index_col_name (str, optional): column name for dataframe index. Defaults to "date".
        table_name (str, optional): table name in the database. Defaults to "streamlit_dashboard_blog_post".

    Returns:
        pd.DataFrame: selected DataFrame
    """
    assert len(date_range) == 2
    date_range = [date.strftime("%Y-%m-%d") for date in date_range]
    partitions = get_partitions(table_name)
    partition = st.sidebar.selectbox("Choose Index", partitions.values[:, 0])
    df_mkt_idx = query_database(table_name, date_range=date_range, key_word=partition)

    column_name_num = list(df_mkt_idx.select_dtypes(include=["number"]).columns)

    columns_selected = st.sidebar.multiselect(
        "Choose Columns", column_name_num, column_name_num[0]
    )

    df_vis = df_mkt_idx[columns_selected]
    brush = alt.selection(type="interval", encodings=["x"])
    base_chart_top = base_chart_down = (
        alt.Chart(df_vis.reset_index())
        .transform_fold(columns_selected)
        .mark_line()
        .encode(
            x=f"{index_col_name}:T",
            y=alt.X(f"value:Q", scale=alt.Scale(zero=False)),
            color="key:N",
            tooltip=[f"{index_col_name}:T"],
        )
    )
    upper = base_chart_top.properties(
        width=600, height=400, title=f"{partition}"
    ).encode(alt.X(f"{index_col_name}:T", scale=alt.Scale(domain=brush)))
    lower = base_chart_down.properties(width=600, height=90).add_selection(brush)
    st.altair_chart(upper & lower, use_container_width=True)

    if st.checkbox("Show DataFrame"):
        st.write(df_mkt_idx)
        st.markdown(get_table_download_link(df_mkt_idx), unsafe_allow_html=True)

    return df_mkt_idx


def to_excel(df: pd.DataFrame):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")
    df.to_excel(writer, sheet_name="Sheet1")
    writer.save()
    processed_data = output.getvalue()
    return processed_data


def get_table_download_link(df: pd.DataFrame) -> str:
    val = to_excel(df)
    b64 = base64.b64encode(val)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="dataframe.xlsx">Download csv file</a>'  # decode b'abc' => abc


if __name__ == "__main__":
    page_config()
    # date range selector
    date_range = set_date_range()
    # Plot Market Data
    st.sidebar.write("## Market Index")
    plot_market_index(date_range)
