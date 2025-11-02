# 🚀 Quant Trading 설정 가이드

## 📋 목차

1. [빠른 시작](#빠른-시작)
2. [상세 설치 가이드](#상세-설치-가이드)
3. [웹앱 실행](#웹앱-실행)
4. [기존 스크립트 실행](#기존-스크립트-실행)
5. [보안 및 프라이버시](#보안-및-프라이버시)
6. [문제 해결](#문제-해결)

---

## 🎯 빠른 시작

### 1단계: 의존성 설치

```bash
# Python 3.8 이상 필요
python --version

# 필수 패키지 설치
pip install -r requirements.txt
```

### 2단계: 웹앱 실행 (권장)

```bash
# Streamlit 웹앱 실행
streamlit run app.py
```

브라우저가 자동으로 열리고 `http://localhost:8501`에서 앱이 실행됩니다.

### 3단계: 백테스팅 시작

1. 왼쪽 사이드바에서 파라미터 입력
2. "백테스트 실행" 버튼 클릭
3. 결과 확인!

---

## 📦 상세 설치 가이드

### 1. Python 환경 설정

#### Option A: 가상 환경 사용 (권장)

```bash
# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate
```

#### Option B: Conda 사용

```bash
# Conda 환경 생성
conda create -n quant-trading python=3.9

# 환경 활성화
conda activate quant-trading
```

### 2. 패키지 설치

```bash
# 필수 패키지
pip install pandas numpy matplotlib scipy yfinance statsmodels cvxopt python-dateutil

# 웹앱 패키지
pip install streamlit plotly flask flask-cors

# 개발 도구 (선택사항)
pip install pytest black flake8

# 또는 한 번에:
pip install -r requirements.txt
```

### 3. 환경 변수 설정 (선택사항)

```bash
# .env.example을 .env로 복사
cp .env.example .env

# .env 파일 편집 (선택사항)
# 기본 설정으로도 충분히 작동합니다
```

---

## 🌐 웹앱 실행

### Streamlit 웹앱 (가장 쉬움)

```bash
# 기본 실행
streamlit run app.py

# 포트 지정
streamlit run app.py --server.port 8080

# 외부 접속 허용 (주의: 로컬 네트워크만)
streamlit run app.py --server.address 0.0.0.0
```

### 기능:

- ✅ 대화형 파라미터 입력
- ✅ 실시간 차트 시각화
- ✅ 성과 지표 계산
- ✅ 거래 내역 표시
- ✅ 모바일 반응형 디자인

---

## 💻 기존 스크립트 실행

### MACD Oscillator 예시

```bash
python "MACD Oscillator backtest.py"
```

**대화형 입력:**

```
=== MACD Oscillator 백테스팅 ===

ma1 (단기 이동평균, 권장: 10): 10
ma2 (장기 이동평균, 권장: 21): 21
시작 날짜 (YYYY-MM-DD): 2020-01-01
종료 날짜 (YYYY-MM-DD): 2023-12-31
티커 심볼: AAPL
슬라이싱 (차트 표시할 데이터 시작점): 0

데이터 다운로드 중: AAPL (2020-01-01 ~ 2023-12-31)...
✓ 1006개의 데이터 포인트 다운로드 완료

백테스팅 완료!
```

### 개선사항:

- ✅ 입력 검증 (잘못된 값 자동 차단)
- ✅ 명확한 한글 안내 메시지
- ✅ 에러 처리 개선
- ✅ 하드코딩된 경로 제거

### 다른 전략:

```bash
# Pair Trading
python "Pair trading backtest.py"

# Bollinger Bands
python "Bollinger Bands Pattern Recognition backtest.py"

# RSI Pattern
python "RSI Pattern Recognition backtest.py"
```

---

## 🔒 보안 및 프라이버시

### ✅ 안전한 부분:

1. **100% 로컬 실행**
   - 모든 백테스팅은 사용자 컴퓨터에서만 실행
   - 결과가 외부로 전송되지 않음

2. **최소한의 외부 통신**
   - Yahoo Finance에서 **공개 시장 데이터**만 다운로드
   - 전송 정보: 티커 심볼 (예: AAPL), 날짜 범위
   - 전송되지 않는 정보: 백테스팅 결과, 거래 전략, 개인 데이터

3. **API 키 불필요**
   - 기본 기능은 API 키 없이 작동
   - Yahoo Finance는 무료 공개 API 사용

4. **오픈소스**
   - Apache 2.0 라이선스
   - 코드 검증 가능

### ⚠️ 주의사항:

1. **하드코딩된 경로**
   - 기존 코드: `os.chdir('K:/ecole/...')` 같은 경로는 로컬에만 존재
   - 새 코드: `config.py`로 자동 경로 설정
   - **외부로 전송되지 않음** - 단지 로컬 파일 읽기용

2. **GitHub 공유 시**
   - `.env` 파일은 절대 커밋하지 마세요
   - `.gitignore`에 이미 추가됨

3. **웹앱 배포 시**
   - 외부 서버에 배포하지 마세요 (개인 사용 권장)
   - 배포 시 인증 및 HTTPS 필수

---

## 🛠️ 문제 해결

### 1. `ModuleNotFoundError: No module named 'yfinance'`

```bash
pip install yfinance
```

### 2. `fix_yahoo_finance` 관련 오류

```bash
# fix_yahoo_finance는 더 이상 사용되지 않음
# yfinance로 교체됨
pip install yfinance --upgrade
```

### 3. `cvxopt` 설치 실패 (Windows)

```bash
# Microsoft C++ Build Tools 설치 필요
# https://visualstudio.microsoft.com/visual-cpp-build-tools/

# 또는 conda 사용:
conda install -c conda-forge cvxopt
```

### 4. 데이터 다운로드 실패

```bash
# Yahoo Finance 서버 문제일 수 있음
# 잠시 후 다시 시도하거나 다른 티커 사용
```

### 5. `config.py` 또는 `validators.py` 없음

```bash
# 프로젝트 루트 디렉토리에서 실행 확인
cd /path/to/quant-trading

# 파일 존재 확인
ls config.py validators.py
```

### 6. Streamlit 포트 충돌

```bash
# 다른 포트 사용
streamlit run app.py --server.port 8502
```

---

## 📊 권장 워크플로우

### 초보자:

1. Streamlit 웹앱 사용 (`streamlit run app.py`)
2. 기본 파라미터로 실험
3. 다양한 티커와 날짜 범위 테스트

### 중급자:

1. 기존 Python 스크립트 직접 실행
2. 파라미터 최적화
3. `config.py`에서 상수 조정

### 고급자:

1. 새로운 전략 구현
2. `validators.py`를 사용한 입력 검증
3. 웹앱에 새 전략 추가

---

## 📁 프로젝트 구조

```
quant-trading/
├── app.py                          # Streamlit 웹앱
├── config.py                       # 설정 및 경로 관리
├── validators.py                   # 입력 검증 유틸리티
├── requirements.txt                # 의존성 목록
├── .env.example                    # 환경 변수 예시
├── .gitignore                      # Git 무시 파일
├── SETUP_GUIDE.md                  # 이 문서
├── README.md                       # 프로젝트 설명
│
├── MACD Oscillator backtest.py     # MACD 전략
├── Pair trading backtest.py        # 페어 트레이딩
├── Bollinger Bands *.py            # 볼린저 밴드
├── ... (기타 전략)
│
├── data/                           # 데이터 파일 (생성됨)
├── preview/                        # 차트 출력 (생성됨)
│
├── Smart Farmers project/          # Smart Farmers 프로젝트
├── Oil Money project/              # Oil Money 프로젝트
├── Monte Carlo project/            # Monte Carlo 프로젝트
└── Ore Money project/              # Ore Money 프로젝트
```

---

## 🎓 다음 단계

1. ✅ 웹앱으로 첫 백테스트 실행
2. 📚 README.md에서 전략 이론 학습
3. 🔧 파라미터 최적화 실험
4. 💡 자신만의 전략 개발
5. 🚀 실전 트레이딩 전 충분한 검증

---

## 💬 지원

- **GitHub Issues**: 버그 리포트 및 기능 요청
- **코드 리뷰**: 오픈소스 기여 환영
- **문서**: README.md 참조

---

**면책 조항**: 이 소프트웨어는 교육 목적으로만 제공됩니다. 실제 거래에서 발생하는 손실에 대해 책임지지 않습니다. 투자는 본인의 판단과 책임 하에 하시기 바랍니다.
