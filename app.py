"""
Quant Trading Web App - Streamlit Prototype
Interactive backtesting dashboard for quantitative trading strategies
"""

import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import traceback

# Page configuration
st.set_page_config(
    page_title="Quant Trading Backtester",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .strategy-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin: 1rem 0;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #e8f4f8;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# ===== STRATEGY IMPLEMENTATIONS =====

def macd_strategy(df, ma1=10, ma2=21):
    """
    MACD Oscillator strategy implementation

    Args:
        df (pd.DataFrame): Price data with OHLC columns
        ma1 (int): Short moving average period
        ma2 (int): Long moving average period

    Returns:
        pd.DataFrame: DataFrame with signals and indicators
    """
    signals = df.copy()

    # Calculate moving averages
    signals['MA1'] = signals['Close'].rolling(window=ma1, min_periods=1).mean()
    signals['MA2'] = signals['Close'].rolling(window=ma2, min_periods=1).mean()

    # Generate positions
    signals['Position'] = 0
    signals.loc[ma1:, 'Position'] = np.where(
        signals['MA1'][ma1:] >= signals['MA2'][ma1:], 1, 0
    )

    # Generate trading signals
    signals['Signal'] = signals['Position'].diff()

    # Calculate oscillator
    signals['Oscillator'] = signals['MA1'] - signals['MA2']

    return signals


def calculate_metrics(df, initial_capital=20000):
    """
    Calculate portfolio metrics

    Args:
        df (pd.DataFrame): DataFrame with signals
        initial_capital (float): Initial capital

    Returns:
        dict: Dictionary of performance metrics
    """
    # Calculate returns
    df['Returns'] = df['Close'].pct_change()
    df['Strategy_Returns'] = df['Position'].shift(1) * df['Returns']

    # Calculate cumulative returns
    df['Cumulative_Returns'] = (1 + df['Returns']).cumprod()
    df['Cumulative_Strategy_Returns'] = (1 + df['Strategy_Returns']).cumprod()

    # Calculate portfolio value
    df['Portfolio_Value'] = initial_capital * df['Cumulative_Strategy_Returns']

    # Calculate metrics
    total_return = (df['Portfolio_Value'].iloc[-1] - initial_capital) / initial_capital * 100
    buy_hold_return = (df['Cumulative_Returns'].iloc[-1] - 1) * 100

    # Sharpe ratio (annualized)
    sharpe = (df['Strategy_Returns'].mean() / df['Strategy_Returns'].std()) * np.sqrt(252)

    # Max drawdown
    cumulative = df['Cumulative_Strategy_Returns']
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min() * 100

    # Win rate
    winning_trades = (df['Strategy_Returns'] > 0).sum()
    total_trades = (df['Signal'] != 0).sum()
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    return {
        'total_return': total_return,
        'buy_hold_return': buy_hold_return,
        'sharpe_ratio': sharpe,
        'max_drawdown': max_drawdown,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'final_value': df['Portfolio_Value'].iloc[-1]
    }


def create_candlestick_chart(df, ticker):
    """
    Create interactive candlestick chart with signals

    Args:
        df (pd.DataFrame): DataFrame with OHLC and signals
        ticker (str): Stock ticker symbol

    Returns:
        plotly.graph_objects.Figure: Interactive chart
    """
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.5, 0.25, 0.25],
        subplot_titles=(f'{ticker} - Price & Signals', 'MACD Oscillator', 'Portfolio Value')
    )

    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price'
        ),
        row=1, col=1
    )

    # Moving averages
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['MA1'],
            mode='lines',
            name='MA1 (Short)',
            line=dict(color='blue', width=1)
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['MA2'],
            mode='lines',
            name='MA2 (Long)',
            line=dict(color='orange', width=1, dash='dot')
        ),
        row=1, col=1
    )

    # Buy signals
    buy_signals = df[df['Signal'] == 1]
    fig.add_trace(
        go.Scatter(
            x=buy_signals.index,
            y=buy_signals['Close'],
            mode='markers',
            name='매수',
            marker=dict(symbol='triangle-up', size=12, color='green')
        ),
        row=1, col=1
    )

    # Sell signals
    sell_signals = df[df['Signal'] == -1]
    fig.add_trace(
        go.Scatter(
            x=sell_signals.index,
            y=sell_signals['Close'],
            mode='markers',
            name='매도',
            marker=dict(symbol='triangle-down', size=12, color='red')
        ),
        row=1, col=1
    )

    # MACD Oscillator
    colors = ['red' if val < 0 else 'green' for val in df['Oscillator']]
    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df['Oscillator'],
            name='MACD',
            marker_color=colors
        ),
        row=2, col=1
    )

    # Portfolio value
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['Portfolio_Value'],
            mode='lines',
            name='Portfolio',
            line=dict(color='purple', width=2),
            fill='tonexty'
        ),
        row=3, col=1
    )

    # Update layout
    fig.update_layout(
        height=900,
        showlegend=True,
        xaxis_rangeslider_visible=False,
        hovermode='x unified'
    )

    fig.update_yaxes(title_text="가격 ($)", row=1, col=1)
    fig.update_yaxes(title_text="Oscillator", row=2, col=1)
    fig.update_yaxes(title_text="포트폴리오 가치 ($)", row=3, col=1)
    fig.update_xaxes(title_text="날짜", row=3, col=1)

    return fig


