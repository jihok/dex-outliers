import streamlit as st
import altair as alt
import pandas as pd
from subgrounds.subgrounds import Subgrounds
import requests


st.set_page_config(page_icon="🔎", layout="wide")
st.title("anAMMolies")

sg = Subgrounds()

with st.sidebar:
    choice = st.selectbox("Financial Metric Type", [
                          "Revenue", "TVL", "Volume"])

# TODO: this should be fetched from config json
deployment_names = [
    "apeswap-bsc",
    "apeswap-polygon",
    "honeyswap-gnosis",
    # "honeyswap-polygon",
    "quickswap-polygon",
    "solarbeam-moonriver",
    "spiritswap-fantom",
    "spookyswap-fantom",
    "sushiswap-arbitrum",
    "sushiswap-avalanche",
    "sushiswap-bsc",
    "sushiswap-celo",
    "sushiswap-ethereum",
    "sushiswap-fantom",
    "sushiswap-fuse",
    "sushiswap-gnosis",
    "sushiswap-moonbeam",
    "sushiswap-moonriver",
    "sushiswap-polygon",
    "trader-joe-avalanche",
    # "trisolaris-aurora",
    "ubeswap-celo",
    "uniswap-v2-ethereum",
    # "vvs-finance-cronos",
]

# fetch financial data for given subgraph


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

    financial_df["network"] = network
    financial_df["date"] = pd.to_datetime(financial_df["id"], unit="d")
    financial_df = financial_df.drop(columns="id")
    return financial_df

# fetch potential outlier swaps for given subgraph


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


if 'subgraphs' not in st.session_state:
    st.session_state['subgraphs'] = {}

if 'financial_dfs' not in st.session_state:
    st.session_state['financial_dfs'] = {}

data_loading = st.text("Fetching subgraphs...")

# build subgraphs dict in session state by loading pending version if applicable or current version otherwise
if (len(st.session_state['subgraphs']) == 0):
    for x in deployment_names:
        res = requests.post("https://api.thegraph.com/index-node/graphql", json={
            "operationName": "Status",
            "query": "query Status($subgraphName: String) {\n  indexingStatusForPendingVersion(subgraphName: $subgraphName) {\n    subgraph\n    health\n    entityCount\n    __typename\n  }\n}",
            "variables": {"subgraphName": "messari/" + x}
        })
        indexingStatusForPendingVerion = res.json(
        )["data"]["indexingStatusForPendingVersion"]
        if (indexingStatusForPendingVerion is None):
            st.session_state['subgraphs'][x] = sg.load_subgraph(
                f"https://api.thegraph.com/subgraphs/name/messari/{x}")
        elif (indexingStatusForPendingVerion["entityCount"] == "0"):
            st.session_state['subgraphs'][x] = sg.load_subgraph(
                f"https://api.thegraph.com/subgraphs/name/messari/{x}")
        else:
            id = indexingStatusForPendingVerion["subgraph"]
            st.session_state['subgraphs'][f"{x} (pending)"] = sg.load_subgraph(
                f"https://api.thegraph.com/subgraphs/id/{id}")

data_loading.text("Gathering data...")

# make big_swaps_df after ensuring the subgraphs are in session state
if 'big_swaps_df' not in st.session_state:
    st.session_state['big_swaps_df'] = {} if 'subgraphs' not in st.session_state else pd.concat(
        map(lambda x: get_big_swaps_df(
            x, st.session_state['subgraphs'][x]), st.session_state['subgraphs'].keys()),
        axis=0,
    )

outlier_container = st.container()
with outlier_container:
    st.header("Potential Outlier Swaps")
    st.markdown(st.session_state['big_swaps_df'].to_markdown())

data_loading.text("Loading data... done!")


def generate_charts(chart_type):
    charts = []
    for network in st.session_state['subgraphs'].keys():
        # always store in session state if doesn't exist there
        if network not in st.session_state['financial_dfs']:
            st.session_state['financial_dfs'][network] = fetch_data(
                network, st.session_state['subgraphs'][network])

        if (chart_type == "Revenue"):
            if 'revenue_charts' not in st.session_state:
                chart = (
                    alt.Chart(st.session_state['financial_dfs']
                              [network], title=network)
                    .mark_area()
                    .encode(x="date:T", y="cumulativeTotalRevenueUSD:Q")
                )
                st.session_state['revenue_charts'] = {network: chart}
            elif network in st.session_state['revenue_charts']:
                chart = st.session_state['revenue_charts'][network]
            else:
                chart = (
                    alt.Chart(st.session_state['financial_dfs']
                              [network], title=network)
                    .mark_area()
                    .encode(x="date:T", y="cumulativeTotalRevenueUSD:Q")
                )
                st.session_state['revenue_charts'][network] = chart
        elif (chart_type == "TVL"):
            if 'tvl_charts' not in st.session_state:
                chart = (
                    alt.Chart(st.session_state['financial_dfs']
                              [network], title=network)
                    .mark_area()
                    .encode(x="date:T", y="totalValueLockedUSD:Q")
                )
                st.session_state['tvl_charts'] = {network: chart}
            elif network in st.session_state['tvl_charts']:
                chart = st.session_state['tvl_charts'][network]
            else:
                chart = (
                    alt.Chart(st.session_state['financial_dfs']
                              [network], title=network)
                    .mark_area()
                    .encode(x="date:T", y="totalValueLockedUSD:Q")
                )
                st.session_state['revenue_charts'][network] = chart
        elif (chart_type == "Volume"):
            if 'volume_charts' not in st.session_state:
                chart = (
                    alt.Chart(st.session_state['financial_dfs']
                              [network], title=network)
                    .mark_area()
                    .encode(x="date:T", y="cumulativeVolumeUSD:Q")
                )
                st.session_state['volume_charts'] = {network: chart}
            elif network in st.session_state['volume_charts']:
                chart = st.session_state['volume_charts'][network]
            else:
                chart = (
                    alt.Chart(st.session_state['financial_dfs']
                              [network], title=network)
                    .mark_area()
                    .encode(x="date:T", y="cumulativeVolumeUSD:Q")
                )
                st.session_state['volume_charts'][network] = chart
        charts.append(chart)
    return charts


chart_container = st.container()
gen_charts = generate_charts(choice)
with chart_container:
    charts_loading = st.text("Generating charts...")
    for index, chart in enumerate(gen_charts):
        st.altair_chart(chart, use_container_width=True)
        charts_loading.text(
            f"Generating charts... ({index + 1}/{len(st.session_state['subgraphs'])})")

    charts_loading.text("Charts ready!")
