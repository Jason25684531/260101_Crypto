"""
HighFreqQuant 交易系統 - Streamlit Dashboard
提供市場數據視覺化、回測結果展示、交易信號監控
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import sys
import os

# 確保可以導入 app 模組
sys.path.insert(0, '/app')

# 頁面配置
st.set_page_config(
    page_title="HighFreqQuant Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== 輔助函數 ====================

@st.cache_data(ttl=300)  # 快取 5 分鐘
def load_market_data(symbol: str, timeframe: str, limit: int = 500):
    """從資料庫載入市場數據"""
    try:
        from app import create_app
        from app.extensions import db
        from app.models import OHLCV
        
        app = create_app()
        
        with app.app_context():
            records = OHLCV.query.filter_by(
                symbol=symbol,
                timeframe=timeframe
            ).order_by(OHLCV.timestamp.desc()).limit(limit).all()
            
            if not records:
                return pd.DataFrame()
            
            data = []
            for r in records:
                data.append({
                    'timestamp': pd.to_datetime(r.timestamp, unit='ms'),
                    'open': float(r.open),
                    'high': float(r.high),
                    'low': float(r.low),
                    'close': float(r.close),
                    'volume': float(r.volume)
                })
            
            df = pd.DataFrame(data)
            df.sort_values('timestamp', inplace=True)
            df.set_index('timestamp', inplace=True)
            return df
    except Exception as e:
        st.error(f"載入數據失敗: {e}")
        return pd.DataFrame()


def fetch_new_data(symbols: list, timeframe: str, limit: int):
    """從 Binance 獲取最新數據"""
    try:
        from app import create_app
        from app.extensions import db
        from app.core.data.fetcher import BinanceFetcher
        
        app = create_app()
        results = {}
        
        with app.app_context():
            fetcher = BinanceFetcher()
            for symbol in symbols:
                count = fetcher.fetch_and_save(
                    symbol=symbol,
                    timeframe=timeframe,
                    limit=limit,
                    db_session=db.session
                )
                results[symbol] = count
        
        return results
    except Exception as e:
        st.error(f"獲取數據失敗: {e}")
        return {}


def calculate_indicators(df: pd.DataFrame):
    """計算技術指標"""
    if df.empty:
        return df
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    df['bb_std'] = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (df['bb_std'] * 2)
    df['bb_lower'] = df['bb_middle'] - (df['bb_std'] * 2)
    
    # SMA
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    
    return df


def run_backtest(symbol: str, strategy: str):
    """執行回測"""
    try:
        from app.core.strategy.backtest import BacktestEngine
        
        engine = BacktestEngine(initial_capital=10000)
        df = engine.load_data_from_db(symbol, '1h')
        
        if df.empty:
            return None
        
        if strategy == 'RSI':
            return engine.run_rsi_strategy(df)
        elif strategy == 'Bollinger':
            return engine.run_bollinger_strategy(df)
        else:
            return None
    except Exception as e:
        st.error(f"回測失敗: {e}")
        return None


def get_kelly_position(win_rate: float = 0.55, odds: float = 1.5):
    """計算 Kelly 持倉比例"""
    try:
        from app.core.risk.kelly import KellyCalculator
        calculator = KellyCalculator(fraction=0.25)
        return calculator.calculate(win_rate, odds)
    except:
        # 簡易 Kelly 公式
        kelly = (win_rate * odds - (1 - win_rate)) / odds
        return max(0, min(kelly * 0.25, 0.25))


def get_panic_score():
    """計算恐慌指數（模擬）"""
    # 這裡使用模擬數據，實際應該從鏈上數據計算
    return np.random.uniform(0.3, 0.7)


# ==================== 圖表組件 ====================

def create_candlestick_chart(df: pd.DataFrame, symbol: str):
    """創建 K 線圖 with 布林帶"""
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.6, 0.2, 0.2],
        subplot_titles=(f'{symbol} K線圖', '成交量', 'RSI')
    )
    
    # K 線
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='K線'
        ),
        row=1, col=1
    )
    
    # 布林帶
    if 'bb_upper' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['bb_upper'],
                line=dict(color='rgba(250,128,114,0.5)', width=1),
                name='BB Upper'
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['bb_lower'],
                line=dict(color='rgba(144,238,144,0.5)', width=1),
                fill='tonexty',
                fillcolor='rgba(173,216,230,0.2)',
                name='BB Lower'
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['bb_middle'],
                line=dict(color='rgba(128,128,128,0.5)', width=1, dash='dash'),
                name='BB Middle'
            ),
            row=1, col=1
        )
    
    # 成交量
    colors = ['red' if df['close'].iloc[i] < df['open'].iloc[i] else 'green' 
              for i in range(len(df))]
    fig.add_trace(
        go.Bar(x=df.index, y=df['volume'], marker_color=colors, name='成交量'),
        row=2, col=1
    )
    
    # RSI
    if 'rsi' in df.columns:
        fig.add_trace(
            go.Scatter(x=df.index, y=df['rsi'], line=dict(color='purple', width=1), name='RSI'),
            row=3, col=1
        )
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
    
    fig.update_layout(
        height=800,
        xaxis_rangeslider_visible=False,
        template='plotly_dark'
    )
    
    return fig


def create_equity_curve(equity: list, dates: list):
    """創建資金曲線圖"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=equity,
        mode='lines',
        name='資金曲線',
        line=dict(color='#00ff88', width=2),
        fill='tozeroy',
        fillcolor='rgba(0,255,136,0.1)'
    ))
    
    fig.update_layout(
        title='📈 資金曲線 (Equity Curve)',
        xaxis_title='時間',
        yaxis_title='資金 (USDT)',
        template='plotly_dark',
        height=400
    )
    
    return fig


