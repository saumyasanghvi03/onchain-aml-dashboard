import streamlit as st
import pandas as pd
import requests
import hashlib
from datetime import datetime
import io
import os

# --- Token-Chain Mapping Dictionary ---
# Maps (chain, symbol) to CoinGecko token ID for accurate price fetching
TOKEN_CHAIN_MAPPING = {
    # Bitcoin (BTC)
    ('Bitcoin', 'BTC'): 'bitcoin',
    ('Ethereum', 'BTC'): 'bitcoin',  # Wrapped BTC on Ethereum
    ('Binance Smart Chain (BSC)', 'BTC'): 'bitcoin',  # Wrapped BTC on BSC
    ('Polygon', 'BTC'): 'bitcoin',  # Wrapped BTC on Polygon
    
    # Ethereum (ETH)
    ('Ethereum', 'ETH'): 'ethereum',
    ('Binance Smart Chain (BSC)', 'ETH'): 'ethereum',  # Wrapped ETH on BSC
    ('Polygon', 'ETH'): 'ethereum',  # Wrapped ETH on Polygon
    
    # USDT
    ('Ethereum', 'USDT'): 'tether',
    ('Binance Smart Chain (BSC)', 'USDT'): 'tether',
    ('Polygon', 'USDT'): 'tether',
    ('Bitcoin', 'USDT'): 'tether',  # USDT on Bitcoin (Omni/Liquid)
}

