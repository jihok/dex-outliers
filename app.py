import streamlit as st
import altair as alt
import pandas as pd
from subgrounds.subgrounds import Subgrounds

sg = Subgrounds()

subgraphs = {
    "apeswap-polygon": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/apeswap-polygon"
    ),
    "apeswap-bsc": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/apeswap-bsc"
    ),
    "sushiswap-arbitrum": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/sushiswap-arbitrum"
    ),
    "sushiswap-avalanche": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/sushiswap-avalanche"
    ),
    "sushiswap-bsc": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/sushiswap-bsc"
    ),
    "sushiswap-celo": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/sushiswap-celo"
    ),
    "sushiswap-fantom": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/sushiswap-fantom"
    ),
    "sushiswap-fuse": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/sushiswap-fuse"
    ),
    "sushiswap-ethereum": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/sushiswap-ethereum"
    ),
    "sushiswap-polygon": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/sushiswap-polygon"
    ),
    "sushiswap-moonbeam": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/sushiswap-moonbeam"
    ),
    "sushiswap-moonriver": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/sushiswap-moonriver"
    ),
    "sushiswap-gnosis": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/sushiswap-gnosis"
    ),
    "solarbeam-moonriver": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/solarbeam-moonriver"
    ),
    "spiritswap-fantom": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/spiritswap-fantom"
    ),
    "spookyswap-fantom": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/spookyswap-fantom"
    ),
    "trader-joe-avalanche": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/trader-joe-avalanche"
    ),
    # "trisolaris-aurora": sg.load_subgraph(
    #     "https://api.thegraph.com/subgraphs/name/messari/trisolaris-aurora"
    # ),
    "ubeswap-celo": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/ubeswap-celo"
    ),
    "uniswap-v2-ethereum": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/uniswap-v2-ethereum"
    ),
    "quickswap-polygon": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/quickswap-polygon"
    ),
    # "vvs-finance-cronos": sg.load_subgraph(
    #     "https://api.thegraph.com/subgraphs/name/messari/vvs-finance-cronos"
    # ),
    "honeyswap-gnosis": sg.load_subgraph(
        "https://api.thegraph.com/subgraphs/name/messari/honeyswap-gnosis"
    ),
    # "honeyswap-polygon": sg.load_subgraph(
    #     "https://api.thegraph.com/subgraphs/name/messari/honeyswap-polygon"
    # ),
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
    print('🔥', df["id"])
    df["date"] = pd.to_datetime(df["id"], unit="d")
    df = df.drop(columns="id")
    return df


def get_big_swaps_df(network, subgraph):
    big_swaps = subgraph.Query.swaps(
        where=[subgraph.Swap.amountInUSD > 1_000_000_000],
        orderBy=subgraph.Swap.amountInUSD,
        orderDirection="desc",
        first=10,
    )

    big_swaps_df = sg.query_df(
        [
            big_swaps.id,
            big_swaps.tokenIn.id,
            big_swaps.tokenIn.name,
            big_swaps.tokenIn.symbol,
            big_swaps.tokenIn.lastPriceUSD,
            big_swaps.amountInUSD,
            big_swaps.amountOutUSD,
        ]
    )
    print(big_swaps_df)
    big_swaps_df["Deployment"] = network
    big_swaps_df = big_swaps_df.rename(columns={
        'swaps_id': 'Tx Hash',
        'swaps_tokenIn_id': 'Token In Address',
        'swaps_tokenIn_name': 'Token In Name',
        'swaps_tokenIn_symbol': 'Token In Symbol',
        'swaps_tokenIn_lastPriceUSD': 'Token In Last Price USD',
        'swaps_amountInUSD': 'Amount In USD',
        'swaps_amountOutUSD': 'Amount Out USD',
    })

    return big_swaps_df


st.set_page_config(page_icon="🔎", layout="wide")
st.title("anAMMolies")

choice = st.selectbox("Financial Metric Type", ["Revenue", "TVL", "Volume"])

data_loading = st.text("Loading data...")

big_swaps_df = pd.concat(
    map(lambda x: get_big_swaps_df(x, subgraphs[x]), subgraphs.keys()),
    axis=0,
)
st.header("Potential Outlier Swaps")
st.markdown(big_swaps_df.to_markdown())

if (choice == "Revenue"):
    for network in subgraphs.keys():
        df = fetch_data(network, subgraphs[network])
        chart = (
            alt.Chart(df, title=network)
            .mark_area()
            .encode(x="date:T", y="cumulativeTotalRevenueUSD:Q")
        )
        st.altair_chart(chart, use_container_width=True)
elif (choice == "TVL"):
    for network in subgraphs.keys():
        df = fetch_data(network, subgraphs[network])
        chart = (
            alt.Chart(df, title=network)
            .mark_area()
            .encode(x="date:T", y="totalValueLockedUSD:Q")
        )
        st.altair_chart(chart, use_container_width=True)
elif (choice == "Volume"):
    for network in subgraphs.keys():
        df = fetch_data(network, subgraphs[network])
        chart = (
            alt.Chart(df, title=network)
            .mark_area()
            .encode(x="date:T", y="cumulativeVolumeUSD:Q")
        )
        st.altair_chart(chart, use_container_width=True)

data_loading.text("Loading data... done!")
