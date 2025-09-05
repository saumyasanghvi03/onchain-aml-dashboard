import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import hashlib

# --- Web3/GenZ Style ---
primary = "#8323FF"
safe = "#2ED47A"
danger = "#D7263D"
bg_gradient = "linear-gradient(90deg, #8323FF 0%, #23FFE6 100%)"

st.set_page_config(page_title="finAIguard: Web3 Crypto Compliance", layout="centered")

st.markdown(f"""
<style>
.bigfont {{
    font-size: 2.4rem !important;
    font-weight: 850;
    color: #000 !important;
    letter-spacing: -1px;
}}
.web3-gradient {{
    background: {bg_gradient};
    padding: 2rem;
    border-radius: 1.1rem;
    color: #fff !important;
    margin-bottom: 2.2rem;
    box-shadow: 0 4px 28px #c8c8e4;
}}
.zn-box {{
    background: #f9f9fb;
    border-radius: 1.15em;
    padding:1.25em 1.5em 1.1em 1.5em;
    margin-bottom:1.5em;
    font-size:1.07em;
    box-shadow: 0 3px 18px #eee;
}}
.info-bar {{
    background: #8323FF15;
    color: #222;
    padding: 0.42em 1em;
    margin-bottom: 1.2em;
    border-radius: 1em;
    font-size: 1.11em;
    font-weight: 600;
}}
</style>
<div class='web3-gradient'>
    <span class='bigfont'>finAIguard 🔮</span>
    <div style='font-size:1.28em; font-weight:600; margin-top: 0.5em;'>Web3 Crypto Compliance & Fraud Dashboard</div>
    <div style='margin-top:0.5em;font-size:1.04em;letter-spacing:-0.01em;'>Next-Gen RegTech for GenZ & DeFi</div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class='zn-box'>
<b>How it works:</b>
<ul>
<li>🔗 Enter your public crypto wallet (for hash proof only, not a connection)</li>
<li>🪙 Add any tokens (BTC, ETH, etc)—check live price compliance via CoinMarketCap</li>
<li>🚦 See flagged risks, instantly</li>
<li>⛓️ Copy a blockchain-style proof hash, ready for audit/NFT use</li>
</ul>
</div>
""", unsafe_allow_html=True)

# Main inputs
wallet_address = st.text_input("Enter your public wallet address (for demo audit hash)", "")
cmc_api_key = st.text_input("Your CoinMarketCap API Key", type="password")
crypto_symbols = st.text_input("Crypto symbols (comma-separated, e.g. BTC,ETH)", "BTC,ETH")

def fetch_cmc_price(symbol, api_key):
    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    params = {'symbol': symbol.upper(), 'convert':'USD'}
    headers = {'Accepts': 'application/json', 'X-CMC_PRO_API_KEY': api_key}
    try:
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
        price = r.json()['data'][symbol.upper()]['quote']['USD']['price']
        return float(price)
    except Exception as e:
        st.warning(f"CMC error for {symbol}: {e}")
        return None

def fmt_price(x):
    try:
        return f"${float(x):,.2f}"
    except Exception:
        return "N/A"

if st.button("🧠 Check Crypto Compliance Now"):
    cryptos = [s.strip().upper() for s in crypto_symbols.split(',') if s.strip()]
    rows = []
    for csym in cryptos:
        if not cmc_api_key:
            st.error("CMC API Key required!")
            st.stop()
        price = fetch_cmc_price(csym, cmc_api_key)
        if price is None:
            continue
        breach = "🚩 YES" if price > 10000 else "✅ OK"
        proof = hashlib.sha256(f"{csym}{price}{wallet_address}".encode()).hexdigest()[:20]
        rows.append({
            "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "token": csym + "-USD",
            "current_price": fmt_price(price),
            "wallet": wallet_address or "(not provided)",
            "compliance_breach": breach,
            "proof_hash": proof,
        })
    if rows:
        df = pd.DataFrame(rows)
        st.markdown("<div class='info-bar'>🔍 <b>Live Compliance Scan Results:</b></div>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.error("No results (bad API or symbol typo)!")

st.markdown("""
---
<div class='zn-box'>
<b>Web3 Tip:</b> 
Want true wallet connection for claim, sign, or on-chain POAP/NFT?<br>
Build a React or Vite app with <a href="https://docs.metamask.io/wallet/how-to/#integrate-with-your-web-app" target="_blank">MetaMask</a> or <a href='https://walletconnect.com/' target='_blank'>WalletConnect</a>.<br>
This Streamlit app provides compliance analytics and blockchain-proof audit hashes.
</div>
""", unsafe_allow_html=True)
