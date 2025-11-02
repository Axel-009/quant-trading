"""
Quant Trading - Gradio 버전 (초간단!)
개인용 백테스팅 웹 인터페이스 - Streamlit보다 더 간단

실행: python app_gradio.py
"""

import gradio as gr
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta


def macd_backtest(ticker, ma1, ma2, start_date, end_date, initial_capital):
    """
    MACD 백테스팅 실행

    Returns:
        tuple: (metrics_html, plotly_figure)
    """
    try:
        # 입력 검증
        ticker = ticker.upper().strip()
        ma1 = int(ma1)
        ma2 = int(ma2)
        initial_capital = float(initial_capital)

        if ma1 >= ma2:
            return "❌ 오류: MA1은 MA2보다 작아야 합니다.", None

        # 데이터 다운로드
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)

        if df.empty:
            return f"❌ 오류: '{ticker}'에 대한 데이터를 찾을 수 없습니다.", None

        # MACD 계산
        df['MA1'] = df['Close'].rolling(window=ma1, min_periods=1).mean()
        df['MA2'] = df['Close'].rolling(window=ma2, min_periods=1).mean()

        # 포지션 및 신호
        df['Position'] = 0
        df.loc[ma1:, 'Position'] = np.where(df['MA1'][ma1:] >= df['MA2'][ma1:], 1, 0)
        df['Signal'] = df['Position'].diff()
        df['Oscillator'] = df['MA1'] - df['MA2']

        # 수익률 계산
        df['Returns'] = df['Close'].pct_change()
        df['Strategy_Returns'] = df['Position'].shift(1) * df['Returns']
        df['Cumulative_Returns'] = (1 + df['Returns']).cumprod()
        df['Cumulative_Strategy_Returns'] = (1 + df['Strategy_Returns']).cumprod()
        df['Portfolio_Value'] = initial_capital * df['Cumulative_Strategy_Returns']

        # 성과 지표 계산
        total_return = (df['Portfolio_Value'].iloc[-1] - initial_capital) / initial_capital * 100
        buy_hold_return = (df['Cumulative_Returns'].iloc[-1] - 1) * 100

        sharpe = (df['Strategy_Returns'].mean() / df['Strategy_Returns'].std()) * np.sqrt(252) if df['Strategy_Returns'].std() != 0 else 0

        cumulative = df['Cumulative_Strategy_Returns']
        running_max = cumulative.cummax()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min() * 100

        winning_trades = (df['Strategy_Returns'] > 0).sum()
        total_trades = (df['Signal'] != 0).sum()
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # 결과 HTML 생성
        metrics_html = f"""
        <div style="font-family: Arial; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white;">
            <h2 style="text-align: center; margin-bottom: 20px;">📊 백테스팅 결과 - {ticker}</h2>

            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px;">
                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                    <div style="font-size: 14px; opacity: 0.8;">총 수익률</div>
                    <div style="font-size: 28px; font-weight: bold;">{total_return:.2f}%</div>
                </div>

                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                    <div style="font-size: 14px; opacity: 0.8;">매수&보유</div>
                    <div style="font-size: 28px; font-weight: bold;">{buy_hold_return:.2f}%</div>
                </div>

                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                    <div style="font-size: 14px; opacity: 0.8;">샤프 비율</div>
                    <div style="font-size: 28px; font-weight: bold;">{sharpe:.2f}</div>
                </div>

                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                    <div style="font-size: 14px; opacity: 0.8;">최대 낙폭</div>
                    <div style="font-size: 28px; font-weight: bold;">{max_drawdown:.2f}%</div>
                </div>

                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                    <div style="font-size: 14px; opacity: 0.8;">승률</div>
                    <div style="font-size: 28px; font-weight: bold;">{win_rate:.1f}%</div>
                </div>

                <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                    <div style="font-size: 14px; opacity: 0.8;">거래 횟수</div>
                    <div style="font-size: 28px; font-weight: bold;">{int(total_trades)}</div>
                </div>
            </div>

            <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px;">
                <div style="font-size: 14px; opacity: 0.8;">최종 자산</div>
                <div style="font-size: 32px; font-weight: bold;">${df['Portfolio_Value'].iloc[-1]:,.2f}</div>
                <div style="font-size: 14px; opacity: 0.8;">손익: ${df['Portfolio_Value'].iloc[-1] - initial_capital:,.2f}</div>
            </div>
        </div>
        """

        # 차트 생성
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.5, 0.25, 0.25],
            subplot_titles=(f'{ticker} - 가격 & 신호', 'MACD Oscillator', '포트폴리오 가치')
        )

        # 캔들스틱
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='가격'
            ),
            row=1, col=1
        )

        # 이동평균
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MA1'], mode='lines', name=f'MA{ma1}',
                      line=dict(color='blue', width=1)),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(x=df.index, y=df['MA2'], mode='lines', name=f'MA{ma2}',
                      line=dict(color='orange', width=1, dash='dot')),
            row=1, col=1
        )

        # 매수/매도 신호
        buy_signals = df[df['Signal'] == 1]
        sell_signals = df[df['Signal'] == -1]

        fig.add_trace(
            go.Scatter(
                x=buy_signals.index, y=buy_signals['Close'],
                mode='markers', name='매수',
                marker=dict(symbol='triangle-up', size=10, color='green')
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=sell_signals.index, y=sell_signals['Close'],
                mode='markers', name='매도',
                marker=dict(symbol='triangle-down', size=10, color='red')
            ),
            row=1, col=1
        )

        # Oscillator
        colors = ['red' if val < 0 else 'green' for val in df['Oscillator']]
        fig.add_trace(
            go.Bar(x=df.index, y=df['Oscillator'], name='MACD', marker_color=colors),
            row=2, col=1
        )

        # 포트폴리오
        fig.add_trace(
            go.Scatter(
                x=df.index, y=df['Portfolio_Value'],
                mode='lines', name='포트폴리오',
                line=dict(color='purple', width=2),
                fill='tozeroy'
            ),
            row=3, col=1
        )

        fig.update_layout(
            height=800,
            showlegend=True,
            xaxis_rangeslider_visible=False,
            hovermode='x unified'
        )

        fig.update_yaxes(title_text="가격 ($)", row=1, col=1)
        fig.update_yaxes(title_text="Oscillator", row=2, col=1)
        fig.update_yaxes(title_text="포트폴리오 ($)", row=3, col=1)

        return metrics_html, fig

    except Exception as e:
        error_msg = f"❌ 오류 발생: {str(e)}"
        return error_msg, None


