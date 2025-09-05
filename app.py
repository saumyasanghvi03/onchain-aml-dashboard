import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import hashlib

st.set_page_config(page_title="finAIguard: Crypto Compliance", layout="centered")

st.markdown("""
# <span style='color:#000'>finAIguard 🔮</span>
**Web3 Crypto Compliance & Fraud Detection**
""", unsafe_allow_html=True)

cmc_api_key = st.text_input("Your CoinMarketCap API Key", type="password")
crypto_symbols = st.text_input("Crypto symbols (comma-separated: e.g. BTC,ETH,MATIC)", "BTC,ETH")
wallet_address = st.text_input("Your (public) wallet address (for proof hash; just for demo)")

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

if st.button("🔍 Check Crypto Compliance Live"):
    cryptos = [s.strip().upper() for s in crypto_symbols.split(',') if s.strip()]
    rows = []
    for csym in cryptos:
        if not cmc_api_key:
            st.error("CMC API Key required!")
            st.stop()
        price = fetch_cmc_price(csym, cmc_api_key)
        if price is None:
            continue
        breach = "YES" if price > 10000 else "No"
        proof = hashlib.sha256(f"{csym}{price}{wallet_address}".encode()).hexdigest()[:20]
        rows.append({
            'timestamp': datetime.utcnow(),
            'symbol': csym + '-USD',
            'price': price,
            'wallet': wallet_address or "(not provided)",
            'compliance_breach': breach,
            'proof_hash': proof
        })
    df = pd.DataFrame(rows)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.error("No results (API/symbol error)!")

st.markdown("""
---
**Web3 wallet connect & NFT acceptance is only possible in frontend JavaScript DApps.  
For true on-chain POAP claim/verification, deploy a React/Vite DApp with wallet connect as shown earlier.**
""")
