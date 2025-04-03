# main.py

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get("https://asiayo.com/zh-tw/package/sport-activities/")
time.sleep(5)

cards = driver.find_elements(By.CSS_SELECTOR, ".card-info")

data = []
for card in cards:
    try:
        name = card.find_element(By.CSS_SELECTOR, ".title").text
        price_text = card.find_element(By.CSS_SELECTOR, ".price").text
        price = int(''.join(filter(str.isdigit, price_text)))
        data.append([name, price])
    except Exception as e:
        print("跳過一筆，因為錯誤：", e)

driver.quit()

with open("activity.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["賽事名稱", "每人最低價"])
    writer.writerows(data)
