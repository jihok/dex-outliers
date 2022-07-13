import streamlit as st
from streamlit_autorefresh import st_autorefresh
import altair as alt
import pandas as pd
from subgrounds.subgrounds import Subgrounds

# Refresh every 30 seconds
REFRESH_INTERVAL_SEC = 30

sg = Subgrounds()
subgraphs = {
    "apeswap-polygon": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/apeswap-polygon"
    ),
    "apeswap-bsc": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/apeswap-bsc"
    ),
    "sushiswap-polygon": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/sushiswap-polygon"
    ),

}


def fetch_data(network, subgraph):
    financial_metrics = subgraph.Query.financialsDailySnapshots(
        orderBy=subgraph.FinancialsDailySnapshot.id,
        orderDirection="desc",
        first=100,
    )

    financial_df = sg.query_df(
        [
            financial_metrics.id,
            financial_metrics.totalValueLockedUSD,
            financial_metrics.cumulativeVolumeUSD,
            financial_metrics.cumulativeTotalRevenueUSD,
        ]
    )

    financial_df = financial_df.rename(
        columns=lambda x: x[len("financialsDailySnapshots_"):]
    )

    df = financial_df
    df["network"] = network
    df["date"] = pd.to_datetime(df["id"], unit="d")
    df = df.drop(columns="id")
    return df


def get_big_swaps_df(network, subgraph):
    big_swaps = subgraph.Query.swaps(
        where=[subgraph.Swap.amountInUSD > 1_000_000],
        orderBy=subgraph.Swap.amountInUSD,
        orderDirection="desc",
        first=10,
    )
    print(big_swaps)
    big_swaps_df = sg.query_df(
        [
            big_swaps.id,
            big_swaps.tokenIn,
            big_swaps.amountInUSD,
        ]
    )
    print(big_swaps_df)
    big_swaps_df["network"] = network
    # big_swaps_df["date"] = pd.to_datetime(big_swaps_df["id"], unit="d")
    # big_swaps_df = big_swaps_df.drop(columns="id")

    return big_swaps_df


st.set_page_config(page_icon="🔎", layout="wide")
ticker = st_autorefresh(interval=REFRESH_INTERVAL_SEC * 1000, key="ticker")
st.title("anAMMolies")

data_loading = st.text(
    f"[Every {REFRESH_INTERVAL_SEC} seconds] Loading data...")
df = pd.concat(
    map(lambda x: fetch_data(x, subgraphs[x]), subgraphs.keys()),
    axis=0,
)
data_loading.text(
    f"[Every {REFRESH_INTERVAL_SEC} seconds] Loading data... done!")

# Plot charts with altair is like a breeze
st.header("Revenue")
rev_stacked_bar_chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(x="date:T", y="cumulativeTotalRevenueUSD:Q", color="network:N")
)
st.altair_chart(rev_stacked_bar_chart, use_container_width=True)

st.header("TVL")
tvl_stacked_bar_chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(x="date:T", y="totalValueLockedUSD:Q", color="network:N")
)
st.altair_chart(tvl_stacked_bar_chart, use_container_width=True)

st.header("Volume")
volume_norm_stacked_area_chart = (
    alt.Chart(df)
    .mark_area()
    .encode(
        x="date:T",
        y=alt.Y("cumulativeVolumeUSD:Q", stack="normalize"),
        color="network:N",
    )
)
st.altair_chart(volume_norm_stacked_area_chart, use_container_width=True)

big_swaps_df = pd.concat(
    map(lambda x: get_big_swaps_df(x, subgraphs[x]), subgraphs.keys()),
    axis=0,
)
print(big_swaps_df)
st.markdown(big_swaps_df.to_markdown())
