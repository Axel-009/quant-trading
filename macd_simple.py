#!/usr/bin/env python3
"""
MACD 백테스팅 - 초간단 버전 (백엔드 없음)
터미널에서 바로 실행 - GUI 필요 없음

실행: python macd_simple.py
"""

import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


def print_banner():
    """배너 출력"""
    print("\n" + "=" * 70)
    print(" " * 20 + "📈 MACD 백테스팅 (초간단 버전)")
    print("=" * 70)
    print("\n🔒 프라이버시: 100% 로컬 실행 - 결과 외부 전송 없음\n")


def get_input(prompt, default, input_type=str, validator=None):
    """안전한 입력 받기"""
    while True:
        try:
            user_input = input(f"{prompt} (기본값: {default}): ").strip()
            value = input_type(user_input) if user_input else default

            if validator and not validator(value):
                print(f"❌ 잘못된 입력입니다. 다시 시도하세요.")
                continue

            return value

        except ValueError:
            print(f"❌ {input_type.__name__} 형식으로 입력하세요.")
        except KeyboardInterrupt:
            print("\n\n취소되었습니다.")
            exit(0)


def macd_backtest():
    """MACD 백테스팅 메인 함수"""

    print_banner()

    # === 파라미터 입력 ===
    print("📊 파라미터 입력 (Enter만 누르면 기본값 사용)\n")

    ticker = get_input(
        "티커 심볼 (예: AAPL, NVDA)",
        "AAPL",
        str,
        lambda x: x.replace('.', '').replace('-', '').isalnum()
    ).upper()

    ma1 = get_input(
        "MA1 (단기 이동평균)",
        10,
        int,
        lambda x: 1 <= x <= 500
    )

    ma2 = get_input(
        "MA2 (장기 이동평균)",
        21,
        int,
        lambda x: ma1 < x <= 500
    )

    start_date = get_input(
        "시작 날짜 (YYYY-MM-DD)",
        (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d'),
        str
    )

    end_date = get_input(
        "종료 날짜 (YYYY-MM-DD)",
        datetime.now().strftime('%Y-%m-%d'),
        str
    )

    initial_capital = get_input(
        "초기 자본 ($)",
        20000,
        float,
        lambda x: x > 0
    )

    print("\n" + "=" * 70)
    print(f"\n📥 {ticker} 데이터 다운로드 중...\n")

    # === 데이터 다운로드 ===
    try:
        df = yf.download(ticker, start=start_date, end=end_date, progress=False)

        if df.empty:
            print(f"❌ 오류: '{ticker}'에 대한 데이터를 찾을 수 없습니다.")
            return

        print(f"✅ {len(df)}개 데이터 포인트 다운로드 완료!\n")

    except Exception as e:
        print(f"❌ 다운로드 오류: {e}")
        return

    # === MACD 계산 ===
    print("⚙️  MACD 전략 계산 중...\n")

    df['MA1'] = df['Close'].rolling(window=ma1, min_periods=1).mean()
    df['MA2'] = df['Close'].rolling(window=ma2, min_periods=1).mean()

    # 포지션 및 신호
    df['Position'] = 0
    df.loc[ma1:, 'Position'] = np.where(df['MA1'][ma1:] >= df['MA2'][ma1:], 1, 0)
    df['Signal'] = df['Position'].diff()
    df['Oscillator'] = df['MA1'] - df['MA2']

    # 수익률
    df['Returns'] = df['Close'].pct_change()
    df['Strategy_Returns'] = df['Position'].shift(1) * df['Returns']
    df['Cumulative_Returns'] = (1 + df['Returns']).cumprod()
    df['Cumulative_Strategy_Returns'] = (1 + df['Strategy_Returns']).cumprod()
    df['Portfolio_Value'] = initial_capital * df['Cumulative_Strategy_Returns']

    # === 성과 지표 계산 ===
    total_return = (df['Portfolio_Value'].iloc[-1] - initial_capital) / initial_capital * 100
    buy_hold_return = (df['Cumulative_Returns'].iloc[-1] - 1) * 100

    sharpe = (df['Strategy_Returns'].mean() / df['Strategy_Returns'].std()) * np.sqrt(252) \
        if df['Strategy_Returns'].std() != 0 else 0

    cumulative = df['Cumulative_Strategy_Returns']
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min() * 100

    winning_trades = (df['Strategy_Returns'] > 0).sum()
    total_trades = (df['Signal'] != 0).sum()
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    # === 결과 출력 ===
    print("=" * 70)
    print(f"{'📊 백테스팅 결과 - ' + ticker:^70}")
    print("=" * 70)

    print(f"\n{'지표':<25} {'값':>20} {'비교':>20}")
    print("-" * 70)
    print(f"{'🎯 총 수익률':<25} {total_return:>19.2f}%")
    print(f"{'📈 매수&보유 수익률':<25} {buy_hold_return:>19.2f}%")
    print(f"{'💰 초과 수익':<25} {total_return - buy_hold_return:>19.2f}%")
    print("-" * 70)
    print(f"{'📊 샤프 비율':<25} {sharpe:>20.2f} {'(>1 양호)':>20}")
    print(f"{'📉 최대 낙폭':<25} {max_drawdown:>19.2f}%")
    print(f"{'🎲 승률':<25} {win_rate:>19.1f}%")
    print("-" * 70)
    print(f"{'💵 초기 자본':<25} ${initial_capital:>19,.2f}")
    print(f"{'💵 최종 자산':<25} ${df['Portfolio_Value'].iloc[-1]:>19,.2f}")
    print(f"{'💵 손익':<25} ${df['Portfolio_Value'].iloc[-1] - initial_capital:>19,.2f}")
    print("-" * 70)
    print(f"{'🔄 총 거래 횟수':<25} {int(total_trades):>20} {'회':>20}")
    print("=" * 70)

    # === 차트 출력 여부 ===
    show_chart = input("\n\n📈 차트를 표시하시겠습니까? (y/n): ").lower()

    if show_chart == 'y':
        print("\n📊 차트 생성 중...\n")

        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

        # 1. 가격 & 신호
        ax1.plot(df.index, df['Close'], label=ticker, alpha=0.7, linewidth=2, color='#2E86AB')
        ax1.plot(df.index, df['MA1'], label=f'MA{ma1}', linewidth=1.5, color='#A23B72')
        ax1.plot(df.index, df['MA2'], label=f'MA{ma2}', linewidth=1.5, linestyle='--', color='#F18F01')

        buy_signals = df[df['Signal'] == 1]
        sell_signals = df[df['Signal'] == -1]

        ax1.scatter(buy_signals.index, buy_signals['Close'],
                   marker='^', color='green', s=100, label='매수', zorder=5)
        ax1.scatter(sell_signals.index, sell_signals['Close'],
                   marker='v', color='red', s=100, label='매도', zorder=5)

        ax1.set_ylabel('가격 ($)', fontsize=12, fontweight='bold')
        ax1.set_title(f'{ticker} MACD 백테스팅 ({start_date} ~ {end_date})',
                     fontsize=16, fontweight='bold', pad=20)
        ax1.legend(loc='upper left', framealpha=0.9)
        ax1.grid(True, alpha=0.3)

        # 2. MACD Oscillator
        colors = ['#E63946' if val < 0 else '#06A77D' for val in df['Oscillator']]
        ax2.bar(df.index, df['Oscillator'], color=colors, alpha=0.7, width=1)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax2.set_ylabel('MACD', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)

        # 3. 포트폴리오 가치
        ax3.plot(df.index, df['Portfolio_Value'],
                label='전략 포트폴리오', linewidth=2, color='#6A4C93')
        ax3.fill_between(df.index, df['Portfolio_Value'], initial_capital,
                        alpha=0.3, color='#6A4C93')
        ax3.axhline(y=initial_capital, color='gray', linestyle='--',
                   label=f'초기 자본 (${initial_capital:,})', linewidth=1.5)
        ax3.set_ylabel('포트폴리오 가치 ($)', fontsize=12, fontweight='bold')
        ax3.set_xlabel('날짜', fontsize=12, fontweight='bold')
        ax3.legend(loc='upper left', framealpha=0.9)
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

        # 저장 여부
        save_chart = input("\n💾 차트를 저장하시겠습니까? (y/n): ").lower()
        if save_chart == 'y':
            filename = f'preview/{ticker}_MACD_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            fig.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"✅ 차트 저장됨: {filename}")

    # === CSV 저장 ===
    save_csv = input("\n💾 결과를 CSV로 저장하시겠습니까? (y/n): ").lower()
    if save_csv == 'y':
        filename = f'data/{ticker}_backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        df.to_csv(filename)
        print(f"✅ 데이터 저장됨: {filename}")

    print("\n🎉 백테스팅 완료!\n")
    print("=" * 70)
    print("\n💡 다른 파라미터로 다시 시도하려면 스크립트를 다시 실행하세요.")
    print("   python macd_simple.py\n")


if __name__ == "__main__":
    try:
        macd_backtest()
    except KeyboardInterrupt:
        print("\n\n취소되었습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