# Supported combinations for clear user feedback
SUPPORTED_COMBINATIONS = set(TOKEN_CHAIN_MAPPING.keys())

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
}
.warning-box {
    background: #fff3cd;
    border: 1px solid #ffeaa7;
    color: #856404;
    padding: 0.75em 1em;
    margin-bottom: 1em;
    border-radius: 0.5em;
    font-size: 0.95em;
}
.success-box {
    background: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
    padding: 0.75em 1em;
    margin-bottom: 1em;
    border-radius: 0.5em;
    font-size: 0.95em;
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

# --- Display Supported Combinations ---
with st.expander("ℹ️ Supported Token-Chain Combinations"):
    st.markdown("**Currently supported combinations:**")
    supported_display = {}
    for (chain, symbol) in SUPPORTED_COMBINATIONS:
        if chain not in supported_display:
            supported_display[chain] = []
        supported_display[chain].append(symbol)
    
    for chain, symbols in supported_display.items():
        st.markdown(f"- **{chain}**: {', '.join(symbols)}")
    
    st.markdown("\n*Unsupported combinations will be skipped with clear warnings.*")

# --- Main Content ---
if st.button("🚀 Run Compliance Check", use_container_width=True):
    if not selected_chains:
        st.error("Please select at least one blockchain.")
    else:
        wallet_list = [w.strip() for w in wallets_input.split('\n') if w.strip()]
        symbol_list = [s.strip().upper() for s in crypto_symbols.split(',') if s.strip()]
        
        if wallet_list and symbol_list:
            # Initialize results list and tracking
            results = []
            skipped_combinations = []
            successful_combinations = []
            
            with st.spinner("Running compliance checks..."):
                # Nested loop for both symbols and chains
                for symbol in symbol_list:
                    for chain in selected_chains:
                        # Check if combination is supported
                        if (chain, symbol) not in SUPPORTED_COMBINATIONS:
                            skipped_combinations.append((chain, symbol))
                            continue
                        
                        # Get the correct CoinGecko token ID
                        coingecko_token_id = TOKEN_CHAIN_MAPPING[(chain, symbol)]
                        
                        # Fetch crypto price from CoinGecko using mapped token ID
                        url = "https://api.coingecko.com/api/v3/simple/price"
                        params = {
                            'ids': coingecko_token_id,
                            'vs_currencies': 'usd'
                        }
                        
                        if api_key:
                            params['x_cg_demo_api_key'] = api_key
                        
                        try:
                            response = requests.get(url, params=params, timeout=10)
                            data = response.json()
                            
                            # Extract price using the mapped token ID
                            price = data.get(coingecko_token_id, {}).get('usd')
                            
                            if price is None:
                                st.warning(f"Could not fetch price for {symbol} on {chain} (token_id: {coingecko_token_id})")
                                continue
                            
                            successful_combinations.append((chain, symbol, price))
                                
                        except Exception as e:
                            st.error(f"API error for {symbol} on {chain}: {str(e)}")
                            continue
                        
                        # Process each wallet for this symbol-chain combination
                        for wallet in wallet_list:
                            timestamp = datetime.utcnow().isoformat()
                            
                            # Enhanced compliance check (price-based with chain awareness)
                            if symbol.upper() == 'BTC':
                                compliance_breach = price > 50000
                            elif symbol.upper() == 'ETH':
                                compliance_breach = price > 3000
                            elif symbol.upper() == 'USDT':
                                # USDT should stay close to $1, flag if deviation > 5%
                                compliance_breach = abs(price - 1.0) > 0.05
                            else:
                                compliance_breach = False  # Default for unknown tokens
                            
                            # Create audit hash with chain-specific information
                            audit_string = f"{wallet}|{symbol}|{chain}|{coingecko_token_id}|{price}|{timestamp}|{compliance_breach}|finAIguard"
                            audit_hash = hashlib.sha256(audit_string.encode()).hexdigest()[:16]
                            
                            results.append({
                                'timestamp_utc': timestamp,
                                'wallet': wallet,
                                'token': symbol,
                                'chain': chain,
                                'coingecko_id': coingecko_token_id,
                                'current_price': price,
                                'compliance_breach': compliance_breach,
                                'audit_hash': audit_hash
                            })
            
            # Display warnings for skipped combinations
            if skipped_combinations:
                st.markdown('<div class="warning-box">', unsafe_allow_html=True)
                st.markdown("**⚠️ Skipped Unsupported Combinations:**")
                for chain, symbol in skipped_combinations:
                    st.markdown(f"• {symbol} on {chain} - not currently supported")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Display successful combinations
            if successful_combinations:
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.markdown("**✅ Successfully Processed Combinations:**")
                for chain, symbol, price in successful_combinations:
                    st.markdown(f"• {symbol} on {chain}: ${price:,.4f}")
                st.markdown('</div>', unsafe_allow_html=True)
            
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
                    st.metric("Supported Chains", len([c for c in selected_chains if any((c, s) in SUPPORTED_COMBINATIONS for s in symbol_list)]))
                with col4:
                    breaches = df['compliance_breach'].sum()
                    st.metric("Breaches", breaches, delta=f"{breaches} alerts")
                
                # Display dataframe with enhanced columns
                st.dataframe(
                    df[['timestamp_utc', 'wallet', 'token', 'chain', 'coingecko_id', 'current_price', 'compliance_breach', 'audit_hash']], 
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
                
                # Enhanced transparency explanation
                st.markdown(
"""
                <div class="zn-box" style="background:#fffaed;font-size:1em;">
                <strong>🔐 Audit Trail Transparency:</strong><br/><br/>
                
                The audit hash is computed over:<br/><br/>
                
                <span style="background:#fff8c0;padding:0.13em 0.45em 0.13em 0.45em;border-radius:1em;font-family:monospace;">
                wallet|token|chain|coingecko_id|price|timestamp|breach|finAIguard
                </span><br/><br/>
                
                This enhanced hash includes the specific CoinGecko token ID used for each chain,
                ensuring full traceability of price sources and chain-specific token mappings.
                All data can be verified from the CSV log!
                </div>
                """, unsafe_allow_html=True)
            else:
                if skipped_combinations and not successful_combinations:
                    st.error("No supported token-chain combinations found. Please check the supported combinations above.")
                else:
                    st.error("No results generated - API errors or invalid symbols.")
        else:
            st.error("Please provide both wallet addresses and crypto symbols.")

# --- Footer Section ---
st.markdown("---")
st.markdown(
"""<div class="zn-box">Note:
Full on-chain wallet connect/POAP/NFT minting requires a React or Vite DApp frontend.
This Streamlit app provides cryptographic audit logging for proof-ready compliance analytics with robust multi-chain token support.</div>""", unsafe_allow_html=True
)
