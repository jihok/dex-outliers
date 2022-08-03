import streamlit as st
import altair as alt
import pandas as pd
from data import fetch_charts_data
from data import get_big_swaps_df
from data import build_subgraphs_dict


st.set_page_config("anAmmolies", page_icon="🔎", layout="wide")
st.title("anAMMolies")

metric_type = None
with st.sidebar:
    view_type = st.selectbox(
        "View", ["Potential Outlier Swaps", "Metrics Charts"])
    if (view_type == "Metrics Charts"):
        metric_type = st.selectbox("Financial Metric Type", [
            "Cumulative Total Revenue", "TVL", "Cumulative Volume", "Daily Volume"])

if 'subgraphs' not in st.session_state:
    st.session_state['subgraphs'] = {}

if 'financial_dfs' not in st.session_state:
    st.session_state['financial_dfs'] = {}

loading_text = st.text("Fetching subgraphs...")


subgraphs_dict = build_subgraphs_dict(st.session_state["subgraphs"])
st.session_state["subgraphs"] = subgraphs_dict


if view_type == "Potential Outlier Swaps":
    loading_text.text("Gathering data...")
    # make big_swaps_df after ensuring the subgraphs are in session state
    if 'big_swaps_df' not in st.session_state:
        st.session_state['big_swaps_df'] = {} if 'subgraphs' not in st.session_state else pd.concat(
            map(lambda x: get_big_swaps_df(
                x, st.session_state['subgraphs'][x]), st.session_state['subgraphs'].keys()),
            axis=0,
        )
    st.markdown(st.session_state['big_swaps_df'].to_markdown())
    loading_text.text("Loading data... done!")

else:
    def generate_charts(chart_type):
        charts = []
        for index, network in enumerate(st.session_state['subgraphs'].keys()):
            loading_text.text(
                f"Building charts...({index + 1}/{len(st.session_state['subgraphs'])})")
            # always store in session state if doesn't exist there
            if network not in st.session_state['financial_dfs']:
                st.session_state['financial_dfs'][network] = fetch_charts_data(
                    network, st.session_state['subgraphs'][network])

            if (chart_type == "Cumulative Total Revenue"):
                if 'revenue_charts' not in st.session_state or network not in st.session_state['revenue_charts']:
                    chart = (
                        alt.Chart(st.session_state['financial_dfs']
                                  [network], title=network)
                        .mark_area()
                        .encode(x="date:T", y="cumulativeTotalRevenueUSD:Q")
                    )
                    st.session_state['revenue_charts'] = {network: chart}
                elif network in st.session_state['revenue_charts']:
                    chart = st.session_state['revenue_charts'][network]
            elif (chart_type == "TVL"):
                if 'tvl_charts' not in st.session_state or network not in st.session_state['tvl_charts']:
                    chart = (
                        alt.Chart(st.session_state['financial_dfs']
                                  [network], title=network)
                        .mark_area()
                        .encode(x="date:T", y="totalValueLockedUSD:Q")
                    )
                    st.session_state['tvl_charts'] = {network: chart}
                elif network in st.session_state['tvl_charts']:
                    chart = st.session_state['tvl_charts'][network]
            elif (chart_type == "Cumulative Volume"):
                if 'cumulative_volume_charts' not in st.session_state or network not in st.session_state['cumulative_volume_charts']:
                    chart = (
                        alt.Chart(st.session_state['financial_dfs']
                                  [network], title=network)
                        .mark_area()
                        .encode(x="date:T", y="cumulativeVolumeUSD:Q")
                    )
                    st.session_state['cumulative_volume_charts'] = {
                        network: chart}
                elif network in st.session_state['cumulative_volume_charts']:
                    chart = st.session_state['cumulative_volume_charts'][network]
            elif (chart_type == "Daily Volume"):
                if 'daily_volume_charts' not in st.session_state or network not in st.session_state['daily_volume_charts']:
                    chart = (
                        alt.Chart(st.session_state['financial_dfs']
                                  [network], title=network)
                        .mark_area()
                        .encode(x="date:T", y="dailyVolumeUSD:Q")
                    )
                    st.session_state['daily_volume_charts'] = {network: chart}
                elif network in st.session_state['daily_volume_charts']:
                    chart = st.session_state['daily_volume_charts'][network]
            charts.append(chart)
        return charts

    gen_charts = generate_charts(metric_type) if metric_type != None else None
    for index, chart in enumerate(gen_charts):
        st.altair_chart(chart, use_container_width=True)
        loading_text.text(
            f"Generating charts... ({index + 1}/{len(st.session_state['subgraphs'])})")
    loading_text.text("Charts ready!")