# ===== MAIN APP =====

def main():
    """Main Streamlit application"""

    # Header
    st.markdown('<div class="main-header">📈 Quant Trading Backtester</div>', unsafe_allow_html=True)
    st.markdown("**양적 거래 전략 백테스팅 웹앱** - 안전하고 로컬에서만 실행됩니다")

    # Sidebar - Strategy Selection
    st.sidebar.header("⚙️ 전략 설정")

    strategy = st.sidebar.selectbox(
        "전략 선택",
        ["MACD Oscillator", "Pair Trading (준비 중)", "Bollinger Bands (준비 중)"]
    )

    st.sidebar.markdown("---")

    # Parameters
    st.sidebar.header("📊 파라미터")

    ticker = st.sidebar.text_input(
        "티커 심볼",
        value="AAPL",
        help="예: AAPL, NVDA, TSLA"
    ).upper()

    col1, col2 = st.sidebar.columns(2)
    with col1:
        ma1 = st.number_input("MA1 (단기)", min_value=1, max_value=500, value=10)
    with col2:
        ma2 = st.number_input("MA2 (장기)", min_value=1, max_value=500, value=21)

    # Validate MA pair
    if ma1 >= ma2:
        st.sidebar.error(f"⚠️ MA1 ({ma1})은 MA2 ({ma2})보다 작아야 합니다")
        return

    # Date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*2)  # Default: 2 years

    date_col1, date_col2 = st.sidebar.columns(2)
    with date_col1:
        start_input = st.date_input(
            "시작 날짜",
            value=start_date,
            max_value=end_date
        )
    with date_col2:
        end_input = st.date_input(
            "종료 날짜",
            value=end_date,
            max_value=end_date
        )

    initial_capital = st.sidebar.number_input(
        "초기 자본 ($)",
        min_value=1000,
        max_value=1000000,
        value=20000,
        step=1000
    )

    st.sidebar.markdown("---")

    # Run backtest button
    if st.sidebar.button("🚀 백테스트 실행", type="primary"):

        try:
            with st.spinner(f"📥 {ticker} 데이터 다운로드 중..."):

                # Download data
                df = yf.download(
                    ticker,
                    start=start_input,
                    end=end_input,
                    progress=False
                )

                if df.empty:
                    st.error(f"❌ '{ticker}'에 대한 데이터를 가져올 수 없습니다. 티커를 확인해주세요.")
                    return

                st.success(f"✓ {len(df)}개의 데이터 포인트 다운로드 완료")

            # Run strategy
            with st.spinner("⚙️ 전략 실행 중..."):
                signals = macd_strategy(df, ma1, ma2)
                metrics = calculate_metrics(signals, initial_capital)

            # Display metrics
            st.markdown("## 📊 백테스팅 결과")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "총 수익률",
                    f"{metrics['total_return']:.2f}%",
                    delta=f"{metrics['total_return'] - metrics['buy_hold_return']:.2f}% vs 매수&보유"
                )

            with col2:
                st.metric(
                    "샤프 비율",
                    f"{metrics['sharpe_ratio']:.2f}",
                    help="위험 대비 수익률 (>1 양호)"
                )

            with col3:
                st.metric(
                    "최대 낙폭",
                    f"{metrics['max_drawdown']:.2f}%",
                    delta=None
                )

            with col4:
                st.metric(
                    "승률",
                    f"{metrics['win_rate']:.1f}%",
                    delta=None
                )

            col5, col6, col7, col8 = st.columns(4)

            with col5:
                st.metric("총 거래 횟수", f"{int(metrics['total_trades'])}")

            with col6:
                st.metric("최종 자산", f"${metrics['final_value']:,.2f}")

            with col7:
                st.metric("매수&보유 수익률", f"{metrics['buy_hold_return']:.2f}%")

            with col8:
                profit = metrics['final_value'] - initial_capital
                st.metric("손익", f"${profit:,.2f}")

            # Display chart
            st.markdown("## 📈 차트")
            fig = create_candlestick_chart(signals, ticker)
            st.plotly_chart(fig, use_container_width=True)

            # Display trade log
            st.markdown("## 📝 거래 내역")
            trades = signals[signals['Signal'] != 0][['Close', 'Signal', 'MA1', 'MA2']].copy()
            trades['거래유형'] = trades['Signal'].map({1: '매수 🟢', -1: '매도 🔴'})
            trades = trades.rename(columns={
                'Close': '가격',
                'MA1': '단기MA',
                'MA2': '장기MA'
            })
            st.dataframe(trades[['거래유형', '가격', '단기MA', '장기MA']], use_container_width=True)

            # Privacy note
            st.info("""
            🔒 **프라이버시 안내**:
            - 모든 계산은 **로컬 컴퓨터**에서만 실행됩니다
            - Yahoo Finance에서 공개 시장 데이터만 다운로드합니다
            - 귀하의 백테스팅 결과는 **외부로 전송되지 않습니다**
            - 데이터는 세션 종료 시 자동 삭제됩니다
            """)

        except Exception as e:
            st.error(f"❌ 오류 발생: {str(e)}")
            with st.expander("🔍 상세 오류 정보"):
                st.code(traceback.format_exc())

    else:
        # Welcome message
        st.markdown("""
        ## 👋 환영합니다!

        이 웹앱은 **양적 거래 전략**을 백테스팅할 수 있는 도구입니다.

        ### 🚀 사용 방법:

        1. **왼쪽 사이드바**에서 전략과 파라미터를 선택하세요
        2. **티커 심볼** (예: AAPL, NVDA)을 입력하세요
        3. **날짜 범위**를 설정하세요
        4. **"백테스트 실행"** 버튼을 클릭하세요

        ### 📊 지원 전략:

        - **MACD Oscillator**: 이동평균 수렴/발산 모멘텀 전략
        - **Pair Trading**: 공적분 기반 통계적 차익거래 (준비 중)
        - **Bollinger Bands**: 볼린저 밴드 패턴 인식 (준비 중)

        ### 🔒 보안 & 프라이버시:

        - ✅ 모든 계산은 **로컬**에서만 실행
        - ✅ 외부 서버로 데이터 전송 **없음**
        - ✅ 오픈소스 (Apache 2.0 라이선스)
        - ✅ API 키 불필요 (Yahoo Finance 공개 데이터 사용)

        ---

        **예시를 시도해보세요:**
        - 티커: `AAPL`, MA1: `10`, MA2: `21`, 기간: 최근 2년
        """)

        # Sample results
        st.markdown("### 📊 샘플 차트 (AAPL, 2022-2024)")
        st.image("https://via.placeholder.com/800x400.png?text=Sample+Chart", use_column_width=True)


if __name__ == "__main__":
    main()
