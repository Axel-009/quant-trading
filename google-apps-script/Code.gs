/**
 * MACD 백테스팅 - Google Apps Script 버전
 *
 * 📱 모바일에서도 사용 가능!
 * 🔒 Google 계정 내에서만 작동 - 안전함
 * 💰 완전 무료
 *
 * 설정 방법:
 * 1. Google Sheets 새 문서 생성
 * 2. 확장 프로그램 > Apps Script
 * 3. 이 코드를 붙여넣기
 * 4. 저장 후 실행
 */


// ==================== 설정 ====================

/**
 * 메뉴에 백테스팅 메뉴 추가
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('📈 백테스팅')
    .addItem('⚙️ 템플릿 생성', 'createTemplate')
    .addItem('🚀 백테스트 실행', 'runBacktest')
    .addItem('📊 차트 생성', 'createChart')
    .addItem('🗑️ 시트 초기화', 'clearResults')
    .addToUi();
}


/**
 * 템플릿 생성 - 처음 한 번만 실행
 */
function createTemplate() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();

  // 설정 시트
  let configSheet = ss.getSheetByName('설정');
  if (!configSheet) {
    configSheet = ss.insertSheet('설정');
  }

  configSheet.clear();
  configSheet.setTabColor('#4285F4');

  // 헤더 스타일
  const headerStyle = configSheet.getRange('A1:B1');
  headerStyle.setBackground('#4285F4')
             .setFontColor('#FFFFFF')
             .setFontWeight('bold')
             .setFontSize(12);

  // 파라미터 입력
  const config = [
    ['파라미터', '값'],
    ['티커 심볼', 'AAPL'],
    ['단기 이동평균 (MA1)', 10],
    ['장기 이동평균 (MA2)', 21],
    ['시작 날짜 (일 전)', 730],  // 2년
    ['초기 자본 ($)', 20000]
  ];

  configSheet.getRange(1, 1, config.length, 2).setValues(config);
  configSheet.getRange(2, 1, config.length - 1, 1).setFontWeight('bold');
  configSheet.getRange(2, 2, config.length - 1, 1).setNumberFormat('#,##0');
  configSheet.setColumnWidth(1, 200);
  configSheet.setColumnWidth(2, 150);

  // 안내 메시지
  configSheet.getRange('A8').setValue('💡 사용 방법:')
                            .setFontWeight('bold')
                            .setFontSize(11);
  configSheet.getRange('A9').setValue('1. 위 파라미터를 수정하세요');
  configSheet.getRange('A10').setValue('2. 메뉴 > 📈 백테스팅 > 🚀 백테스트 실행');
  configSheet.getRange('A11').setValue('3. 결과 시트에서 결과 확인');

  // 결과 시트
  let resultSheet = ss.getSheetByName('결과');
  if (!resultSheet) {
    resultSheet = ss.insertSheet('결과');
  }
  resultSheet.setTabColor('#34A853');

  // 데이터 시트
  let dataSheet = ss.getSheetByName('데이터');
  if (!dataSheet) {
    dataSheet = ss.insertSheet('데이터');
  }
  dataSheet.setTabColor('#FBBC04');

  SpreadsheetApp.getUi().alert('✅ 템플릿 생성 완료!\\n\\n설정 시트에서 파라미터를 수정한 후\\n"백테스트 실행"을 클릭하세요.');
}


// ==================== 데이터 다운로드 ====================

/**
 * Yahoo Finance에서 주가 데이터 가져오기
 * Google Finance 함수는 제한적이므로 API 사용
 */
function fetchStockData(ticker, daysAgo) {
  const endDate = new Date();
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - daysAgo);

  // Yahoo Finance API 사용 (무료)
  const url = `https://query1.finance.yahoo.com/v7/finance/download/${ticker}?period1=${Math.floor(startDate.getTime()/1000)}&period2=${Math.floor(endDate.getTime()/1000)}&interval=1d&events=history`;

  try {
    const response = UrlFetchApp.fetch(url);
    const csv = response.getContentText();
    const rows = Utilities.parseCsv(csv);

    // 헤더 제거하고 데이터만 반환
    const data = rows.slice(1).map(row => {
      return {
        date: new Date(row[0]),
        open: parseFloat(row[1]),
        high: parseFloat(row[2]),
        low: parseFloat(row[3]),
        close: parseFloat(row[4]),
        volume: parseFloat(row[6])
      };
    });

    return data.filter(d => !isNaN(d.close));

  } catch (error) {
    SpreadsheetApp.getUi().alert('❌ 데이터 다운로드 실패:\\n' + error.toString() +
                                  '\\n\\n대안: Google Finance 함수를 사용하세요.');
    return null;
  }
}


