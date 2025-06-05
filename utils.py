import platform
import matplotlib.pyplot as plt
from deep_translator import GoogleTranslator
import requests
from bs4 import BeautifulSoup
import os

# --- 한글 폰트 설정 ---
def set_korean_font():
    """운영체제에 따라 Matplotlib 한글 폰트를 설정합니다."""
    if platform.system() == "Darwin":  # macOS
        plt.rcParams['font.family'] = 'AppleGothic'
    elif platform.system() == "Windows":
        plt.rcParams['font.family'] = 'Malgun Gothic'
    else:  # Linux
        # 나눔 고딕 폰트가 설치되어 있다고 가정합니다.
        # 설치되어 있지 않다면, 시스템에 맞는 폰트 설정이 필요합니다.
        plt.rcParams['font.family'] = 'NanumGothic'
    plt.rcParams['axes.unicode_minus'] = False

def translate_to_korean(text: str) -> str:
    """영문 텍스트를 한글로 번역합니다. 번역 실패 시 오류 메시지를 반환합니다."""
    try:
        return GoogleTranslator(source='auto', target='ko').translate(text)
    except Exception as e:
        return f"(❌ 번역 실패: {e}) " + text
    
def get_today_usd_to_krw_rate() -> float:
    api_key = os.getenv("ALPHA_API_KEY")
    try:
        url = f"https://www.alphavantage.co/query?function=CURRENCY_EXCHANGE_RATE&from_currency=USD&to_currency=KRW&apikey={api_key}"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        rate = float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
        return rate
    except Exception as e:
        print(f"AlphaVantage 환율 정보를 가져오는 데 실패했습니다: {e}")
        return 1350.0

def format_currency(amount: float, currency: str = "USD", rate: float | None = None) -> str:
    """
    금액을 읽기 쉬운 형식으로 포맷팅하고, USD의 경우 한화(KRW)로 병기합니다.
    '조', '억', '천만', '백만', '원' 단위로 표시합니다.
    """
    if amount is None or amount == 0:
        return "-"

    def classify_unit(value: float) -> tuple[str, float]:
        if value >= 1_000_000_000_000:
            return "조", value / 1_000_000_000_000
        if value >= 100_000_000:
            return "억", value / 100_000_000
        elif value >= 10_000_000:
            return "천만", value / 10_000_000
        elif value >= 1_000_000:
            return "백만", value / 1_000_000
        else:
            return "원", value

    if currency == "USD":
        if rate is None:
            rate = get_today_usd_to_krw_rate() # 함수 호출로 변경
        
        usd_unit, usd_value = classify_unit(amount)
        # USD 단위는 '달러'로 표기하는 것이 자연스러움
        usd_unit_str = ""
        if usd_unit == "조":
            usd_unit_str = "조 달러"
        elif usd_unit == "억":
            usd_unit_str = "억 달러"
        elif usd_unit == "천만":
            usd_unit_str = "천만 달러"
        elif usd_unit == "백만":
            usd_unit_str = "백만 달러"
        elif usd_unit == "원": # 1백만 달러 미만의 경우
            usd_unit_str = "달러"

        krw_total = amount * rate
        krw_unit, krw_value = classify_unit(krw_total)

        usd_fmt = f"${usd_value:,.2f}{usd_unit_str}"
        krw_fmt = f"₩ {krw_value:,.2f}{krw_unit}"
        return f"{usd_fmt} ({krw_fmt})"

    elif currency == "KRW":
        unit, value = classify_unit(amount)
        return f"₩ {value:,.2f}{unit}"

    else:
        return f"{amount:,.2f} {currency}" # 지원되지 않는 통화도 일단 표시

def usd_with_krw_eok(usd: float) -> str:
    """USD 금액을 원화 '억' 단위로 함께 표시합니다."""
    if not usd:
        return "-"
    rate = get_today_usd_to_krw_rate()
    usd_fmt = f"{usd:,.2f}"
    krw = usd * rate
    eok = krw / 100_000_000
    krw_fmt = f"{eok:,.2f}"
    return f"{usd_fmt} ({krw_fmt} 억 원)"