# ==================== 主介面 ====================

def main():
    # 側邊欄
    st.sidebar.title("🚀 HighFreqQuant")
    st.sidebar.markdown("---")
    
    # 交易對選擇
    symbol = st.sidebar.selectbox(
        "選擇交易對",
        ['BTC/USDT', 'ETH/USDT'],
        index=0
    )
    
    timeframe = st.sidebar.selectbox(
        "時間週期",
        ['1h', '4h', '1d'],
        index=0
    )
    
    st.sidebar.markdown("---")
    
    # 獲取數據按鈕
    if st.sidebar.button("🔄 獲取最新數據", use_container_width=True):
        with st.spinner("正在從 Binance 獲取數據..."):
            results = fetch_new_data(['BTC/USDT', 'ETH/USDT'], timeframe, 500)
            if results:
                st.sidebar.success(f"✅ 已更新 {sum(results.values())} 筆數據")
                st.cache_data.clear()
            else:
                st.sidebar.warning("⚠️ 無新數據")
    
    st.sidebar.markdown("---")
    
    # 策略選擇
    strategy = st.sidebar.selectbox(
        "回測策略",
        ['RSI', 'Bollinger'],
        index=0
    )
    
    # 主要內容區
    st.title("📊 HighFreqQuant 交易儀表板")
    
    # 建立頁籤
    tab1, tab2, tab3 = st.tabs(["📈 市場數據", "🎯 回測結果", "⚡ 交易信號"])
    
    # ==================== Tab 1: 市場數據 ====================
    with tab1:
        st.header(f"{symbol} 市場概覽")
        
        # 載入數據
        df = load_market_data(symbol, timeframe)
        
        if df.empty:
            st.warning("⚠️ 無數據，請先點擊「獲取最新數據」")
        else:
            # 計算指標
            df = calculate_indicators(df)
            
            # 顯示當前價格
            col1, col2, col3, col4 = st.columns(4)
            
            current_price = df['close'].iloc[-1]
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]
            current_rsi = df['rsi'].iloc[-1] if 'rsi' in df.columns else 0
            
            col1.metric(
                "當前價格",
                f"${current_price:,.2f}",
                f"{price_change:+.2%}"
            )
            col2.metric(
                "24h 最高",
                f"${df['high'].tail(24).max():,.2f}"
            )
            col3.metric(
                "24h 最低",
                f"${df['low'].tail(24).min():,.2f}"
            )
            col4.metric(
                "RSI (14)",
                f"{current_rsi:.1f}",
                "超買" if current_rsi > 70 else ("超賣" if current_rsi < 30 else "中性")
            )
            
            # K 線圖
            st.plotly_chart(create_candlestick_chart(df, symbol), use_container_width=True)
            
            # 數據統計
            with st.expander("📊 數據統計"):
                st.write(f"**數據筆數:** {len(df)}")
                st.write(f"**時間範圍:** {df.index.min()} ~ {df.index.max()}")
                st.dataframe(df.tail(10))
    
    # ==================== Tab 2: 回測結果 ====================
    with tab2:
        st.header(f"🎯 {strategy} 策略回測")
        
        if st.button("▶️ 執行回測", use_container_width=True):
            with st.spinner("正在執行回測..."):
                result = run_backtest(symbol, strategy)
                
                if result and result.get('success'):
                    # 儲存到 session state
                    st.session_state['backtest_result'] = result
                    st.success("✅ 回測完成！")
                else:
                    st.error("❌ 回測失敗，請確認資料庫有數據")
        
        # 顯示結果
        if 'backtest_result' in st.session_state:
            result = st.session_state['backtest_result']
            
            # 指標卡片
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric(
                "總報酬",
                f"{result['total_return']:.2%}",
                delta_color="normal" if result['total_return'] > 0 else "inverse"
            )
            col2.metric(
                "夏普比率",
                f"{result['sharpe_ratio']:.2f}"
            )
            col3.metric(
                "最大回撤",
                f"{result['max_drawdown']:.2%}"
            )
            col4.metric(
                "勝率",
                f"{result['win_rate']:.2%}"
            )
            
            # 資金曲線
            if result['equity_curve']:
                st.plotly_chart(
                    create_equity_curve(result['equity_curve'], result['equity_dates']),
                    use_container_width=True
                )
            
            # 詳細統計
            with st.expander("📊 詳細統計"):
                st.write(f"**初始資金:** $10,000")
                st.write(f"**最終資金:** ${result['final_value']:,.2f}")
                st.write(f"**總交易次數:** {result['total_trades']}")
                st.write(f"**獲利因子:** {result['profit_factor']:.2f}")
    
    # ==================== Tab 3: 交易信號 ====================
    with tab3:
        st.header("⚡ 即時交易信號")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📐 Kelly 持倉建議")
            
            # 從回測結果取得勝率
            win_rate = 0.55
            if 'backtest_result' in st.session_state:
                win_rate = max(0.4, st.session_state['backtest_result'].get('win_rate', 0.55))
            
            kelly_size = get_kelly_position(win_rate, 1.5)
            
            st.metric(
                "建議持倉比例",
                f"{kelly_size:.1%}",
                f"勝率: {win_rate:.1%}"
            )
            
            # 進度條
            st.progress(kelly_size / 0.25)  # 以 25% 為最大
            
            st.info(f"""
            **Kelly Criterion 計算說明**
            - 預估勝率: {win_rate:.1%}
            - 賠率 (Odds): 1.5
            - 使用 Quarter Kelly (保守策略)
            - 建議單筆持倉: {kelly_size:.1%} 總資金
            """)
        
        with col2:
            st.subheader("🚨 恐慌指數")
            
            panic_score = get_panic_score()
            
            # 顏色映射
            if panic_score < 0.4:
                color = "🟢"
                status = "低風險"
            elif panic_score < 0.7:
                color = "🟡"
                status = "中等風險"
            else:
                color = "🔴"
                status = "高風險"
            
            st.metric(
                "Panic Score",
                f"{color} {panic_score:.0%}",
                status
            )
            
            st.progress(panic_score)
            
            if panic_score > 0.8:
                st.error("⚠️ 恐慌指數過高！系統將拒絕買入訂單")
            elif panic_score > 0.6:
                st.warning("⚠️ 市場波動較大，建議減少持倉")
            else:
                st.success("✅ 市場穩定，可正常交易")
        
        # 交易建議
        st.markdown("---")
        st.subheader("📝 綜合交易建議")
        
        df = load_market_data(symbol, timeframe)
        if not df.empty:
            df = calculate_indicators(df)
            current_rsi = df['rsi'].iloc[-1] if 'rsi' in df.columns else 50
            
            if current_rsi < 30 and panic_score < 0.7:
                st.success(f"""
                🟢 **買入信號**
                - RSI ({current_rsi:.1f}) 處於超賣區
                - 恐慌指數 ({panic_score:.0%}) 在可接受範圍
                - 建議買入持倉比例: {kelly_size:.1%}
                """)
            elif current_rsi > 70:
                st.warning(f"""
                🟡 **賣出信號**
                - RSI ({current_rsi:.1f}) 處於超買區
                - 建議獲利了結部分持倉
                """)
            else:
                st.info(f"""
                ⚪ **觀望**
                - RSI ({current_rsi:.1f}) 處於中性區域
                - 等待更明確的交易信號
                """)
    
    # 頁腳
    st.sidebar.markdown("---")
    st.sidebar.caption("© 2025 HighFreqQuant Trading System")
    st.sidebar.caption("Phase 1.5: Local MVP & Visualization")


if __name__ == "__main__":
    main()