// ==================== MACD 계산 ====================

/**
 * 이동평균 계산
 */
function calculateMA(data, period) {
  const ma = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      ma.push(null);
    } else {
      const sum = data.slice(i - period + 1, i + 1).reduce((a, b) => a + b.close, 0);
      ma.push(sum / period);
    }
  }
  return ma;
}


/**
 * MACD 전략 백테스팅
 */
function runMACDBacktest(data, ma1Period, ma2Period, initialCapital) {
  // 이동평균 계산
  const ma1 = calculateMA(data, ma1Period);
  const ma2 = calculateMA(data, ma2Period);

  // 포지션 및 시그널
  const positions = [];
  const signals = [];

  for (let i = 0; i < data.length; i++) {
    if (i < ma1Period || ma1[i] === null || ma2[i] === null) {
      positions.push(0);
      signals.push(0);
    } else {
      const position = ma1[i] >= ma2[i] ? 1 : 0;
      positions.push(position);
      signals.push(i > 0 ? position - positions[i - 1] : 0);
    }
  }

  // 수익률 계산
  const returns = [0];  // 첫날은 0
  for (let i = 1; i < data.length; i++) {
    returns.push((data[i].close - data[i-1].close) / data[i-1].close);
  }

  // 전략 수익률
  const strategyReturns = [];
  for (let i = 0; i < data.length; i++) {
    const pos = i > 0 ? positions[i - 1] : 0;
    strategyReturns.push(pos * returns[i]);
  }

  // 누적 수익률
  let cumReturn = 1;
  let cumStrategyReturn = 1;
  const cumReturns = [];
  const cumStrategyReturns = [];

  for (let i = 0; i < data.length; i++) {
    cumReturn *= (1 + returns[i]);
    cumStrategyReturn *= (1 + strategyReturns[i]);
    cumReturns.push(cumReturn);
    cumStrategyReturns.push(cumStrategyReturn);
  }

  // 포트폴리오 가치
  const portfolioValue = cumStrategyReturns.map(r => initialCapital * r);

  // Oscillator
  const oscillator = [];
  for (let i = 0; i < data.length; i++) {
    if (ma1[i] !== null && ma2[i] !== null) {
      oscillator.push(ma1[i] - ma2[i]);
    } else {
      oscillator.push(null);
    }
  }

  return {
    data: data,
    ma1: ma1,
    ma2: ma2,
    positions: positions,
    signals: signals,
    returns: returns,
    strategyReturns: strategyReturns,
    cumReturns: cumReturns,
    cumStrategyReturns: cumStrategyReturns,
    portfolioValue: portfolioValue,
    oscillator: oscillator
  };
}


/**
 * 성과 지표 계산
 */
function calculateMetrics(result, initialCapital) {
  const finalValue = result.portfolioValue[result.portfolioValue.length - 1];
  const totalReturn = ((finalValue - initialCapital) / initialCapital) * 100;
  const buyHoldReturn = (result.cumReturns[result.cumReturns.length - 1] - 1) * 100;

  // 샤프 비율 (간단 버전)
  const strategyReturns = result.strategyReturns.filter((r, i) => i > 0);
  const avgReturn = strategyReturns.reduce((a, b) => a + b, 0) / strategyReturns.length;
  const stdReturn = Math.sqrt(strategyReturns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / strategyReturns.length);
  const sharpe = stdReturn > 0 ? (avgReturn / stdReturn) * Math.sqrt(252) : 0;

  // 최대 낙폭
  let maxDrawdown = 0;
  let peak = result.cumStrategyReturns[0];
  for (let i = 1; i < result.cumStrategyReturns.length; i++) {
    if (result.cumStrategyReturns[i] > peak) {
      peak = result.cumStrategyReturns[i];
    }
    const drawdown = (result.cumStrategyReturns[i] - peak) / peak;
    if (drawdown < maxDrawdown) {
      maxDrawdown = drawdown;
    }
  }
  maxDrawdown *= 100;

  // 승률
  const winningTrades = strategyReturns.filter(r => r > 0).length;
  const totalTrades = result.signals.filter(s => s !== 0).length;
  const winRate = totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0;

  return {
    totalReturn: totalReturn,
    buyHoldReturn: buyHoldReturn,
    excessReturn: totalReturn - buyHoldReturn,
    sharpe: sharpe,
    maxDrawdown: maxDrawdown,
    winRate: winRate,
    totalTrades: totalTrades,
    initialCapital: initialCapital,
    finalValue: finalValue,
    profit: finalValue - initialCapital
  };
}