# Gradio 인터페이스
with gr.Blocks(title="📈 Quant Trading Backtester", theme=gr.themes.Soft()) as demo:

    gr.Markdown("""
    # 📈 Quant Trading Backtester

    **개인용 백테스팅 도구** - 간단하고 빠르게!

    ## 🚀 사용 방법:
    1. 아래 파라미터 입력
    2. "백테스트 실행" 버튼 클릭
    3. 결과 확인

    **🔒 100% 로컬 실행** - 데이터 외부 전송 없음
    """)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ 파라미터 설정")

            ticker_input = gr.Textbox(
                label="티커 심볼",
                value="AAPL",
                placeholder="예: AAPL, NVDA, TSLA"
            )

            with gr.Row():
                ma1_input = gr.Number(
                    label="MA1 (단기)",
                    value=10,
                    minimum=1,
                    maximum=500
                )
                ma2_input = gr.Number(
                    label="MA2 (장기)",
                    value=21,
                    minimum=1,
                    maximum=500
                )

            start_date_input = gr.Textbox(
                label="시작 날짜",
                value=(datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d'),
                placeholder="YYYY-MM-DD"
            )

            end_date_input = gr.Textbox(
                label="종료 날짜",
                value=datetime.now().strftime('%Y-%m-%d'),
                placeholder="YYYY-MM-DD"
            )

            capital_input = gr.Number(
                label="초기 자본 ($)",
                value=20000,
                minimum=1000
            )

            run_btn = gr.Button("🚀 백테스트 실행", variant="primary", size="lg")

            gr.Markdown("""
            ---
            ### 💡 TIP
            - **MA1 < MA2**: 단기 이동평균이 장기보다 작아야 합니다
            - **권장 조합**: MA10/MA21, MA12/MA26
            - **기간**: 최소 1년 이상 권장

            ### 🔒 프라이버시
            - ✅ 로컬에서만 실행
            - ✅ 결과 외부 전송 없음
            - ✅ Yahoo Finance 공개 데이터 사용
            """)

        with gr.Column(scale=2):
            gr.Markdown("### 📊 백테스팅 결과")

            metrics_output = gr.HTML(
                value="<div style='text-align: center; padding: 50px; color: #666;'>파라미터를 입력하고 '백테스트 실행'을 클릭하세요</div>"
            )

            chart_output = gr.Plot()

    # 이벤트 연결
    run_btn.click(
        fn=macd_backtest,
        inputs=[ticker_input, ma1_input, ma2_input, start_date_input, end_date_input, capital_input],
        outputs=[metrics_output, chart_output]
    )

    gr.Markdown("""
    ---

    ## 📚 지원 전략

    현재: **MACD Oscillator** (이동평균 수렴/발산)

    준비 중: Pair Trading, Bollinger Bands, RSI Pattern

    ---

    **면책 조항**: 교육 목적으로만 사용하세요. 실제 거래 손실에 대해 책임지지 않습니다.
    """)


# 실행
if __name__ == "__main__":
    print("=" * 60)
    print("📈 Quant Trading Backtester (Gradio)")
    print("=" * 60)
    print("\n🚀 서버 시작 중...")
    print("\n🔒 보안 안내:")
    print("   - 모든 계산은 로컬에서만 실행됩니다")
    print("   - 백테스팅 결과는 외부로 전송되지 않습니다")
    print("   - Yahoo Finance 공개 데이터만 사용합니다")
    print("\n" + "=" * 60 + "\n")

    demo.launch(
        server_name="127.0.0.1",  # 로컬만 접속 가능
        server_port=7860,
        share=False,  # 외부 공유 차단
        show_error=True
    )
