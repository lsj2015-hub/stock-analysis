import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st

class YahooFinanceDataManager:
    def __init__(self):
        pass

    @st.cache_data(show_spinner=True, ttl=3600) # 1시간 캐싱
    def get_price_data_adjusted(_self, symbol: str, start: str, end: str, max_backtrack_days: int = 30): # self를 _self로 변경
        """
        주가 데이터를 조회합니다. 
        종료일에 데이터가 없으면 이전 날짜로 이동하며 최대 `max_backtrack_days`까지 조회합니다.
        """
        current_end = datetime.strptime(end, "%Y-%m-%d")
        for i in range(max_backtrack_days):
            end_str = current_end.strftime("%Y-%m-%d")
            try:
                df = yf.download(symbol, start=start, end=end_str, progress=False)
                if not df.empty:
                    return df, end_str
            except Exception as e:
                print(f"yfinance download error for {symbol} on {end_str}: {e}")
            current_end -= timedelta(days=1)
        return None, None

    @st.cache_data(show_spinner=False, ttl=3600) # 1시간 캐싱
    def get_info(_self, symbol: str) -> dict | None: # self를 _self로 변경
        """
        주어진 종목 코드에 대한 기업 정보를 가져옵니다.
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # yfinance가 빈 dict나 None을 반환하는 경우 방지
            if not info or not isinstance(info, dict) or not info.get('symbol'):
                return None

            return info
        except Exception as e:
            print(f"기업 정보 가져오기 실패: {e}")
            return None

    def process_price_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        다운로드한 주가 데이터를 Streamlit 표시를 위해 포맷팅합니다.
        """
        if df is None:
            return pd.DataFrame()
            
        df = df.reset_index()
        # 멀티 인덱스 컬럼 평탄화 처리 (yfinance 최신 버전에서는 필요 없을 수도 있지만 안전하게 유지)
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
        
        df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
        
        # 숫자 컬럼이 존재하는지 확인 후 처리
        numeric_cols = ["Close", "High", "Low", "Open", "Volume"]
        for col in numeric_cols:
            if col in df.columns:
                if col != "Volume":
                    df[col] = df[col].map(lambda x: f"{x:.2f}")
                else:
                    df[col] = df[col].map(lambda x: f"{int(x):,}")
        
        # 필요한 컬럼만 선택하고 순서 정리
        final_cols = ["Date", "Close", "High", "Low", "Open", "Volume"]
        return df[final_cols]