// ==================== 메인 실행 ====================

/**
 * 백테스트 실행
 */
function runBacktest() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const ui = SpreadsheetApp.getUi();

  // 설정 읽기
  const configSheet = ss.getSheetByName('설정');
  if (!configSheet) {
    ui.alert('❌ 오류: 먼저 "템플릿 생성"을 실행하세요.');
    return;
  }

  const ticker = configSheet.getRange('B2').getValue().toString().toUpperCase();
  const ma1 = parseInt(configSheet.getRange('B3').getValue());
  const ma2 = parseInt(configSheet.getRange('B4').getValue());
  const daysAgo = parseInt(configSheet.getRange('B5').getValue());
  const initialCapital = parseFloat(configSheet.getRange('B6').getValue());

  // 검증
  if (!ticker || ma1 >= ma2) {
    ui.alert('❌ 오류: 파라미터를 확인하세요.\\nMA1은 MA2보다 작아야 합니다.');
    return;
  }

  ui.alert('📥 데이터 다운로드 중...\\n잠시만 기다려주세요.');

  // 데이터 다운로드
  const data = fetchStockData(ticker, daysAgo);
  if (!data || data.length === 0) {
    ui.alert('❌ 데이터를 가져올 수 없습니다.\\n\\n대안:\\n1. Google Finance 함수 사용\\n2. 수동으로 데이터 입력');
    return;
  }

  // 백테스팅 실행
  const result = runMACDBacktest(data, ma1, ma2, initialCapital);
  const metrics = calculateMetrics(result, initialCapital);

  // 결과 시트에 출력
  outputResults(ss, result, metrics, ticker, ma1, ma2);

  // 데이터 시트에 상세 데이터 출력
  outputData(ss, result);

  // 완료 메시지
  const message = `✅ 백테스팅 완료!\\n\\n` +
                  `📊 ${ticker}\\n` +
                  `📈 총 수익률: ${metrics.totalReturn.toFixed(2)}%\\n` +
                  `💰 최종 자산: $${metrics.finalValue.toLocaleString('en-US', {maximumFractionDigits: 2})}\\n\\n` +
                  `"결과" 시트를 확인하세요.`;

  ui.alert(message);

  // 결과 시트로 이동
  ss.setActiveSheet(ss.getSheetByName('결과'));
}


/**
 * 결과 출력
 */
function outputResults(ss, result, metrics, ticker, ma1, ma2) {
  let resultSheet = ss.getSheetByName('결과');
  resultSheet.clear();

  // 제목
  resultSheet.getRange('A1').setValue(`📊 ${ticker} MACD 백테스팅 결과`)
                            .setFontSize(16)
                            .setFontWeight('bold');

  resultSheet.getRange('A2').setValue(`MA${ma1} / MA${ma2}`)
                            .setFontSize(10)
                            .setFontColor('#666666');

  // 성과 지표
  const metricsData = [
    ['', ''],
    ['지표', '값'],
    ['🎯 총 수익률', `${metrics.totalReturn.toFixed(2)}%`],
    ['📈 매수&보유 수익률', `${metrics.buyHoldReturn.toFixed(2)}%`],
    ['💰 초과 수익', `${metrics.excessReturn.toFixed(2)}%`],
    ['', ''],
    ['📊 샤프 비율', metrics.sharpe.toFixed(2)],
    ['📉 최대 낙폭', `${metrics.maxDrawdown.toFixed(2)}%`],
    ['🎲 승률', `${metrics.winRate.toFixed(1)}%`],
    ['🔄 총 거래 횟수', `${metrics.totalTrades}회`],
    ['', ''],
    ['💵 초기 자본', `$${metrics.initialCapital.toLocaleString('en-US')}`],
    ['💵 최종 자산', `$${metrics.finalValue.toLocaleString('en-US', {maximumFractionDigits: 2})}`],
    ['💵 손익', `$${metrics.profit.toLocaleString('en-US', {maximumFractionDigits: 2})}`]
  ];

  resultSheet.getRange(4, 1, metricsData.length, 2).setValues(metricsData);

  // 헤더 스타일
  resultSheet.getRange('A5:B5').setBackground('#34A853')
                               .setFontColor('#FFFFFF')
                               .setFontWeight('bold');

  // 수익률에 조건부 서식
  const returnCell = resultSheet.getRange('B6');
  if (metrics.totalReturn > 0) {
    returnCell.setFontColor('#0F9D58').setFontWeight('bold');
  } else {
    returnCell.setFontColor('#DB4437').setFontWeight('bold');
  }

  // 열 너비 조정
  resultSheet.setColumnWidth(1, 180);
  resultSheet.setColumnWidth(2, 150);

  // 안내 메시지
  resultSheet.getRange('A20').setValue('💡 차트를 생성하려면:')
                             .setFontWeight('bold');
  resultSheet.getRange('A21').setValue('메뉴 > 📈 백테스팅 > 📊 차트 생성');

  resultSheet.getRange('A23').setValue('📱 모바일에서 사용:')
                             .setFontWeight('bold');
  resultSheet.getRange('A24').setValue('Google Sheets 앱에서 이 파일을 열면');
  resultSheet.getRange('A25').setValue('언제 어디서나 결과를 확인할 수 있습니다!');
}


