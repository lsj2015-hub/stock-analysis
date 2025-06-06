import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

# 로컬 모듈 임포트
from utils import set_korean_font, translate_to_korean, get_today_usd_to_krw_rate, format_currency
from data_manager import YahooFinanceDataManager
from llm_service import OpenAIService

# Streamlit 페이지 설정
st.set_page_config(
    page_title="기업 정보 요약",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("📊 범주별 기업 정보 조회")

# 데이터 및 AI 서비스 객체 초기화
data_manager = YahooFinanceDataManager()
try:
    ai_service = OpenAIService()
except ValueError as e:
    st.error(f"AI 서비스 초기화 오류: {e}. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
    ai_service = None # 오류 발생 시 AI 서비스 사용 불가

symbol = st.text_input("🔍 종목 코드 (예: AAPL)", value="AAPL").strip().upper()

# --- 범주별 버튼 조회 기능 ---

if st.button("🏢 회사 기본 정보"):
    info = data_manager.get_info(symbol)
    if not info:
        st.error(f"'{symbol}'에 대한 데이터를 불러올 수 없습니다. 종목 코드를 확인해주세요.")
    else:
        summary_en = info.get('longBusinessSummary', '')
        summary_ko = translate_to_korean(summary_en)

        st.subheader(f"{info.get('longName', '기업명 없음')} ({symbol})")
        employees = info.get('fullTimeEmployees', None)
        employees_str = f"{employees:,}명" if isinstance(employees, int) else "정보 없음"

        st.markdown(f"""
        - **산업군**: {info.get('industry', '정보 없음')}
        - **섹터**: {info.get('sector', '정보 없음')}
        - **설명 (한글 번역)**: {summary_ko}
        - **주소**: {info.get('address1', '')}, {info.get('city', '')}, {info.get('state', '')} {info.get('zip', '')}, {info.get('country', '')}
        - **웹사이트**: [{info.get('website', '')}]({info.get('website', '')})
        - **직원 수**: {employees_str}
        """)


if st.button("💰 재무 요약"):
    info = data_manager.get_info(symbol)
    rate = get_today_usd_to_krw_rate()

    if not info:
        st.error(f"'{symbol}'에 대한 데이터를 불러올 수 없습니다. 종목 코드를 확인해주세요.")
    else:
        st.subheader("💰 재무 요약")
        st.markdown(f"""
        - **총수익**: {format_currency(info.get('totalRevenue'), "USD", rate)}
        - **순이익**: {format_currency(info.get('netIncomeToCommon'), "USD", rate)}
        - **영업이익률**: {info.get('operatingMargins', 0) * 100:.2f}%
        - **배당률**: {info.get('dividendYield', 0) * 100:.2f}%
        - **EPS**: {info.get('trailingEps', 0):.2f}
        - **현금 보유**: {format_currency(info.get('totalCash'), "USD", rate)}
        - **총 부채**: {format_currency(info.get('totalDebt'), "USD", rate)}
        - **부채비율**: {info.get('debtToEquity', 0):.2f}%
        """)

# 임원 요약 버튼 클릭 시
if st.button("🧑‍💼 임원 요약"):
    info = data_manager.get_info(symbol)
    officers = info.get("companyOfficers", []) if info else []
    if not officers:
        st.warning("임원 정보가 없습니다.")
    else:
        # 상위 5명만 표시
        top_officers = sorted(officers, key=lambda x: x.get('totalPay', 0), reverse=True)[:5]
        data = []
        for officer in top_officers:
            name = officer.get("name", "")
            title = officer.get("title", "")
            pay = officer.get("totalPay", 0)
            formatted_pay = format_currency(pay, currency="USD", rate=get_today_usd_to_krw_rate())
            data.append({
                "이름": name,
                "직책": title,
                "연봉 (USD)": formatted_pay
            })
        df = pd.DataFrame(data)
        st.subheader("🧑‍💼 상위 임원")
        st.dataframe(df, hide_index=True)

if st.button("📈 투자 지표"):
    info = data_manager.get_info(symbol)
    if not info:
        st.error(f"'{symbol}'에 대한 데이터를 불러올 수 없습니다. 종목 코드를 확인해주세요.")
    else:
        st.subheader("📈 투자 지표")
        st.markdown(f"""
        - **PER (Trailing)**: {info.get('trailingPE', 0):.2f}
        - **PER (Forward)**: {info.get('forwardPE', 0):.2f}
        - **PBR**: {info.get('priceToBook', 0):.2f}
        - **ROE**: {info.get('returnOnEquity', 0) * 100:.2f}%
        - **ROA**: {info.get('returnOnAssets', 0) * 100:.2f}%
        - **Beta**: {info.get('beta', 0):.2f}
        """)

if st.button("📊 주가/시장 정보"):
    info = data_manager.get_info(symbol)
    rate = get_today_usd_to_krw_rate()
    if not info:
        st.error(f"'{symbol}'에 대한 데이터를 불러올 수 없습니다. 종목 코드를 확인해주세요.")
    else:
        st.subheader("📊 주가/시장 정보")
        st.markdown(f"""
        - **현재가**: ${info.get('currentPrice', 0):.2f}
        - **전일 종가**: ${info.get('previousClose', 0):.2f}
        - **고가 / 저가 (당일)**: \\${info.get('dayHigh', 0):.2f} / \\${info.get('dayLow', 0):.2f}
        - **52주 최고 / 최저**: \\${info.get('fiftyTwoWeekHigh', 0):.2f} / \\${info.get('fiftyTwoWeekLow', 0):.2f}
        - **시가총액**:  {format_currency(info.get('marketCap'), "USD", rate)}
        - **유통주식수**: {info.get('sharesOutstanding', 0):,}주
        - **거래량 (당일)**: {info.get('volume', 0):,}주
        """)

        # {format_currency(info.get('marketCap'), "KRW")}

if st.button("🧠 분석가 의견"):
    info = data_manager.get_info(symbol)
    if not info:
        st.error(f"'{symbol}'에 대한 데이터를 불러올 수 없습니다. 종목 코드를 확인해주세요.")
    else:
        st.subheader("🧠 분석가 의견")
        st.markdown(f"""
        - **추천 평균 등급**: {info.get('recommendationMean', 'N/A')} ({info.get('recommendationKey', 'N/A')})
        - **분석가 수**: {info.get('numberOfAnalystOpinions', 'N/A')}
        - **목표 주가 평균**: ${info.get('targetMeanPrice', 0):.2f}
        - **목표 주가 상/하**: ${info.get('targetHighPrice', 0):.2f} / ${info.get('targetLowPrice', 0):.2f}
        """)

# ✅ 주가 히스토리 조회
st.divider()
st.subheader("📆 기간별 주가 히스토리 조회")

today = datetime.today()

start_date = st.date_input("시작일", value=today - timedelta(days=7), key="start_date_hist")
end_date = st.date_input("종료일", value=today, key="end_date_hist")

# app.py 파일의 해당 부분 수정
if st.button("📈 주가 데이터 조회"):
    if start_date >= end_date:
        st.warning("⚠️ 시작일은 종료일보다 앞서야 합니다.")
    else:
        with st.spinner("데이터 불러오는 중..."):
            raw_df, adjusted_end = data_manager.get_price_data_adjusted(
                symbol,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
        
        if raw_df is None or raw_df.empty:
            st.error("30일 이내에 해당 종목의 주가 데이터를 찾을 수 없습니다. 종목 코드 또는 기간을 확인해주세요.")
            # 디버깅을 위한 print 추가 (Streamlit 콘솔에 출력)
            print(f"Debug: No data found for {symbol} from {start_date} to {end_date}.")
            print(f"Debug: raw_df is None or empty: {raw_df is None or raw_df.empty}")
        else:
            st.success(f"📅 {adjusted_end}까지 데이터 불러오기 성공")
            
            # --- raw_df 컬럼 평탄화 추가 ---
            # yfinance가 멀티 레벨 컬럼을 반환할 수 있으므로, 여기서 평탄화
            raw_df.columns = [col[0] if isinstance(col, tuple) else col for col in raw_df.columns]
            # --- 여기까지 추가/수정 ---

            # 디버깅을 위한 print 추가 (Streamlit 콘솔에 출력)
            print(f"Debug: Raw DataFrame columns after flattening: {raw_df.columns}")
            print(f"Debug: Raw DataFrame head after flattening:\n{raw_df.head()}")
            
            # dtype 확인 라인 수정: raw_df.dtypes['Close'] 사용
            if 'Close' in raw_df.columns:
                print(f"Debug: raw_df['Close'] Dtype: {raw_df.dtypes['Close']}")
            else:
                print(f"Debug: 'Close' column not found in raw_df.")


            display_df = data_manager.process_price_df(raw_df.copy()) # 원본 raw_df를 건드리지 않도록 copy() 사용

            st.session_state["latest_df"] = display_df # AI Q&A를 위해 포맷팅된 df 저장
            st.session_state["latest_symbol"] = symbol
            st.session_state["latest_start_date"] = start_date
            st.session_state["latest_end_date"] = end_date
            st.session_state["raw_price_data"] = raw_df # AI Q&A를 위해 원본 데이터도 저장

            # 출력 (인덱스 숨기기!)
            st.dataframe(display_df, hide_index=True)

            st.subheader("📊 Chart")

            set_korean_font()

            # Plotly 그래프 구성
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=raw_df.index, # 날짜가 인덱스
                y=raw_df["Close"], # float 타입 그대로 사용
                mode='lines+markers',
                hovertemplate="날짜: %{x}<br>종가: %{y:.2f}원"
            ))

            fig.update_layout(
                xaxis_title="",
                yaxis_title="",
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=40),
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)


