FROM python:3.10-slim

# 設置 Debian 前端為非互動模式
ENV DEBIAN_FRONTEND=noninteractive

# 安裝必要的套件
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 設定環境變數
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# 移除 webdriver-manager (因為不再需要下載 chromedriver)
RUN pip uninstall -y webdriver-manager

CMD ["python", "-u", "Crawler.py"]
