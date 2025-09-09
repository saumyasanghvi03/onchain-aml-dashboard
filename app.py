import streamlit as st
import pandas as pd
import requests
import hashlib
from datetime import datetime, date, time, timedelta
import io
import os
import re

# --- Token Mapping Dictionary (Top 10 by Market Cap, for Ethereum/ERC-20 where applicable) ---
TOKEN_MAPPING = {
    'BTC': 'bitcoin',             # Wrapped BTC on Ethereum
    'ETH': 'ethereum',            # Native ETH
    'USDT': 'tether',             # USDT on Ethereum
    'BNB': 'binancecoin',         # Wrapped BNB (rare on Ethereum, may show "not found" if not deployed)
    'SOL': 'solana',              # Wrapped SOL (if any, very uncommon on Ethereum)
    'XRP': 'ripple',              # Wrapped XRP (rare on Ethereum, CoinGecko may return null)
    'USDC': 'usd-coin',           # USDC on Ethereum
    'ADA': 'cardano',             # Wrapped ADA (rare on Ethereum, may not resolve)
    'DOGE': 'dogecoin',           # Wrapped DOGE (rare on Ethereum, may not resolve)
    'TON': 'the-open-network'     # Wrapped TON (rare, may not resolve)
}


# --- Utility Functions ---
def validate_ethereum_address(address):
    if not address or not isinstance(address, str):
        return False
    address = address.strip()
    return bool(re.match(r'^0x[a-fA-F0-9]{40}$', address))

def validate_symbols_input(symbols_input):
    if not symbols_input or not isinstance(symbols_input, str):
        return []
    symbols = [s.strip().upper() for s in symbols_input.split(',') if s.strip()]
    return symbols

def get_crypto_price(token_id, api_key=None):
    try:
        base_url = "https://api.coingecko.com/api/v3/simple/price"
        params = {'ids': token_id, 'vs_currencies': 'usd'}
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
etherscan_api_key = st.sidebar.text_input(
    "Etherscan API Key (optional)",
    value="",
    type="password",
    help="Your Etherscan API key for historical wallet activity analysis."
)

# --- Display Supported Tokens ---
with st.expander("ℹ️ Supported Tokens on Ethereum"):
    st.markdown("**Currently supported tokens on Ethereum:**")
    for symbol, token_id in TOKEN_MAPPING.items():
        st.markdown(f"- **{symbol}** ({token_id})")
    st.markdown("\n*Note: This app focuses on Ethereum-based tokens for compliance monitoring.*")

