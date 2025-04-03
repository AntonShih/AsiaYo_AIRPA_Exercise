from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
import re
import json
import os

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-blink-features=AutomationControlled')  # 嘗試繞過反爬蟲檢測
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

# 增加更多日誌輸出
print("啟動爬蟲程式...")
print(f"當前工作目錄: {os.getcwd()}")

driver = webdriver.Chrome(options=options)

try:
    print("訪問網頁...")
    driver.get("https://asiayo.com/zh-tw/package/sport-activities/")
    
    # 等待頁面加載
    wait = WebDriverWait(driver, 30)
    print("等待頁面加載...")
    time.sleep(10)  # 增加等待時間
    
    # 保存頁面源代碼
    html_source = driver.page_source
    print(f"頁面源代碼長度: {len(html_source)} 字符")

    # 檢查頁面標題和內容
    print(f"頁面標題: {driver.title}")
    
    # 嘗試手動獲取所有活動卡片
    print("手動查找活動卡片...")
    
    # 新增：嘗試執行捲動來加載更多內容
    print("執行頁面捲動以加載更多內容...")
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)  # 等待捲動後的內容加載
    
    # 使用多種方法查找活動卡片
    card_selectors = [
        "div[class*='card']", 
        "div[class*='item']", 
        "a[href*='journey']",  # 基於您之前的截圖
        "div[class^='sc-']",   # 基於您之前的截圖中看到的類名模式
        "h2[class*='cezyBN']"  # 基於您之前的截圖
    ]
    
    all_cards = []
    for selector in card_selectors:
        cards = driver.find_elements(By.CSS_SELECTOR, selector)
        if cards:
            print(f"使用選擇器 '{selector}' 找到 {len(cards)} 個元素")
            all_cards.extend(cards)
    
    all_cards = list(set(all_cards))  # 去除重複
    print(f"總共找到 {len(all_cards)} 個可能的卡片元素")
    
    # 使用JavaScript直接抓取數據
    print("使用JavaScript抓取數據...")
    
    # 修改JavaScript來強化搜索能力
    js_extract = """
    // 優先尋找所有標題元素
    const titleSelectors = ['h1', 'h2', 'h3', 'h4', '[class*="title"]', '[class*="cezyBN"]'];
    let allTitles = [];
    
    for (const selector of titleSelectors) {
        const elements = document.querySelectorAll(selector);
        for (const el of elements) {
            const text = el.textContent.trim();
            if (text && text.length > 5) {
                allTitles.push(el);
            }
        }
    }
    
    console.log("找到 " + allTitles.length + " 個可能的標題元素");
    
    // 尋找所有價格元素
    const priceElements = Array.from(document.querySelectorAll('*')).filter(
        el => (el.textContent || '').includes('NT$') || 
              (el.textContent || '').includes('每人最低') ||
              (el.textContent || '').includes('$')
    );
    
    console.log("找到 " + priceElements.length + " 個可能的價格元素");
    
    // 嘗試將標題和價格配對
    const results = [];
    const processedTitles = new Set();
    
    // 函數：尋找最近的價格元素
    function findNearestPrice(titleEl) {
        // 檢查自身文本
        if (titleEl.textContent.includes('NT$') || titleEl.textContent.includes('$')) {
            return titleEl.textContent;
        }
        
        // 檢查相鄰元素
        let el = titleEl;
        let maxSteps = 10;  // 增加搜索範圍
        
        // 向下搜索
        while (el && maxSteps > 0) {
            const nextEl = el.nextElementSibling;
            if (nextEl) {
                if (nextEl.textContent.includes('NT$') || nextEl.textContent.includes('$')) {
                    return nextEl.textContent;
                }
            }
            el = nextEl;
            maxSteps--;
        }
        
        // 向上搜索
        el = titleEl;
        maxSteps = 10;
        
        while (el && maxSteps > 0) {
            if (el.parentElement) {
                const children = el.parentElement.children;
                for (const child of children) {
                    if (child !== titleEl && (child.textContent.includes('NT$') || child.textContent.includes('$'))) {
                        return child.textContent;
                    }
                }
                el = el.parentElement;
            } else {
                break;
            }
            maxSteps--;
        }
        
        // 搜索周圍的元素
        const rect = titleEl.getBoundingClientRect();
        for (const priceEl of priceElements) {
            const priceRect = priceEl.getBoundingClientRect();
            const distance = Math.sqrt(
                Math.pow(rect.top - priceRect.top, 2) + 
                Math.pow(rect.left - priceRect.left, 2)
            );
            
            // 如果距離足夠近，認為它們是相關的
            if (distance < 300) {  // 增加距離閾值
                return priceEl.textContent;
            }
        }
        
        return null;
    }
    
    // 對每個標題尋找相關價格
    for (const titleEl of allTitles) {
        const name = titleEl.textContent.trim();
        
        // 忽略已處理過的標題
        if (processedTitles.has(name)) continue;
        processedTitles.add(name);
        
        // 只考慮與運動或活動相關的標題
        if (name.includes('馬拉松') || name.includes('活動') || 
            name.includes('賽事') || name.includes('比賽') || 
            name.includes('山') || name.includes('運動') ||
            name.includes('節') || name.includes('遊')) {
            
            const priceText = findNearestPrice(titleEl);
            
            let price = '0';
            if (priceText) {
                const match = priceText.match(/\\$\\s*(\\d{1,3}(,\\d{3})*(\.\\d+)?)/);
                if (match) {
                    price = match[1].replace(/,/g, '');
                } else {
                    price = priceText.replace(/[^0-9]/g, '');
                }
            }
            
            results.push({
                name: name,
                price: price || '0',
                priceText: priceText || '未找到價格'
            });
        }
    }
    
    // 額外的方法：嘗試從href中找到活動
    const activityLinks = Array.from(document.querySelectorAll('a[href*="journey"]'));
    for (const link of activityLinks) {
        const possibleTitle = link.querySelector('h2, h3, h4, [class*="title"]');
        if (possibleTitle) {
            const name = possibleTitle.textContent.trim();
            
            // 忽略已處理過的標題
            if (processedTitles.has(name)) continue;
            processedTitles.add(name);
            
            const priceText = findNearestPrice(link);
            
            let price = '0';
            if (priceText) {
                const match = priceText.match(/\\$\\s*(\\d{1,3}(,\\d{3})*(\.\\d+)?)/);
                if (match) {
                    price = match[1].replace(/,/g, '');
                } else {
                    price = priceText.replace(/[^0-9]/g, '');
                }
            }
            
            results.push({
                name: name,
                price: price || '0',
                priceText: priceText || '未找到價格'
            });
        }
    }
    
    return results;
    """
    
    activities = driver.execute_script(js_extract)
    
    if activities:
        print(f"使用JavaScript找到 {len(activities)} 個活動")
        
        # 將結果保存為JSON，以便分析
        try:
            with open("/app/activities.json", "w", encoding="utf-8") as f:
                json.dump(activities, f, ensure_ascii=False, indent=2)
            print("成功保存activities.json到/app目錄")
        except Exception as e:
            print(f"保存JSON時出錯: {e}")
            
            # 嘗試保存到當前目錄
            try:
                with open("activities.json", "w", encoding="utf-8") as f:
                    json.dump(activities, f, ensure_ascii=False, indent=2)
                print("成功保存activities.json到當前目錄")
            except Exception as e2:
                print(f"保存到當前目錄也失敗: {e2}")
        
        # 將資料寫入CSV檔案 - 嘗試多個路徑
        csv_paths =  "./activity.csv"
        csv_success = False
        
        for csv_path in csv_paths:
            try:
                with open(csv_path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f, delimiter="\t")
                    writer.writerow(["賽事名稱", "每人最低價"])
                    for activity in activities:
                        writer.writerow([activity['name'], activity['price']])
                print(f"成功保存CSV到 {csv_path}")
                csv_success = True
                break
            except Exception as e:
                print(f"保存CSV到 {csv_path} 失敗: {e}")
        
        if csv_success:
            print(f"成功抓取 {len(activities)} 個活動，並儲存到 activity.csv")
        else:
            print("無法保存CSV文件到任何路徑")
        
        # 顯示找到的活動
        for i, activity in enumerate(activities):
            print(f"活動 {i+1}: {activity['name']} - 價格: {activity['priceText']}")
    else:
        print("未能使用JavaScript找到活動")
        
        # 如果前面的方法都失敗，創建一個解釋原因的CSV
        try:
            with open("/app/activity.csv", "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f, delimiter="\t")
                writer.writerow(["賽事名稱", "每人最低價"])
                writer.writerow(["無法抓取資料", "0"])
                writer.writerow(["原因: 網站使用複雜的動態加載技術或有反爬蟲機制", "0"])
            print("已創建包含錯誤說明的CSV文件")
        except Exception as e:
            print(f"創建錯誤說明CSV失敗: {e}")
            
            # 嘗試保存到當前目錄
            try:
                with open("activity.csv", "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f, delimiter="\t")
                    writer.writerow(["賽事名稱", "每人最低價"])
                    writer.writerow(["無法抓取資料", "0"])
                    writer.writerow(["原因: 網站使用複雜的動態加載技術或有反爬蟲機制", "0"])
                print("已在當前目錄創建包含錯誤說明的CSV文件")
            except Exception as e2:
                print(f"在當前目錄創建錯誤說明CSV也失敗: {e2}")
        
except Exception as e:
    print(f"發生錯誤: {e}")
    import traceback
    print(traceback.format_exc())
    
    # 發生錯誤時也創建一個CSV文件說明原因
    try:
        with open("/app/activity.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(["賽事名稱", "每人最低價"])
            writer.writerow(["爬蟲執行出錯", "0"])
            writer.writerow([f"錯誤: {str(e)}", "0"])
        print("已創建包含錯誤信息的CSV文件")
    except:
        try:
            with open("activity.csv", "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f, delimiter="\t")
                writer.writerow(["賽事名稱", "每人最低價"])
                writer.writerow(["爬蟲執行出錯", "0"])
                writer.writerow([f"錯誤: {str(e)}", "0"])
            print("已在當前目錄創建包含錯誤信息的CSV文件")
        except:
            print("無法創建錯誤信息CSV文件")
finally:
    driver.quit()
    print("完成!")