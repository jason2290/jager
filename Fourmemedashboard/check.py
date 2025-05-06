import requests
import time
import pandas as pd
import os

# 配置
API_KEY = "97RE3EJVJRZJD3N8E6KC38Y7G7XP4XKRB5"
CONTRACT_ADDRESS = "0x5c952063c7fc8610FFDB798152D69F0B9550762b"
BASE_URL = "https://api.bscscan.com/api"
PAGE_SIZE = 1000  # 每次請求的記錄數
VALUE_THRESHOLD = 10000000000000000  # 0.01 BNB (in Wei)
OUTPUT_FILE = "address.csv"  # 輸出文件名
LAST_BLOCK_FILE = "last_block.txt"  # 記錄上次處理的區塊號

def get_transactions(address, start_block, end_block, page=1, offset=PAGE_SIZE, retries=3):
    params = {
        "module": "account",
        "action": "txlist",
        "address": address,
        "startblock": start_block,
        "endblock": end_block,
        "page": page,
        "offset": offset,
        "sort": "asc",
        "apikey": API_KEY
    }
    for attempt in range(retries):
        try:
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            if data["status"] == "1":
                return data["result"]
            else:
                print(f"API Error: {data['message']}, Details: {data.get('result', 'No details')}")
                return []
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                print("Max retries reached.")
                return []

def save_to_csv(transactions, filename=OUTPUT_FILE, is_first_write=False):
    if not transactions:
        print("No transactions to save in this batch.")
        return
    df = pd.DataFrame(transactions, columns=["address", "value", "timestamp"])
    df.to_csv(filename, mode='a', index=False, header=is_first_write)
    print(f"Appended {len(df)} transactions to {filename}")

def save_last_block(last_block, filename=LAST_BLOCK_FILE):
    with open(filename, 'w') as f:
        f.write(str(last_block))
    print(f"Saved last processed block: {last_block} to {filename}")

def load_last_block(filename=LAST_BLOCK_FILE):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return int(f.read().strip())
        except (ValueError, IOError):
            print(f"Error reading {filename}, starting from scratch.")
            return None
    return None

def fetch_filtered_transactions(address, start_block=49073155, end_block=49200851, block_step=100):
    # 檢查上次處理的區塊
    last_block = load_last_block()
    if last_block is not None:
        # 從上次結束的區塊 + 1 開始，但不能小於用戶指定的 start_block
        actual_start_block = max(last_block + 1, start_block)
        print(f"Resuming from block {actual_start_block} (last processed: {last_block})")
    else:
        actual_start_block = start_block
        print(f"Starting from block {actual_start_block}")

    # 如果 actual_start_block 超過 end_block，無需處理
    if actual_start_block > end_block:
        print(f"No new blocks to process (start_block: {actual_start_block}, end_block: {end_block})")
        return 0

    filtered_transactions = []
    current_start = actual_start_block
    is_first_write = not os.path.exists(OUTPUT_FILE)  # 檢查是否為第一次寫入 CSV
    total_transactions = 0

    while current_start < end_block:
        current_end = min(current_start + block_step - 1, end_block)
        print(f"Fetching blocks {current_start} to {current_end}...")
        page = 1
        while True:
            print(f"  Page {page}...")
            transactions = get_transactions(address, current_start, current_end, page=page)
            if not transactions:
                break
            for tx in transactions:
                value = int(tx["value"])
                if value > VALUE_THRESHOLD:
                    value_in_bnb = value / 1e18
                    filtered_transactions.append({
                        "address": tx["from"],
                        "value": f"{value_in_bnb:.18f}",
                        "timestamp": tx["timeStamp"]  # 添加 timestamp
                    })
            if len(transactions) < PAGE_SIZE:
                break
            page += 1
            time.sleep(0.5)  # 分頁間延遲

        # 每輪 block_step 結束後將數據追加到 CSV
        if filtered_transactions:
            save_to_csv(filtered_transactions, filename=OUTPUT_FILE, is_first_write=is_first_write)
            total_transactions += len(filtered_transactions)
            filtered_transactions = []  # 清空當前數據，釋放內存
            is_first_write = False  # 後續寫入不再包含表頭

        # 保存當前處理的區塊範圍
        save_last_block(current_end)

        current_start += block_step
        time.sleep(0.5)  # 區塊範圍間延遲

    print(f"Total transactions with value > 0.01 BNB saved: {total_transactions}")
    return total_transactions

def main():
    print(f"Fetching transactions for {CONTRACT_ADDRESS}")
    total_transactions = fetch_filtered_transactions(CONTRACT_ADDRESS)
    print(f"Completed. Total transactions with value > 0.01 BNB: {total_transactions}")
    print(f"Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()