# --- Compliance Price Check Logic ---
if st.sidebar.button("🚀 Run Compliance Check", type="primary"):
    validation_errors = []
    if not wallets_input or not wallets_input.strip():
        validation_errors.append("Please provide at least one wallet address")
    else:
        wallet_list = [addr.strip() for addr in wallets_input.strip().split('\n') if addr.strip()]
        invalid_wallets = [addr for addr in wallet_list if not validate_ethereum_address(addr)]
        if invalid_wallets:
            validation_errors.append(f"Invalid wallet address(es): {', '.join(invalid_wallets[:3])}{'...' if len(invalid_wallets) > 3 else ''}")
        if not wallet_list:
            validation_errors.append("No valid wallet addresses found")
    if not crypto_symbols or not crypto_symbols.strip():
        validation_errors.append("Please provide at least one crypto symbol")
    else:
        symbols = validate_symbols_input(crypto_symbols)
        if not symbols:
            validation_errors.append("No valid crypto symbols found")
    if validation_errors:
        for error in validation_errors:
            st.error(f"❌ Validation Error: {error}")
        st.info("Please correct the above errors and try again.")
    else:
        try:
            wallet_list = [addr.strip() for addr in wallets_input.strip().split('\n') if addr.strip()]
            symbols = validate_symbols_input(crypto_symbols)
            supported_tokens = [symbol for symbol in symbols if symbol in TOKEN_MAPPING]
            unsupported_tokens = [symbol for symbol in symbols if symbol not in TOKEN_MAPPING]
            if unsupported_tokens:
                st.warning(f"⚠️ Unsupported tokens (skipped): {', '.join(unsupported_tokens)}")
            if not supported_tokens:
                st.error("❌ No supported tokens found. Please check the supported tokens list above.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                audit_data = []
                successful_tokens = []
                failed_tokens = []
                total_operations = len(wallet_list) * len(supported_tokens)
                current_operation = 0
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
                                compliance_breach = 1 if price > 1000 else 0
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
                progress_bar.empty()
                status_text.empty()
                if failed_tokens:
                    st.warning(f"⚠️ Failed to fetch data for: {', '.join(failed_tokens)}")
                if successful_tokens:
                    st.success(f"✅ Successfully processed: {', '.join(successful_tokens)}")
                if audit_data:
                    try:
                        df = pd.DataFrame(audit_data)
                        st.markdown("### 📊 Compliance Dashboard")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Checks", len(df))
                        with col2:
                            st.metric("Wallets", len(wallet_list))
                        with col3:
                            breaches = df['compliance_breach'].sum()
                            st.metric("Breaches", breaches, delta=f"{breaches} alerts")
                        st.dataframe(
                            df[['timestamp_utc', 'wallet', 'token', 'coingecko_id', 'current_price', 'compliance_breach', 'audit_hash']], 
                            use_container_width=True
                        )
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
    st.info("👆 Configure your wallet addresses and crypto symbols in the sidebar, then click 'Run Compliance Check' to begin.")
    with st.expander("📋 Preview: Dashboard Output"):
        st.markdown("When you run a compliance check, you'll see:")
        st.markdown("- 📊 **Metrics**: Total checks, wallets analyzed, compliance breaches")
        st.markdown("- 📋 **Data Table**: Detailed results with timestamps, prices, and audit hashes")
        st.markdown("- 📥 **Download**: CSV export of complete audit trail")
        st.markdown("- 🔐 **Transparency**: Cryptographic verification details")

# --- Period-based Ethereum Wallet Activity Analysis (Etherscan powered) ---
st.sidebar.subheader("Activity Analysis Period")
start_date = st.sidebar.date_input("Start date", date.today() - timedelta(days=7))
end_date = st.sidebar.date_input("End date", date.today())
activity_run = st.sidebar.button("🚀 Run Wallet Activity Analysis")

def fetch_eth_transactions(address, etherscan_api_key=None):
    api_key = etherscan_api_key or "VWJEDM7IYQZTX4KKDY45NSDT3IWB1PTJI5"
    url = (
        f"https://api.etherscan.io/api?module=account&action=txlist"
        f"&address={address}&startblock=0&endblock=99999999&sort=asc"
        f"&apikey={api_key}"
    )
    try:
        r = requests.get(url, timeout=12)
        data = r.json()
        if data.get("status") == "1":
            return data["result"]
        return []
    except Exception as e:
        st.error(f"Etherscan error for {address}: {e}")
        return []

def summarize_activity(txlist, start, end, large_amt=2.0):
    start_ts = int(datetime.combine(start, time.min).timestamp())
    end_ts = int(datetime.combine(end, time.max).timestamp())
    filtered = [tx for tx in txlist if start_ts <= int(tx["timeStamp"]) <= end_ts]
    sent, received, large = 0.0, 0.0, []
    for tx in filtered:
        eth = float(tx["value"]) / 1e18
        # Define direction as received if tx["to"] == current wallet, otherwise sent
        if eth >= large_amt:
            large.append(tx)
        received += eth
    return {
        "count": len(filtered),
        "received": received,
        "large_count": len(large),
        "large_txs": large,
        "all_txs": filtered
    }

if activity_run:
    wallets = [w.strip() for w in wallets_input.strip().split('\n') if w.strip()]
    for wallet in wallets:
        st.subheader(f"Activity for {wallet}")
        txlist = fetch_eth_transactions(wallet, etherscan_api_key)
        summ = summarize_activity(txlist, start_date, end_date)
        st.metric("Tx Count (period)", summ["count"])
        st.metric("Total Received (ETH)", f"{summ['received']:.4f}")
        st.metric("Large Transactions (>=2 ETH)", summ["large_count"])
        if summ["large_count"]:
            st.write("Large Transactions:")
            st.dataframe([
                {"Hash": tx["hash"], "Time": datetime.fromtimestamp(int(tx["timeStamp"])),
                 "From": tx["from"], "To": tx["to"],
                 "Value(ETH)": float(tx["value"]) / 1e18}
                for tx in summ["large_txs"]
            ])
        if summ["count"]:
            st.write("All Period Transactions:")
            st.dataframe([
                {"Hash": tx["hash"], "Time": datetime.fromtimestamp(int(tx["timeStamp"])),
                 "From": tx["from"], "To": tx["to"],
                 "Value(ETH)": float(tx["value"]) / 1e18}
                for tx in summ["all_txs"]
            ])
        else:
            st.info("No transactions for this wallet in selected period.")

# --- Footer Section ---
st.markdown("---")
st.info(
    "**Note:** Full on-chain wallet connect/POAP/NFT minting requires a React or Vite DApp frontend. "
    "This Streamlit app provides cryptographic audit logging for proof-ready compliance analytics with Ethereum-only support."
)
