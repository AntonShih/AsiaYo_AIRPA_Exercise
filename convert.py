# convert.py

import csv
import json
import requests

# 讀取 CSV 轉 JSON
json_data = []
with open("activity.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f, delimiter="\t")
    for row in reader:
        json_data.append({
            "name": row["賽事名稱"],
            "price": int(row["每人最低價"])
        })

print("轉換後的 JSON:")
print(json.dumps(json_data, indent=2, ensure_ascii=False))

# 模擬 API 呼叫（不實際發送）
payload = json_data[0]
headers = {
    "channel": "CP",
    "user": "rpa",
    "contentType": "application/JSON"
}

print("\n模擬發送至 API:")
print(f"Payload: {payload}")
print(f"Headers: {headers}")

# 模擬回傳錯誤
mock_response = {
    "status": {
        "code": 500,
        "msg": "Validation failed."
    },
    "data": {
        "errors": "price: The price must be numeric"
    }
}

print("\n錯誤訊息：")
print(mock_response["data"]["errors"])
