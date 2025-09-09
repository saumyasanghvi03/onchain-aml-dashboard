import streamlit as st
import pandas as pd
import requests
import hashlib
from datetime import datetime
import io
import os

# --- Token Mapping Dictionary (Ethereum only) ---
# Maps token symbols to CoinGecko token IDs for Ethereum
TOKEN_MAPPING = {
    'BTC': 'bitcoin',    # Wrapped BTC on Ethereum
    'ETH': 'ethereum',   # Native ETH
    'USDT': 'tether'     # USDT on Ethereum
}

# --- Main App Interface ---
st.title("🔍 finAIguard")
st.markdown("Real-time Ethereum compliance monitoring with cryptographic audit trails")

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
api_key = st.sidebar.text_input(
    "CoinGecko API Key (optional)",
    type="password",
    help="For higher rate limits"
)

# --- Display Supported Tokens ---
with st.expander("ℹ️ Supported Tokens on Ethereum"):
    st.markdown("**Currently supported tokens on Ethereum:**")
    for symbol, coingecko_id in TOKEN_MAPPING.items():
        st.markdown(f"- **{symbol}**: {coingecko_id}")
    st.markdown("\n*Only Ethereum blockchain is supported. Unsupported tokens will be skipped.*")

# --- Main Content ---
if st.button("🚀 Run Compliance Check", use_container_width=True):
    wallet_list = [w.strip() for w in wallets_input.split('\n') if w.strip()]
    symbol_list = [s.strip().upper() for s in crypto_symbols.split(',') if s.strip()]
    
    if wallet_list and symbol_list:
        # Initialize results list and tracking
        results = []
        skipped_tokens = []
        successful_tokens = []
        
        with st.spinner("Running compliance checks on Ethereum..."):
            # Process each symbol
            for symbol in symbol_list:
                # Check if token is supported
                if symbol not in TOKEN_MAPPING:
                    skipped_tokens.append(symbol)
                    continue
                
                # Get the correct CoinGecko token ID
                coingecko_token_id = TOKEN_MAPPING[symbol]
                
                # Fetch crypto price from CoinGecko
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
                        st.warning(f"Could not fetch price for {symbol} (token_id: {coingecko_token_id})")
                        continue
                    
                    successful_tokens.append((symbol, price))
                        
                except Exception as e:
                    st.error(f"API error for {symbol}: {str(e)}")
                    continue
                
                # Process each wallet for this token
                for wallet in wallet_list:
                    timestamp = datetime.utcnow().isoformat()
                    
                    # Enhanced compliance check (price-based)
                    if symbol.upper() == 'BTC':
                        compliance_breach = price > 50000
                    elif symbol.upper() == 'ETH':
                        compliance_breach = price > 3000
                    elif symbol.upper() == 'USDT':
                        # USDT should stay close to $1, flag if deviation > 5%
                        compliance_breach = abs(price - 1.0) > 0.05
                    else:
                        compliance_breach = False  # Default for unknown tokens
                    
                    # Create audit hash (simplified for single chain)
                    audit_string = f"{wallet}|{symbol}|{coingecko_token_id}|{price}|{timestamp}|{compliance_breach}|finAIguard"
                    audit_hash = hashlib.sha256(audit_string.encode()).hexdigest()[:16]
                    
                    results.append({
                        'timestamp_utc': timestamp,
                        'wallet': wallet,
                        'token': symbol,
                        'coingecko_id': coingecko_token_id,
                        'current_price': price,
                        'compliance_breach': compliance_breach,
                        'audit_hash': audit_hash
                    })
        
        # Display warnings for skipped tokens
        if skipped_tokens:
            st.warning("⚠️ Skipped Unsupported Tokens:")
            for token in skipped_tokens:
                st.markdown(f"• {token} - not supported on Ethereum")
        
        # Display successful tokens
        if successful_tokens:
            st.success("✅ Successfully Processed Tokens on Ethereum:")
            for symbol, price in successful_tokens:
                st.markdown(f"• {symbol}: ${price:,.4f}")
        
        if results:
            df = pd.DataFrame(results)
            
            st.success("✅ Ethereum Compliance Analysis Complete")
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Checks", len(df))
            with col2:
                st.metric("Wallets", len(wallet_list))
            with col3:
                breaches = df['compliance_breach'].sum()
                st.metric("Breaches", breaches, delta=f"{breaches} alerts")
            
            # Display dataframe (without chain column)
            st.dataframe(
                df[['timestamp_utc', 'wallet', 'token', 'coingecko_id', 'current_price', 'compliance_breach', 'audit_hash']], 
                use_container_width=True
            )
            
            # Download button for audit log
            buf = io.StringIO()
            df.to_csv(buf, index=False)
            st.download_button(
                "Download Audit Log CSV", 
                buf.getvalue(), 
                file_name="finAIguard_ethereum_auditlog.csv", 
                mime="text/csv"
            )
            
            # Enhanced transparency explanation
            st.markdown(
                "### 🔐 Audit Trail Transparency\n\n"
                "The audit hash is computed over: `wallet|token|coingecko_id|price|timestamp|breach|finAIguard`\n\n"
                "This hash includes the specific CoinGecko token ID used for Ethereum tokens, "
                "ensuring full traceability of price sources. All data can be verified from the CSV log!"
            )
        else:
            if skipped_tokens and not successful_tokens:
                st.error("No supported tokens found for Ethereum. Please check the supported tokens above.")
            else:
                st.error("No results generated - API errors or invalid symbols.")
    else:
        st.error("Please provide both wallet addresses and crypto symbols.")

# --- Footer Section ---
st.markdown("---")
st.info(
    "**Note:** Full on-chain wallet connect/POAP/NFT minting requires a React or Vite DApp frontend. "
    "This Streamlit app provides cryptographic audit logging for proof-ready compliance analytics with Ethereum-only support."
)
