import streamlit as st
import pandas as pd
import requests
import hashlib
from datetime import datetime
import io
import os
import re

# --- Token Mapping Dictionary (Ethereum only) ---
# Maps token symbols to CoinGecko token IDs for Ethereum
TOKEN_MAPPING = {
    'BTC': 'bitcoin',    # Wrapped BTC on Ethereum
    'ETH': 'ethereum',   # Native ETH
    'USDT': 'tether'     # USDT on Ethereum
}

# --- Utility Functions ---
def validate_ethereum_address(address):
    """Validate Ethereum wallet address format"""
    if not address or not isinstance(address, str):
        return False
    # Remove whitespace
    address = address.strip()
    # Check if it's a valid Ethereum address (0x followed by 40 hex characters)
    return bool(re.match(r'^0x[a-fA-F0-9]{40}$', address))

def validate_symbols_input(symbols_input):
    """Validate and clean crypto symbols input"""
    if not symbols_input or not isinstance(symbols_input, str):
        return []
    
    # Split by comma and clean up
    symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
    return symbols

def get_crypto_price(token_id, api_key=None):
    """Fetch price from CoinGecko with proper error handling"""
    try:
        base_url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': token_id,
            'vs_currencies': 'usd'
        }
        
        headers = {}
        if api_key:
            headers['x-cg-demo-api-key'] = api_key
        
        response = requests.get(base_url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if token_id in data and 'usd' in data[token_id]:
            return data[token_id]['usd']
        else:
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"API request failed for {token_id}: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error fetching price for {token_id}: {str(e)}")
        return None

def create_audit_hash(wallet, token, coingecko_id, price, timestamp, breach):
    """Create cryptographic hash for audit trail"""
    try:
        audit_string = f"{wallet}|{token}|{coingecko_id}|{price}|{timestamp}|{breach}|finAIguard"
        return hashlib.sha256(audit_string.encode()).hexdigest()[:16]
    except Exception as e:
        st.error(f"Error creating audit hash: {str(e)}")
        return "error"

# --- Main App Interface ---
st.title("🔍 finAIguard")
st.markdown("Real-time Ethereum compliance monitoring with cryptographic audit trails")

# --- Sidebar Configuration ---
st.sidebar.markdown("### Configuration")

wallets_input = st.sidebar.text_area(
    "Wallet Addresses (one per line)",
    "0x742d35Cc6634C0532925a3b8D7389A6dCfc3A6F3\n0x8BA1F109551bD432803012645Hac136c0c7b908\n0x1F916BF5c16eE52c9E79E42A60dBd0b1A1C26A2E",
    height=120,
    help="Enter Ethereum wallet addresses, one per line. Each address should start with 0x followed by 40 hex characters."
)

crypto_symbols = st.sidebar.text_input(
    "Crypto Symbols (comma-separated)",
    "BTC,ETH,USDT",
    help="Enter cryptocurrency symbols separated by commas. Only tokens supported on Ethereum are available."
)

api_key = st.sidebar.text_input(
    "CoinGecko API Key (optional)",
    type="password",
    help="For higher rate limits"
)

# --- Display Supported Tokens ---
with st.expander("ℹ️ Supported Tokens on Ethereum"):
    st.markdown("**Currently supported tokens on Ethereum:**")
    for symbol, token_id in TOKEN_MAPPING.items():
        st.markdown(f"- **{symbol}** ({token_id})")
    st.markdown("\n*Note: This app focuses on Ethereum-based tokens for compliance monitoring.*")