# ----------------------------------
# AI Q&A 히스토리 및 ENTER 실행 지원
# ----------------------------------

st.divider()
st.subheader("🧠 AI에게 자유롭게 질문하세요 (조회한 데이터 기반)")

# 히스토리 세션 state로 관리
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

# 폼(form)을 사용하면 ENTER로도 제출 가능 (버튼과 동시에 지원)
with st.form("ai_qa_form", clear_on_submit=True):
    user_question = st.text_area(
        "AI에게 질문 (예: 이 종목의 최근 변동성은? 매수 적기일까?)",
        key="user_question",
        placeholder="질문 입력 후 Enter 또는 버튼 클릭"
    )
    submitted = st.form_submit_button("AI에게 질문하기")

if submitted and ai_service: # ai_service가 초기화된 경우에만 실행
    # AI Q&A를 위해 가공되지 않은 raw_price_data를 활용하는 것이 좋습니다.
    # AI가 숫자 계산을 더 잘하도록 Volume은 정수로 변환 후 to_string
    raw_price_data = st.session_state.get("raw_price_data")
    symbol_for_ai = st.session_state.get("latest_symbol", "")
    start_date_for_ai = st.session_state.get("latest_start_date")
    end_date_for_ai = st.session_state.get("latest_end_date")

    if raw_price_data is not None and not raw_price_data.empty:
        # AI에게 전달할 데이터는 숫자형 그대로 유지 (Open, High, Low, Close, Volume)
        # 인덱스(날짜)를 컬럼으로 추가
        df_for_ai = raw_price_data.reset_index()
        df_for_ai['Date'] = df_for_ai['Date'].dt.strftime('%Y-%m-%d')
        # Volume 컬럼은 정수로 변환하여 AI가 숫자임을 명확히 인지하도록 함
        if 'Volume' in df_for_ai.columns:
            df_for_ai['Volume'] = df_for_ai['Volume'].astype(int)
        
        # AI에게 필요한 컬럼만 선택
        df_text = df_for_ai[["Date", "Open", "High", "Low", "Close", "Volume"]].to_string(index=False)

        prompt = f"""
아래는 {symbol_for_ai}의 {start_date_for_ai}부터 {end_date_for_ai}까지의 주가 데이터입니다.
이 데이터는 날짜(Date), 시가(Open), 고가(High), 저가(Low), 종가(Close), 거래량(Volume)을 포함합니다.

--- 주가 데이터 시작 ---
{df_text}
--- 주가 데이터 끝 ---
당신의 이름은 David입니다.
위의 실제 데이터에 기반하여 아래 질문에 데이터 분석가처럼 상세하게 답해주세요.
단, 답변은 한국어로 해주세요.

질문: {user_question}
"""
        with st.spinner("AI가 데이터를 바탕으로 답변 생성 중..."):
            answer = ai_service.get_qa_response(prompt, model="gpt-4o") # 모델명을 "gpt-4o" 또는 "gpt-4"로 변경
        
        # 히스토리에 Q&A 추가
        st.session_state["chat_history"].append({"user": user_question, "David": answer})
    else:
        st.warning("먼저 '주가 데이터 조회' 버튼을 눌러 종목 데이터를 조회해야 David가 답변할 수 있습니다.")
elif submitted and not ai_service:
    st.error("OpenAI API 키가 설정되지 않아 AI 서비스를 사용할 수 없습니다.")


# 히스토리 표시 (최신 질문이 가장 위에 오도록 역순으로 표시)
for item in reversed(st.session_state["chat_history"]):
    st.markdown(f"""
**사용자:** {item.get('user', '')}
> **David:** {str(item.get('David', ''))}
""")