import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# ===== CONFIGURATION =====
SOURCE_ADDRESS = os.getenv("SOURCE_ADDRESS")
TARGET_ADDRESS = os.getenv("TARGET_ADDRESS")
API_KEY = os.getenv("TRONGRID_API_KEY")

USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"

if API_KEY:
    HEADERS = {"TRON-PRO-API-KEY": API_KEY}
else:
    HEADERS = {}

TRONGRID = "https://api.trongrid.io"

def get_account_info():
    url = f"{TRONGRID}/v1/accounts/{SOURCE_ADDRESS}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        if data.get("data") and len(data["data"]) > 0:
            return data["data"][0]
        return None
    except Exception as e:
        print(f"Error getting account: {e}")
        return None

def get_usdt_balance():
    account = get_account_info()
    if not account:
        return 0
    tokens = account.get("trc20", [])
    for token in tokens:
        if USDT_CONTRACT in token:
            return int(token[USDT_CONTRACT])
    return 0

def get_trx_balance():
    account = get_account_info()
    if not account:
        return 0
    return account.get("balance", 0)

def sweep_usdt():
    try:
        balance = get_usdt_balance()
        if balance == 0:
            print(f"[{time.ctime()}] No USDT to sweep. Waiting...")
            return False

        readable_balance = balance / 1_000_000
        print(f"[{time.ctime()}] Found {readable_balance:,.2f} USDT!")
        
        trx_balance = get_trx_balance()
        trx_readable = trx_balance / 1_000_000
        print(f"[{time.ctime()}] TRX balance: {trx_readable:.6f} TRX")
        
        if trx_balance < 10_000_000:
            print(f"[{time.ctime()}] ⚠️ LOW TRX! Need at least 10 TRX for gas.")
            return False
        
        print(f"[{time.ctime()}] 🚀 USDT detected! Add TRX to source wallet to sweep.")
        print(f"[{time.ctime()}] 📤 Send USDT manually from {SOURCE_ADDRESS} to {TARGET_ADDRESS}")
        
        return True

    except Exception as e:
        print(f"[{time.ctime()}] ❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔄 TRON USDT SWEEPER BOT (CLOUD)")
    print("=" * 60)
    print(f"📤 Source: {SOURCE_ADDRESS}")
    print(f"📥 Target: {TARGET_ADDRESS}")
    print(f"📊 Watching: USDT (TRC-20)")
    print(f"🔑 API Key: {'✅ Set' if API_KEY else '❌ Not set'}")
    print("=" * 60)
    print(f"⏱️  Running 24/7 on Render.com")
    print("=" * 60)
    
    while True:
        try:
            if sweep_usdt():
                time.sleep(60)
            else:
                time.sleep(5)
        except Exception as e:
            print(f"[{time.ctime()}] ❌ Critical error: {e}")
            time.sleep(30)
