import argparse
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

BASE = "https://api.coingecko.com/api/v3/coins/{id}/market_chart"

def fetch_token_market(id: str, vs: str = "usd", days: int = 30):
    url = BASE.format(id=id)
    r = requests.get(url, params={"vs_currency": vs, "days": days}, timeout=30)
    r.raise_for_status()
    data = r.json()
    prices = pd.DataFrame(data["prices"], columns=["ts", "price"])
    volumes = pd.DataFrame(data["total_volumes"], columns=["ts", "volume"])
    df = prices.merge(volumes, on="ts")
    df["ts"] = pd.to_datetime(df["ts"], unit="ms")
    return df.sort_values("ts").reset_index(drop=True)

def detect_anomalies(df: pd.DataFrame, z: float = 3.0, win: int = 24):
    out = df.copy()
    out["ret"] = out["price"].pct_change()
    out["vol_ma"] = out["volume"].rolling(win, min_periods=max(3, win//3)).mean()
    out["vol_sd"] = out["volume"].rolling(win, min_periods=max(3, win//3)).std(ddof=0)
    out["vol_z"] = (out["volume"] - out["vol_ma"]) / (out["vol_sd"].replace(0, np.nan))
    out["ret_ma"] = out["ret"].rolling(win, min_periods=max(3, win//3)).mean()
    out["ret_sd"] = out["ret"].rolling(win, min_periods=max(3, win//3)).std(ddof=0)
    out["ret_z"] = (out["ret"] - out["ret_ma"]) / (out["ret_sd"].replace(0, np.nan))
    out["vol_spike"] = out["vol_z"] > z
    out["pump_spike"] = out["ret_z"] > z
    out["dump_spike"] = out["ret_z"] < -z
    return out

def plot_anomalies(df: pd.DataFrame, out_path: str, label: str):
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax1.plot(df["ts"], df["price"], label="Price")
    ax1.set_ylabel("Price")
    ax1.set_title(f"{label}: Price & Volume (anomalies)")
    ax2 = ax1.twinx()
    ax2.plot(df["ts"], df["volume"], label="Volume", alpha=0.5)
    ax2.set_ylabel("Volume")
    for _, r in df[df["vol_spike"]].iterrows():
        ax2.scatter(r["ts"], r["volume"], s=30)
        ax2.annotate("Volume spike", (r["ts"], r["volume"]), xytext=(0, 18), textcoords="offset points", fontsize=8, rotation=30)
    for _, r in df[df["pump_spike"]].iterrows():
        ax1.scatter(r["ts"], r["price"], s=20)
        ax1.annotate("Pump", (r["ts"], r["price"]), xytext=(0, -22), textcoords="offset points", fontsize=8, rotation=30)
    for _, r in df[df["dump_spike"]].iterrows():
        ax1.scatter(r["ts"], r["price"], s=20)
        ax1.annotate("Dump", (r["ts"], r["price"]), xytext=(0, 14), textcoords="offset points", fontsize=8, rotation=30)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    print(f"[+] Saved {out_path}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--token-id", required=True)
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--z", type=float, default=3.0)
    ap.add_argument("--win", type=int, default=24)
    ap.add_argument("--out", default="out/task2_anomalies.png")
    args = ap.parse_args()

    df = fetch_token_market(args.token_id, days=args.days)
    df2 = detect_anomalies(df, z=args.z, win=args.win)
    plot_anomalies(df2, args.out, args.token_id)

    flagged = df2[(df2["vol_spike"]) | (df2["pump_spike"]) | (df2["dump_spike"])][["ts","price","volume","vol_z","ret_z"]]
    print("\n=== Flagged points ===")
    print(flagged.tail(15).to_string(index=False))

if __name__ == "__main__":
    main()
