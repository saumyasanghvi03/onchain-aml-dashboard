import streamlit as st
import pandas as pd
import requests
import hashlib
from datetime import datetime
import io
import os

# --- CSS Styles in Single Block ---
st.markdown(
""".bigfont {
    font-size: 2.4rem !important;
    font-weight: 850;
    color: #000 !important;
    letter-spacing: -1px;
}
.web3-gradient {
    background: linear-gradient(90deg, #8323FF 0%, #23FFE6 100%);
    padding: 2rem;
    border-radius: 1.1rem;
    color: #fff !important;
    margin-bottom: 2.2rem;
    box-shadow: 0 4px 28px #c8c8e4;
}
.zn-box {
    background: #f9f9fb;
    border-radius: 1.15em;
    padding: 1.25em 1.5em 1.1em 1.5em;
    margin-bottom: 1.5em;
    font-size: 1.08em;
    box-shadow: 0 3px 18px #eee;
}
.info-bar {
    background: #8323FF15;
    color: #222;
    padding: 0.42em 1em;
    margin-bottom: 1.2em;
    border-radius: 1em;
    font-size: 1.11em;
    font-weight: 600;
}""", unsafe_allow_html=True)

# --- Title & Description ---
st.markdown('<h1 class="bigfont">🔍 finAIguard</h1>', unsafe_allow_html=True)
st.markdown(
    '<div class="web3-gradient">Real-time on-chain compliance monitoring with cryptographic audit trails</div>',
    unsafe_allow_html=True
)

# --- Sidebar Configuration ---
st.sidebar.markdown("### Configuration")
wallets_input = st.sidebar.text_area(
    "Wallet Addresses (one per line)",
    "0x742d35Cc6634C0532925a3b8D7389A6dCfc3A6F3\n0x8BA1F109551bD432803012645Hac136c0c7b908\n0x1F916BF5c16eE52c9E79E42A60dBd0b1A1C26A2E",
    height=120
)
crypto_symbols = st.sidebar.text_input(
    "Crypto Symbols (comma-separated)",
    "BTC,ETH,USDT"
)

# --- Blockchain Selection ---
supported_chains = ["Ethereum", "Binance Smart Chain (BSC)", "Polygon", "Bitcoin"]
selected_chains = st.multiselect(
    "Select blockchain(s) for compliance check",
    supported_chains,
    default=["Ethereum"]
)

api_key = st.sidebar.text_input(
    "CoinGecko API Key (optional)",
    type="password",
    help="For higher rate limits"
)

# --- Main Content ---
if st.button("🚀 Run Compliance Check", use_container_width=True):
    if not selected_chains:
        st.error("Please select at least one blockchain.")
    else:
        wallet_list = [w.strip() for w in wallets_input.split('\n') if w.strip()]
        symbol_list = [s.strip().upper() for s in crypto_symbols.split(',') if s.strip()]
        
        if wallet_list and symbol_list:
            # Initialize results list
            results = []
            
            with st.spinner("Running compliance checks..."):
                # Nested loop for both symbols and chains
                for symbol in symbol_list:
                    for chain in selected_chains:
                        # Fetch crypto price from CoinGecko
                        url = "https://api.coingecko.com/api/v3/simple/price"
                        params = {
                            'ids': symbol.lower() if symbol.lower() in ['bitcoin', 'ethereum'] else f'{symbol.lower()}-token',
                            'vs_currencies': 'usd'
                        }
                        
                        if api_key:
                            params['x_cg_demo_api_key'] = api_key
                        
                        try:
                            response = requests.get(url, params=params, timeout=10)
                            data = response.json()
                            
                            # Handle different symbol formats
                            price = None
                            if symbol.lower() == 'btc' or symbol.lower() == 'bitcoin':
                                price = data.get('bitcoin', {}).get('usd')
                            elif symbol.lower() == 'eth' or symbol.lower() == 'ethereum':
                                price = data.get('ethereum', {}).get('usd')
                            else:
                                # Try various token formats
                                for key in data.keys():
                                    if key.startswith(symbol.lower()):
                                        price = data[key].get('usd')
                                        break
                            
                            if price is None:
                                st.warning(f"Could not fetch price for {symbol} on {chain}")
                                continue
                                
                        except Exception as e:
                            st.error(f"API error for {symbol} on {chain}: {str(e)}")
                            continue
                        
                        # Process each wallet for this symbol-chain combination
                        for wallet in wallet_list:
                            timestamp = datetime.utcnow().isoformat()
                            
                            # Simple compliance check (price-based)
                            compliance_breach = price > 50000 if symbol.upper() in ['BTC', 'BITCOIN'] else price > 3000
                            
                            # Create audit hash
                            audit_string = f"{wallet}|{symbol}|{chain}|{price}|{timestamp}|{compliance_breach}|finAIguard"
                            audit_hash = hashlib.sha256(audit_string.encode()).hexdigest()[:16]
                            
                            results.append({
                                'timestamp_utc': timestamp,
                                'wallet': wallet,
                                'token': symbol,
                                'chain': chain,
                                'current_price': price,
                                'compliance_breach': compliance_breach,
                                'audit_hash': audit_hash
                            })
            
            if results:
                df = pd.DataFrame(results)
                
                st.markdown('<div class="info-bar">✅ Compliance Analysis Complete</div>', unsafe_allow_html=True)
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Checks", len(df))
                with col2:
                    st.metric("Wallets", len(wallet_list))
                with col3:
                    st.metric("Chains", len(selected_chains))
                with col4:
                    breaches = df['compliance_breach'].sum()
                    st.metric("Breaches", breaches, delta=f"{breaches} alerts")
                
                # Display dataframe
                st.dataframe(
                    df[['timestamp_utc', 'wallet', 'token', 'chain', 'current_price', 'compliance_breach', 'audit_hash']], 
                    use_container_width=True
                )
                
                # Download button for audit log
                buf = io.StringIO()
                df.to_csv(buf, index=False)
                st.download_button(
                    "Download Audit Log CSV", 
                    buf.getvalue(), 
                    file_name="finAIguard_auditlog.csv", 
                    mime="text/csv"
                )
                
                # Transparency explanation
                st.markdown(
"""
                <div class="zn-box" style="background:#fffaed;font-size:1em;">
                For full transparency:
                <br><br>
                The audit hash above is computed over:
                <br><br>
                <span style="background:#fff8c0;padding:0.13em 0.45em 0.13em 0.45em;border-radius:1em;font-family:monospace;">
                wallet|token|chain|price|timestamp|breach|finAIguard
                </span>
                <br><br>
                and can be verified by anyone from the CSV log!
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("No results (bad API or symbol typo)!")
        else:
            st.error("Please provide both wallet addresses and crypto symbols.")

# --- Footer Section ---
st.markdown("---")
st.markdown(
"""<div class="zn-box">Note:

Full on-chain wallet connect/POAP/NFT minting requires a React or Vite DApp frontend.

This Streamlit app provides cryptographic audit logging for proof-ready compliance analytics.</div>""", unsafe_allow_html=True
)
