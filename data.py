from subgrounds.subgrounds import Subgrounds
import requests
import pandas as pd

sg = Subgrounds()


def get_deployment_names():
    # TODO: this should be fetched from config json
    return [
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


# build subgraphs dict in session state by loading pending version if applicable or current version otherwise
def build_subgraphs_dict(state):
    deployment_names = get_deployment_names()
    if (len(state) == 0):
        for x in deployment_names:
            res = requests.post("https://api.thegraph.com/index-node/graphql", json={
                "operationName": "Status",
                "query": "query Status($subgraphName: String) {\n  indexingStatusForPendingVersion(subgraphName: $subgraphName) {\n    subgraph\n    health\n    entityCount\n    __typename\n  }\n}",
                "variables": {"subgraphName": "messari/" + x}
            })
            indexingStatusForPendingVerion = res.json(
            )["data"]["indexingStatusForPendingVersion"]
            # no pending version
            if (indexingStatusForPendingVerion is None):
                state[x] = sg.load_subgraph(
                    f"https://api.thegraph.com/subgraphs/name/messari/{x}")
            # pending exists but no entities indexed
            elif (indexingStatusForPendingVerion["entityCount"] == "0"):
                state[x] = sg.load_subgraph(
                    f"https://api.thegraph.com/subgraphs/name/messari/{x}")
            # use pending
            else:
                id = indexingStatusForPendingVerion["subgraph"]
                state[f"{x} (pending)"] = sg.load_subgraph(
                    f"https://api.thegraph.com/subgraphs/id/{id}")
    return state

# fetch financial data for given subgraph


def fetch_charts_data(network, subgraph):
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
            financial_metrics.dailyVolumeUSD
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