/**
 * 데이터 시트에 상세 출력
 */
function outputData(ss, result) {
  let dataSheet = ss.getSheetByName('데이터');
  dataSheet.clear();

  // 헤더
  const headers = ['날짜', '종가', 'MA1', 'MA2', 'Oscillator', '포지션', '시그널', '포트폴리오'];
  dataSheet.getRange(1, 1, 1, headers.length).setValues([headers])
           .setBackground('#FBBC04')
           .setFontColor('#FFFFFF')
           .setFontWeight('bold');

  // 데이터
  const rows = [];
  for (let i = 0; i < result.data.length; i++) {
    rows.push([
      result.data[i].date,
      result.data[i].close,
      result.ma1[i],
      result.ma2[i],
      result.oscillator[i],
      result.positions[i],
      result.signals[i],
      result.portfolioValue[i]
    ]);
  }

  dataSheet.getRange(2, 1, rows.length, headers.length).setValues(rows);

  // 숫자 포맷
  dataSheet.getRange(2, 2, rows.length, 7).setNumberFormat('#,##0.00');

  // 열 너비
  dataSheet.setColumnWidth(1, 100);
  for (let i = 2; i <= headers.length; i++) {
    dataSheet.setColumnWidth(i, 90);
  }

  // 고정 행
  dataSheet.setFrozenRows(1);
}


/**
 * 차트 생성
 */
function createChart() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dataSheet = ss.getSheetByName('데이터');
  const resultSheet = ss.getSheetByName('결과');

  if (!dataSheet || dataSheet.getLastRow() < 2) {
    SpreadsheetApp.getUi().alert('❌ 먼저 백테스트를 실행하세요.');
    return;
  }

  // 기존 차트 삭제
  const charts = resultSheet.getCharts();
  charts.forEach(chart => resultSheet.removeChart(chart));

  const lastRow = dataSheet.getLastRow();

  // 차트 1: 가격 & 이동평균
  const priceChart = dataSheet.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(dataSheet.getRange('A1:A' + lastRow))  // 날짜
    .addRange(dataSheet.getRange('B1:D' + lastRow))  // 종가, MA1, MA2
    .setPosition(5, 4, 0, 0)
    .setOption('title', '가격 & 이동평균')
    .setOption('width', 600)
    .setOption('height', 300)
    .setOption('legend', {position: 'bottom'})
    .setOption('series', {
      0: {color: '#4285F4'},
      1: {color: '#DB4437'},
      2: {color: '#F4B400'}
    })
    .build();

  resultSheet.insertChart(priceChart);

  // 차트 2: 포트폴리오 가치
  const portfolioChart = dataSheet.newChart()
    .setChartType(Charts.ChartType.AREA)
    .addRange(dataSheet.getRange('A1:A' + lastRow))
    .addRange(dataSheet.getRange('H1:H' + lastRow))
    .setPosition(20, 4, 0, 0)
    .setOption('title', '포트폴리오 가치')
    .setOption('width', 600)
    .setOption('height', 300)
    .setOption('legend', {position: 'none'})
    .setOption('series', {
      0: {color: '#0F9D58', areaOpacity: 0.3}
    })
    .build();

  resultSheet.insertChart(portfolioChart);

  SpreadsheetApp.getUi().alert('✅ 차트 생성 완료!');
}


/**
 * 결과 초기화
 */
function clearResults() {
  const ui = SpreadsheetApp.getUi();
  const response = ui.alert('결과를 초기화하시겠습니까?', ui.ButtonSet.YES_NO);

  if (response === ui.Button.YES) {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const resultSheet = ss.getSheetByName('결과');
    const dataSheet = ss.getSheetByName('데이터');

    if (resultSheet) resultSheet.clear();
    if (dataSheet) dataSheet.clear();

    ui.alert('✅ 초기화 완료!');
  }
}
