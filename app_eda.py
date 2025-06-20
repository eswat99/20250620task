import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                이 앱은 대한민국의 **인구 관련 공공데이터(population_trends.csv)**를 기반으로,
연도별/지역별 인구 통계, 출생아 수, 사망자 수 등을 다양한 시각적 및 통계적 방식으로 탐색(EDA)할 수 있는 인터랙티브 대시보드입니다.

Streamlit 프레임워크를 기반으로 개발되었으며, CSV 파일 업로드만으로 누구나 쉽게 인구 데이터를 분석할 수 있습니다.
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 인구 동향 데이터 분석")
        uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return
        tabs = st.tabs([
            "0. 기초통계",
            "1. 연도별 추이",
            "2. 지역별 분석",
            "3. 변화량 분석",
            "4. 시각화"
        ])
        df = pd.read_csv(uploaded)
        df.columns = df.columns.str.strip()
        # 1. 목적 & 분석 절차
        with tabs[0]:
            st.dataframe(df.head())
            # 전처리: '-' → 0 치환
            df.replace('-', 0, inplace=True)

            # 숫자형 변환: '인구', '출생아수(명)', '사망자수(명)'
            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            st.subheader("🧼 전처리된 전체 데이터 미리보기")
            st.dataframe(df.head())

            # 전체 데이터 기준 요약 통계
            st.subheader("📈 전체 데이터에 대한 요약 통계 (describe())")
            st.dataframe(df.describe())

            # info()는 문자열로 캡처해서 출력
            st.subheader("🧾 전체 데이터프레임 구조 (info())")
            buffer = io.StringIO()
            df.info(buf=buffer)
            info_str = buffer.getvalue()
            st.text(info_str)
        with tabs[1]:
            st.header("📈 Population Trends: National Level Forecast")
            required_cols = ['연도', '지역', '인구', '출생아수(명)', '사망자수(명)']
            for col in required_cols:
                if col not in df.columns:
                    st.error(f"Column '{col}' not found in dataset.")
                    return

            # 전국 데이터 필터링
            national_df = df[df['지역'] == '전국'].copy()

            # 숫자형 변환
            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                national_df[col] = pd.to_numeric(national_df[col], errors='coerce').fillna(0)

            # 연도 오름차순 정렬
            national_df.sort_values(by='연도', inplace=True)

            # 최근 3년 평균 출생아수 및 사망자수 계산
            recent = national_df.tail(3)
            avg_births = recent['출생아수(명)'].mean()
            avg_deaths = recent['사망자수(명)'].mean()
            net_change = avg_births - avg_deaths
            st.write(f"Recent 3-Year Avg: Births = {avg_births:.0f}, Deaths = {avg_deaths:.0f}, Net = {net_change:.0f}")

            # 가장 최근 인구 데이터로부터 2035년까지 예측
            last_year = national_df['연도'].max()
            last_pop = national_df[national_df['연도'] == last_year]['인구'].values[0]
            years_to_forecast = 2035 - last_year
            forecast_pop = last_pop + net_change * years_to_forecast

            # 예측 결과 추가
            forecast_df = pd.DataFrame({'연도': [2035], '인구': [forecast_pop]})
            combined_df = pd.concat([national_df[['연도', '인구']], forecast_df], ignore_index=True)

            # 시각화
            plt.figure(figsize=(10, 6))
            sns.lineplot(data=combined_df, x='연도', y='인구', marker='o')
            plt.title("Population Trend and 2035 Forecast")
            plt.xlabel("Year")
            plt.ylabel("Population")
            plt.grid(True)

            # 예측 지점 강조
            plt.axvline(x=2035, color='red', linestyle='--', label='2035 Forecast')
            plt.scatter(2035, forecast_pop, color='red')
            plt.legend()

            st.pyplot(plt)
        with tabs[2]:
            st.header("📊 Regional Population Change Analysis (Last 5 Years)")    

            required_cols = ['연도', '지역', '인구']
            if not all(col in df.columns for col in required_cols):
                st.error(f"Missing one of the required columns: {required_cols}")
                return

            # 숫자형 변환
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0)

            # '전국' 제외
            df = df[df['지역'] != '전국']

            # 연도 오름차순 정렬
            df.sort_values(by='연도', inplace=True)

            # 최근 5년 확인
            recent_years = sorted(df['연도'].unique())[-5:]
            df_recent = df[df['연도'].isin(recent_years)]

            # 지역별 인구 변화량 계산
            pivot = df_recent.pivot(index='연도', columns='지역', values='인구')
            diff = (pivot.iloc[-1] - pivot.iloc[0]).sort_values(ascending=False)  # 최근 - 5년 전
            rate = ((pivot.iloc[-1] - pivot.iloc[0]) / pivot.iloc[0] * 100).sort_values(ascending=False)

            # 지역명 영어 변환 (샘플 매핑)
            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju',
                '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi', '강원': 'Gangwon',
                '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk', '전남': 'Jeonnam',
                '경북': 'Gyeongbuk', '경남': 'Gyeongnam', '제주': 'Jeju'
            }
            diff.index = diff.index.map(region_map.get)
            rate.index = rate.index.map(region_map.get)

            # 단위 변환 (천명)
            diff_thousands = (diff / 1000).round(1)
            rate_percent = rate.round(2)

            # 🔷 변화량 그래프
            st.subheader("📉 Population Change (Last 5 Years)")
            fig1, ax1 = plt.subplots(figsize=(10, 8))
            sns.barplot(x=diff_thousands.values, y=diff_thousands.index, ax=ax1, palette="Blues_r")
            ax1.set_title("Population Change by Region (in Thousands)")
            ax1.set_xlabel("Change (Thousands)")
            ax1.set_ylabel("Region")

            # 막대에 수치 표시
            for i, v in enumerate(diff_thousands.values):
                ax1.text(v + 1, i, f"{v}", va='center')

            st.pyplot(fig1)

            # 🔷 변화율 그래프
            st.subheader("📈 Population Growth Rate (%)")
            fig2, ax2 = plt.subplots(figsize=(10, 8))
            sns.barplot(x=rate_percent.values, y=rate_percent.index, ax=ax2, palette="Greens_r")
            ax2.set_title("Population Growth Rate by Region")
            ax2.set_xlabel("Change Rate (%)")
            ax2.set_ylabel("Region")

            for i, v in enumerate(rate_percent.values):
                ax2.text(v + 0.2, i, f"{v:.2f}%", va='center')

            st.pyplot(fig2)

            # 🔍 해설
            st.markdown("### 🧾 Interpretation")
            st.markdown(f"""
            - The **population change** graph shows the absolute increase or decrease in population (in thousands) over the last 5 years per region.
            - The **growth rate** graph shows the percentage change compared to the population 5 years ago.
            - Regions with a **positive bar** indicate growth, while **negative bars** show a population decline.
            - This analysis helps identify **demographically growing or shrinking areas**, useful for policy, infrastructure, or economic planning.
            """)
        with tabs[3]:
            st.header("📋 Top 100 Population Changes by Region and Year")
            if not all(col in df.columns for col in ['연도', '지역', '인구']):
                st.error("❌ Required columns ('연도', '지역', '인구') are missing.")
                return

            df = df[df['지역'] != '전국'].copy()
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce')
            df.dropna(subset=['인구'], inplace=True)

            # 연도 정렬
            df.sort_values(by=['지역', '연도'], inplace=True)

            # 증감 계산
            df['증감'] = df.groupby('지역')['인구'].diff()

            # 최근 100개 절댓값 기준 증감 상위
            top_changes = df.dropna(subset=['증감']).copy()
            top_changes['abs_증감'] = top_changes['증감'].abs()
            top_100 = top_changes.sort_values(by='abs_증감', ascending=False).head(100)

            # 천단위 콤마 적용
            top_100['인구'] = top_100['인구'].apply(lambda x: f"{int(x):,}")
            top_100['증감'] = top_100['증감'].apply(lambda x: f"{int(x):,}")

            # 시각적 강조 (증감 열 배경색)
            def highlight_diff(val):
                try:
                    val_int = int(val.replace(",", ""))
                    if val_int > 0:
                        color = f'background-color: rgba(0, 100, 255, 0.15);'
                    elif val_int < 0:
                        color = f'background-color: rgba(255, 0, 0, 0.15);'
                    else:
                        color = ''
                    return color
                except:
                    return ''

            styled = top_100[['연도', '지역', '인구', '증감']].style.applymap(highlight_diff, subset=['증감'])

            st.subheader("📈 Top 100 Population Changes")
            st.dataframe(styled, use_container_width=True)
        with tabs[4]:
            if not all(col in df.columns for col in ['연도', '지역', '인구']):
                st.error("CSV must contain columns: '연도', '지역', '인구'")
                return
            # 전국 제외 & 숫자형 변환
            df = df[df['지역'] != '전국'].copy()
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce')
            df.dropna(subset=['인구'], inplace=True)

            # 지역명 영문 변환
            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon', '광주': 'Gwangju',
                '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong', '경기': 'Gyeonggi', '강원': 'Gangwon',
                '충북': 'Chungbuk', '충남': 'Chungnam', '전북': 'Jeonbuk', '전남': 'Jeonnam',
                '경북': 'Gyeongbuk', '경남': 'Gyeongnam', '제주': 'Jeju'
            }
            df['Region'] = df['지역'].map(region_map)

            # 피벗 테이블 생성: 행=연도, 열=지역, 값=인구
            pivot = df.pivot_table(index='연도', columns='Region', values='인구', aggfunc='sum').fillna(0)

            # 연도 순 정렬
            pivot.sort_index(inplace=True)

            # 그래프 그리기
            st.subheader("📈 Stacked Area Chart by Region")

            plt.figure(figsize=(12, 6))
            sns.set_palette("tab20")  # 명확한 구분을 위한 색상 세트

            plt.stackplot(
                pivot.index,
                pivot.T.values,
                labels=pivot.columns,
                alpha=0.9
            )

            plt.legend(loc='upper left', bbox_to_anchor=(1.01, 1), fontsize='small')
            plt.title("Regional Population Over Time (Stacked Area)")
            plt.xlabel("Year")
            plt.ylabel("Population")
            plt.tight_layout()

            st.pyplot(plt)

            st.markdown("This chart visualizes population contributions by each region over time. The stacked area shows cumulative growth and relative share.")
# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()