import requests
import json

# API 端點
url = "https://api.jager.meme/api/airdrop/queryAirdrop/"

# 儲存 canAirdrop: true 的地址
can_airdrop_addresses = []

# 讀取 address.txt
with open("address.txt", "r") as file:
    addresses = [line.strip() for line in file if line.strip()]

# 對每個地址發送請求
for address in addresses:
    try:
        # 構造請求 URL
        full_url = f"{url}{address}"
        response = requests.get(full_url)
        
        # 檢查請求是否成功
        if response.status_code == 200:
            data = response.json()
            # 檢查 canAirdrop 是否為 true
            if data.get("data", {}).get("canAirdrop", False):
                can_airdrop_addresses.append(address)
        else:
            print(f"請求失敗 for address {address}: Status {response.status_code}")
            
    except Exception as e:
        print(f"錯誤 for address {address}: {str(e)}")

# 輸出所有 canAirdrop: true 的地址
print("可以空投的地址：")
for addr in can_airdrop_addresses:
    print(addr)

# 輸出總數
print(f"\n總共找到 {len(can_airdrop_addresses)} 個可以空投的地址")