import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

SOURCE_ADDRESS = os.getenv("SOURCE_ADDRESS")
TARGET_ADDRESS = os.getenv("TARGET_ADDRESS")
SOURCE_PRIVATE_KEY = os.getenv("SOURCE_PRIVATE_KEY")

TRONGRID = "https://api.trongrid.io"

def get_trx_balance(address):
    try:
        r = requests.get(f"{TRONGRID}/v1/accounts/{address}", timeout=10)
        data = r.json()
        if data.get("data"):
            return data["data"][0].get("balance", 0)
        return 0
    except Exception as e:
        print(f"Balance check error: {e}")
        return 0

def sweep_trx():
    balance = get_trx_balance(SOURCE_ADDRESS)
    if balance < 1_000_000:  # less than 1 TRX
        print(f"[{time.ctime()}] TRX too small: {balance / 1_000_000:.6f} TRX")
        return False

    # Keep 1 TRX for fees, send the rest
    send_amount = balance - 1_000_000

    # Get current block for ref
    block = requests.get(f"{TRONGRID}/wallet/getnowblock").json()
    ref_block_bytes = block["block_header"]["raw_data"]["number"]
    ref_block_hash = block["blockID"][16:32]

    # Build raw transaction
    tx = {
        "to_address": TARGET_ADDRESS,
        "owner_address": SOURCE_ADDRESS,
        "amount": send_amount,
        "ref_block_bytes": ref_block_bytes,
        "ref_block_hash": ref_block_hash,
        "timestamp": int(time.time() * 1000)
    }

    # Create unsigned transaction
    create_resp = requests.post(f"{TRONGRID}/wallet/createtransaction", json=tx).json()
    if "Error" in create_resp:
        print(f"Create error: {create_resp}")
        return False

    # Sign with private key
    sign_resp = requests.post(
        f"{TRONGRID}/wallet/getsignweight",
        json={"transaction": create_resp, "privateKey": SOURCE_PRIVATE_KEY.replace("0x", "")}
    ).json()

    # For actual signing, use the gettransactionsign endpoint
    sign_resp = requests.post(
        f"{TRONGRID}/wallet/gettransactionsign",
        json={"transaction": create_resp, "privateKey": SOURCE_PRIVATE_KEY.replace("0x", "")}
    ).json()

    # Broadcast
    broadcast = requests.post(f"{TRONGRID}/wallet/broadcasttransaction", json=sign_resp).json()

    if broadcast.get("result"):
        print(f"[{time.ctime()}] ✅ Swept {send_amount / 1_000_000:.6f} TRX | TX: {broadcast['txid']}")
        return True
    else:
        print(f"[{time.ctime()}] ❌ Broadcast failed: {broadcast}")
        return False

if __name__ == "__main__":
    print("🔄 TRX SWEEPER ACTIVE")
    print(f"📤 Source: {SOURCE_ADDRESS}")
    print(f"📥 Target: {TARGET_ADDRESS}")
    while True:
        try:
            if not sweep_trx():
                time.sleep(0.01)
            else:
                time.sleep(30)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)
