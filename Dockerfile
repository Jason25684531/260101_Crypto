# HighFreqQuant Trading System - Optimized for Scientific Computing
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
# build-essential: C/C++ 編譯器（numpy/pandas 需要）
# libopenblas-dev: 高性能線性代數庫（替代 libatlas，scipy 需要）
# pkg-config: 編譯配置工具
# libhdf5-dev: HDF5 支援（大數據處理）
# gfortran: Fortran 編譯器（某些科學計算庫需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libopenblas-dev \
    pkg-config \
    libhdf5-dev \
    gfortran \
    && rm -rf /var/lib/apt/lists/*

# 先複製 requirements.txt 以利用 Docker 快取
COPY requirements.txt .

# 安裝 Python 依賴（使用快取加速）
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼
COPY . .

# 創建必要的目錄
RUN mkdir -p /app/data /app/logs

# 設定環境變數
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Taipei

# 暴露端口（Flask API）
EXPOSE 5000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# 啟動命令（可在 docker-compose.yml 覆蓋）
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0"]
