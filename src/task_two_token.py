import os
import argparse
import requests
import pandas as pd
import matplotlib.pyplot as plt

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=30"

def fetch_token_data(token="bitcoin", days=30, vs="usd"):
    """
    Pull token price + volume data from CoinGecko.
    """
    try:
        url = COINGECKO_URL.format(token=token)
        resp = requests.get(url, params={"vs_currency": vs, "days": days}, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print("[!] fetch failed:", e)
        return pd.DataFrame() 

    prices = pd.DataFrame(data.get("prices", []), columns=["ts", "price"])
    volumes = pd.DataFrame(data.get("total_volumes", []), columns=["ts", "volume"])
    prices["ts"] = pd.to_datetime(prices["ts"], unit="ms")
    volumes["ts"] = pd.to_datetime(volumes["ts"], unit="ms")
    df = prices.merge(volumes, on="ts")
    return df

def plot_anomalies(df, token="bitcoin", out_path="out/task2_analysis.png"):
    """
    Plot volume over time and flag unusual spikes.
    """
    if df.empty:
        print("[i] no data to plot")
        return

df = fetch_token_data("dogecoin", days=30)

print(df.head())


out_path = "out/task2_doge.png"
token = "dogecoin"

threshold = df["volume"].mean() + 2 * df["volume"].std()
spikes = df[df["volume"] > threshold]

plt.figure(figsize=(12, 6))
plt.plot(df["ts"], df["volume"], label="Volume", color="orange")
plt.scatter(spikes["ts"], spikes["volume"], color="red", label="suspicious spike")
plt.title(f"{token.upper()} trading volume (last {len(df)//24} days)")
plt.xlabel("Date")
plt.ylabel("Volume")
plt.legend()
plt.tight_layout()
plt.savefig(out_path, dpi=200)
plt.close()

abs_path = os.path.abspath(out_path)
print(f"[saved] {abs_path}")

def parse_arguments():
    import sys
    ap = argparse.ArgumentParser()
    ap.add_argument("--token", default="bitcoin", help="coin id (e.g. bitcoin, ethereum, dogecoin)")
    ap.add_argument("--days", type=int, default=30, help="days of history (7/14/30)")
    ap.add_argument("--out", default="out/task2_analysis.png", help="output PNG path")


    if "ipykernel" in sys.modules:
        return ap.parse_args([])   
    return ap.parse_args()

def main():
    args = parse_arguments()
    print(f"[i] fetching {args.token} data for {args.days} days…")
    df = fetch_token_data(args.token, args.days)

    if df.empty:
        print("[!] no data fetched, exiting")
        return

    print("[i] plotting anomalies…")
    plot_anomalies(df, args.token, args.out)


if __name__ == "__main__":
    main()

