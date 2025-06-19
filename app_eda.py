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
                ---
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
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
        st.title("📊 Population Trend EDA")

        # 1) File uploader
        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if not uploaded:
            st.info("Please upload population_trends.csv")
            st.stop()

        # 2) Read and clean
        orig_df = pd.read_csv(uploaded, dtype=str)
        orig_df.columns = orig_df.columns.str.strip()
        orig_df = orig_df.replace('-', '0')
        orig_df['Year']       = orig_df['연도'].astype(int)
        orig_df['Population'] = pd.to_numeric(orig_df['인구'], errors='coerce')
        orig_df['Births']     = pd.to_numeric(orig_df['출생아수(명)'], errors='coerce')
        orig_df['Deaths']     = pd.to_numeric(orig_df['사망자수(명)'], errors='coerce')

        # 3) Prepare regional DataFrame (exclude nationwide)
        region_df = orig_df[orig_df['지역'] != '전국'].copy()
        region_map = {
            '서울특별시':'Seoul','부산광역시':'Busan','대구광역시':'Daegu',
            '인천광역시':'Incheon','광주광역시':'Gwangju','대전광역시':'Daejeon',
            '울산광역시':'Ulsan','세종특별자치시':'Sejong','경기도':'Gyeonggi',
            '강원도':'Gangwon','충청북도':'Chungbuk','충청남도':'Chungnam',
            '전라북도':'Jeonbuk','전라남도':'Jeonnam','경상북도':'Gyeongbuk',
            '경상남도':'Gyeongnam','제주특별자치도':'Jeju'
        }
        region_df['Region'] = region_df['지역'].map(region_map)
        region_df = region_df.dropna(subset=['Population'])

        # 4) Pivot table for tabs below
        pivot = (
            region_df
            .pivot_table(index='Year', columns='Region', values='Population', aggfunc='sum')
            .fillna(0)
            .sort_index()
        )
        # Ensure numeric dtype for plotting
        pivot = pivot.astype(float)

        # 5) Tabs
        tabs = st.tabs([
            "Basic Stats",
            "Nationwide Trend",
            "Pivot Table",
            "Change Analysis",
            "Visualization"
        ])

        # Basic Stats
        with tabs[0]:
            st.header("Basic Statistics")
            buf = io.StringIO()
            orig_df.info(buf=buf)
            st.text(buf.getvalue())
            st.subheader("Descriptive Statistics")
            st.dataframe(orig_df[['Population','Births','Deaths']].describe())

        # Nationwide Trend
        with tabs[1]:
            st.header("Nationwide Trend & 2035 Projection")
            nation = orig_df[orig_df['지역']=='전국'].sort_values('Year')
            last3   = nation.tail(3)
            avg_net = (last3['Births'] - last3['Deaths']).mean()
            ly, lp  = last3['Year'].iat[-1], last3['Population'].iat[-1]
            proj_years = list(range(ly+1, 2036))
            proj_pops  = [lp + avg_net*(y-ly) for y in proj_years]
            proj_df    = pd.DataFrame({'Year': proj_years, 'Population': proj_pops})
            trend_df   = pd.concat([nation[['Year','Population']], proj_df], ignore_index=True)

            fig, ax = plt.subplots(figsize=(10,6))
            sns.lineplot(data=trend_df, x='Year', y='Population', label='Observed', ax=ax)
            sns.scatterplot(data=proj_df, x='Year', y='Population', label='Projected', ax=ax)
            ax.set_title("Population Trend by Year")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend()
            st.pyplot(fig)

        # Pivot Table
        with tabs[2]:
            st.header("Pivot Table: Population by Region & Year")
            st.dataframe(pivot)

        # Change Analysis
        with tabs[3]:
            st.header("5-Year Change Analysis")
            years = sorted(pivot.columns)
            if len(years) < 2:
                st.warning("Not enough data to compute changes.")
            else:
                last_year = years[-1]
                year_5ago = years[-6] if len(years) > 5 else years[0]
                p5 = pivot.dropna(subset=[year_5ago, last_year]).copy()
                p5['Change'] = p5[last_year] - p5[year_5ago]
                p5['Rate']   = p5['Change'] / p5[year_5ago] * 100
                p5 = p5.sort_values('Change', ascending=False)

                fig1, ax1 = plt.subplots(figsize=(8,6))
                sns.barplot(x=p5['Change']/1000, y=p5.index, ax=ax1, palette="Blues_d")
                ax1.set_title("5-Year Population Change")
                ax1.set_xlabel("Change (Thousands)")
                st.pyplot(fig1)

                fig2, ax2 = plt.subplots(figsize=(8,6))
                sns.barplot(x=p5['Rate'], y=p5.index, ax=ax2, palette="coolwarm")
                ax2.set_title("5-Year Change Rate (%)")
                ax2.set_xlabel("Rate (%)")
                st.pyplot(fig2)

        # Visualization
        with tabs[4]:
            st.header("Cumulative Population Area Chart")

            # 1) X축: Year 리스트 (정수)
            years = pivot.index.astype(int).tolist()

            # 2) Y축: 각 Region별 Population 값 배열 (float)
            data = [pivot[col].astype(float).to_numpy() for col in pivot.columns]

            # 3) 그리기
            fig3, ax3 = plt.subplots(figsize=(12, 7))
            palette = sns.color_palette("tab20", n_colors=len(data))
            ax3.stackplot(years, *data, labels=pivot.columns.tolist(), colors=palette)
            ax3.set_title("Population by Region Over Years")
            ax3.set_xlabel("Year")
            ax3.set_ylabel("Population")
            ax3.legend(title="Region", bbox_to_anchor=(1, 1))

            plt.tight_layout()
            st.pyplot(fig3)
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