# --- Input Validation and Processing ---
if st.sidebar.button("🚀 Run Compliance Check", type="primary"):
    # Input validation
    validation_errors = []
    
    # Validate wallet addresses
    if not wallets_input or not wallets_input.strip():
        validation_errors.append("Please provide at least one wallet address")
    else:
        wallet_list = [addr.strip() for addr in wallets_input.strip().split('\n') if addr.strip()]
        invalid_wallets = [addr for addr in wallet_list if not validate_ethereum_address(addr)]
        
        if invalid_wallets:
            validation_errors.append(f"Invalid wallet address(es): {', '.join(invalid_wallets[:3])}{'...' if len(invalid_wallets) > 3 else ''}")
        
        if not wallet_list:
            validation_errors.append("No valid wallet addresses found")
    
    # Validate symbols
    if not crypto_symbols or not crypto_symbols.strip():
        validation_errors.append("Please provide at least one crypto symbol")
    else:
        symbols = validate_symbols_input(crypto_symbols)
        if not symbols:
            validation_errors.append("No valid crypto symbols found")
    
    # Display validation errors
    if validation_errors:
        for error in validation_errors:
            st.error(f"❌ Validation Error: {error}")
        st.info("Please correct the above errors and try again.")
    else:
        # Process valid inputs
        try:
            wallet_list = [addr.strip() for addr in wallets_input.strip().split('\n') if addr.strip()]
            symbols = validate_symbols_input(crypto_symbols)
            
            # Filter supported tokens
            supported_tokens = [symbol for symbol in symbols if symbol in TOKEN_MAPPING]
            unsupported_tokens = [symbol for symbol in symbols if symbol not in TOKEN_MAPPING]
            
            # Show warnings for unsupported tokens
            if unsupported_tokens:
                st.warning(f"⚠️ Unsupported tokens (skipped): {', '.join(unsupported_tokens)}")
            
            if not supported_tokens:
                st.error("❌ No supported tokens found. Please check the supported tokens list above.")
            else:
                # Processing indicators
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                audit_data = []
                successful_tokens = []
                failed_tokens = []
                
                total_operations = len(wallet_list) * len(supported_tokens)
                current_operation = 0
                
                # Process each wallet-token combination
                for wallet in wallet_list:
                    for symbol in supported_tokens:
                        current_operation += 1
                        progress = current_operation / total_operations
                        progress_bar.progress(progress)
                        status_text.text(f"Processing {symbol} for wallet {wallet[:10]}...")
                        
                        try:
                            token_id = TOKEN_MAPPING[symbol]
                            price = get_crypto_price(token_id, api_key)
                            
                            if price is not None:
                                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                
                                # Simple compliance check (price > $1000 = breach)
                                compliance_breach = 1 if price > 1000 else 0
                                
                                # Create audit hash
                                audit_hash = create_audit_hash(
                                    wallet, symbol, token_id, price, timestamp, compliance_breach
                                )
                                
                                audit_data.append({
                                    'timestamp_utc': timestamp,
                                    'wallet': wallet,
                                    'token': symbol,
                                    'coingecko_id': token_id,
                                    'current_price': price,
                                    'compliance_breach': compliance_breach,
                                    'audit_hash': audit_hash
                                })
                                
                                if symbol not in successful_tokens:
                                    successful_tokens.append(symbol)
                            else:
                                if symbol not in failed_tokens:
                                    failed_tokens.append(symbol)
                                    
                        except Exception as e:
                            st.error(f"Error processing {symbol} for {wallet}: {str(e)}")
                            if symbol not in failed_tokens:
                                failed_tokens.append(symbol)
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
                # Show processing results
                if failed_tokens:
                    st.warning(f"⚠️ Failed to fetch data for: {', '.join(failed_tokens)}")
                
                if successful_tokens:
                    st.success(f"✅ Successfully processed: {', '.join(successful_tokens)}")
                
                # Display results
                if audit_data:
                    try:
                        df = pd.DataFrame(audit_data)
                        
                        st.markdown("### 📊 Compliance Dashboard")
                        
                        # Metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Checks", len(df))
                        with col2:
                            st.metric("Wallets", len(wallet_list))
                        with col3:
                            breaches = df['compliance_breach'].sum()
                            st.metric("Breaches", breaches, delta=f"{breaches} alerts")
                        
                        # Display dataframe
                        st.dataframe(
                            df[['timestamp_utc', 'wallet', 'token', 'coingecko_id', 'current_price', 'compliance_breach', 'audit_hash']], 
                            use_container_width=True
                        )
                        
                        # Download button (only enabled when results exist)
                        try:
                            buf = io.StringIO()
                            df.to_csv(buf, index=False)
                            st.download_button(
                                "📥 Download Audit Log CSV", 
                                buf.getvalue(), 
                                file_name="finAIguard_ethereum_auditlog.csv", 
                                mime="text/csv",
                                help="Download complete audit trail as CSV file"
                            )
                        except Exception as e:
                            st.error(f"Error preparing download: {str(e)}")
                        
                        # Enhanced transparency explanation
                        st.markdown(
                            "### 🔐 Audit Trail Transparency\n\n"
                            "The audit hash is computed over: `wallet|token|coingecko_id|price|timestamp|breach|finAIguard`\n\n"
                            "This hash includes the specific CoinGecko token ID used for Ethereum tokens, "
                            "ensuring full traceability of price sources. All data can be verified from the CSV log!"
                        )
                        
                    except Exception as e:
                        st.error(f"Error creating results dataframe: {str(e)}")
                        st.info("Please try again or contact support if the issue persists.")
                        
                else:
                    if not supported_tokens:
                        st.error("❌ No supported tokens found for Ethereum. Please check the supported tokens above.")
                    elif failed_tokens and not successful_tokens:
                        st.error("❌ All API requests failed. Please check your internet connection and try again.")
                        st.info("If you have a CoinGecko API key, try adding it in the sidebar for better reliability.")
                    else:
                        st.error("❌ No results generated. This could be due to API errors or network issues.")
                        st.info("Please try again in a few moments.")
                        
        except Exception as e:
            st.error(f"❌ Unexpected error during processing: {str(e)}")
            st.info("Please refresh the page and try again. If the issue persists, contact support.")
else:
    # Default state - no action taken yet
    st.info("👆 Configure your wallet addresses and crypto symbols in the sidebar, then click 'Run Compliance Check' to begin.")
    
    # Show example of what the dashboard looks like
    with st.expander("📋 Preview: Dashboard Output"):
        st.markdown("When you run a compliance check, you'll see:")
        st.markdown("- 📊 **Metrics**: Total checks, wallets analyzed, compliance breaches")
        st.markdown("- 📋 **Data Table**: Detailed results with timestamps, prices, and audit hashes")
        st.markdown("- 📥 **Download**: CSV export of complete audit trail")
        st.markdown("- 🔐 **Transparency**: Cryptographic verification details")

# --- Footer Section ---
st.markdown("---")
st.info(
    "**Note:** Full on-chain wallet connect/POAP/NFT minting requires a React or Vite DApp frontend. "
    "This Streamlit app provides cryptographic audit logging for proof-ready compliance analytics with Ethereum-only support."
)
