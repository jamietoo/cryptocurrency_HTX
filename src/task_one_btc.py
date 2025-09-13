import argparse
import requests
import networkx as nx
import matplotlib.pyplot as plt

RAWADDR_URL = "https://blockchain.info/rawaddr/{address}"

def fetch_btc_transactions(address: str, limit: int = 20):
    url = RAWADDR_URL.format(address=address)
    r = requests.get(url, params={"limit": max(limit, 50)}, timeout=30)
    r.raise_for_status()
    return r.json().get("txs", [])[:limit]

def tx_to_edges(tx: dict):
    h = tx.get("hash")
    ins = [i.get("prev_out", {}).get("addr") for i in tx.get("inputs", [])]
    outs = [o.get("addr") for o in tx.get("out", [])]
    ins = [a for a in ins if a]
    outs = [a for a in outs if a]
    if not ins:
        ins = ["COINBASE"]
    return [(i, o, h) for i in ins for o in outs]

def build_graph(txs):
    G = nx.DiGraph()
    all_edges = []
    for tx in txs:
        all_edges += tx_to_edges(tx)
    for s, d, h in all_edges:
        if G.has_edge(s, d):
            G[s][d]["count"] += 1
            G[s][d]["hashes"].append(h)
        else:
            G.add_edge(s, d, count=1, hashes=[h])
    return G

def plot_wallet_graph(G, out_path: str):
    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42, k=0.6)
    nx.draw_networkx_nodes(G, pos, node_size=200)
    nx.draw_networkx_edges(G, pos, arrows=True, arrowstyle="->", arrowsize=10, width=1.0)
    deg = dict(G.degree())
    top_nodes = [n for n, _ in sorted(deg.items(), key=lambda x: x[1], reverse=True)[:10]]
    nx.draw_networkx_labels(G, pos, labels={n: n for n in top_nodes}, font_size=8)
    plt.title("Wallet Graph (sample)")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    print(f"[+] Saved graph to {out_path}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--address", required=True)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--out", default="out/task1_graph.png")
    args = ap.parse_args()

    txs = fetch_btc_transactions(args.address, args.limit)
    G = build_graph(txs)

    print("=== Graph Summary ===")
    print("Nodes:", G.number_of_nodes(), "Edges:", G.number_of_edges())

    plot_wallet_graph(G, args.out)

if __name__ == "__main__":
    main()
