import streamlit as st
import pandas as pd
import requests
import hashlib
from datetime import datetime
import io
import os

# --- Web3/GenZ UI Styles ---
primary = "#8323FF"
safe = "#2ED47A"
danger = "#D7263D"
bg_gradient = "linear-gradient(90deg, #8323FF 0%, #23FFE6 100%)"

st.set_page_config(page_title="onchain aml dashboard: Web3 Crypto Compliance", layout="centered")

st.markdown(f""".bigfont {{
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
    font-size:1.08em;
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
<div class="web3-gradient">
    <span class="bigfont">finAIguard 🔮</span>
    <div style="font-size:1.28em; font-weight:600; margin-top: 0.5em;">Web3 Crypto Compliance & Fraud Dashboard</div>
    <div style="margin-top:0.5em;font-size:1.04em;letter-spacing:-0.01em;">Next-Gen RegTech for GenZ & DeFi</div>
</div>""", unsafe_allow_html=True)

st.markdown("""<div class="zn-box">
How it works:
🔗 Enter a public crypto wallet (used as unique proof-of-audit input)
🪙 Add tokens (BTC, ETH, etc)—checks live price compliance via CoinMarketCap
⛓️ Each token check gets a real SHA-256 audit hash for future proof
📥 Download your audit log as CSV—auditable by any party anytime
</div>""", unsafe_allow_html=True)

wallet_address = st.text_input("Enter your public wallet address (for immutable audit hash)", "")
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

def make_audit_hash(wallet, token, price, timestamp, breach):
    s = f"{wallet}|{token}|{price}|{timestamp}|{breach}|finAIguard"
    return hashlib.sha256(s.encode()).hexdigest()

if st.button("🧠 Check Crypto Compliance Now"):
    cryptos = [s.strip().upper() for s in crypto_symbols.split(',') if s.strip()]
    rows = []
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    for csym in cryptos:
        if not cmc_api_key:
            st.error("CMC API Key required!")
            st.stop()
        
        price = fetch_cmc_price(csym, cmc_api_key)
        if price is None:
            continue
        
        compliance_condition = price > 10000
        breach = "🚩 YES" if compliance_condition else "✅ OK"
        price_str = fmt_price(price)
        
        # Real audit hash with all fields made transparent below
        audit_hash = make_audit_hash(wallet_address, csym + "-USD", price_str, timestamp, breach)
        
        rows.append({
            "timestamp_utc": timestamp,
            "wallet": wallet_address or "(not provided)",
            "token": csym + "-USD",
            "current_price": price_str,
            "compliance_breach": breach,
            "audit_hash": audit_hash,
            "audit_formula": f"{wallet_address}|{csym + '-USD'}|{price_str}|{timestamp}|{breach}|finAIguard"
        })
    
    if rows:
        df = pd.DataFrame(rows)
        st.markdown("<div class=\"info-bar\">🔍 Live Compliance Audit Results (verifiable!):</div>", unsafe_allow_html=True)
        st.dataframe(df[["timestamp_utc", "wallet", "token", "current_price", "compliance_breach", "audit_hash"]], use_container_width=True)
        
        # Downloadable audit log with formula for proof
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        st.download_button("Download Audit Log CSV", buf.getvalue(), file_name="finAIguard_auditlog.csv", mime="text/csv")
        
        st.markdown("""
        <div class="zn-box" style="background:#fffaed;font-size:1em;">
        For full transparency:

        The audit hash above is computed over:

        <span style="background:#fff8c0;padding:0.13em 0.45em 0.13em 0.45em;border-radius:1em;font-family:monospace;">
        wallet|token|price|timestamp|breach|finAIguard
        </span>

        and can be verified by anyone from the CSV log!
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("No results (bad API or symbol typo)!")

st.markdown("""
---
<div class="zn-box">
Note:
Full on-chain wallet connect/POAP/NFT minting requires a React or Vite DApp frontend.

This Streamlit app provides cryptographic audit logging for proof-ready compliance analytics.
</div>""", unsafe_allow_html=True)
