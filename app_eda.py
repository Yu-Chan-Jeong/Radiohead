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

        uploaded = st.file_uploader("Upload population_trend.csv", type="csv")
        if not uploaded:
            st.info("Please upload population_trend.csv")
            st.stop()

        # 2) 원본 한 번 읽기
        orig_df = pd.read_csv(uploaded, dtype=str)
        orig_df.columns = orig_df.columns.str.strip()

        # 3) Sejong 통계
        sejong = orig_df[orig_df['지역']=='세종'].replace('-', '0').copy()
        for col in ['인구','출생아수(명)','사망자수(명)']:
            sejong[col] = pd.to_numeric(sejong[col], errors='coerce')
        st.subheader("Sejong Data Structure")
        buf = io.StringIO(); sejong.info(buf=buf); st.text(buf.getvalue())
        st.subheader("Sejong Descriptive Statistics")
        st.dataframe(sejong[['인구','출생아수(명)','사망자수(명)']].describe())

        # 4) Nationwide 추이 & 2035 예측
        nation = orig_df[orig_df['지역']=='전국'].replace('-', '0').copy()
        nation['Year']       = nation['연도'].astype(int)
        nation['Population'] = pd.to_numeric(nation['인구'], errors='coerce')
        nation['Births']     = pd.to_numeric(nation['출생아수(명)'], errors='coerce')
        nation['Deaths']     = pd.to_numeric(nation['사망자수(명)'], errors='coerce')
        nation = nation.dropna(subset=['Population','Births','Deaths']).sort_values('Year')

        last3   = nation.tail(3)
        avg_net = (last3['Births'] - last3['Deaths']).mean()
        ly, lp  = last3['Year'].iat[-1], last3['Population'].iat[-1]
        proj_years = list(range(ly+1, 2036))
        proj_pops  = [lp + avg_net*(y-ly) for y in proj_years]
        proj_df    = pd.DataFrame({'Year': proj_years, 'Population': proj_pops})

        trend_df = pd.concat([nation[['Year','Population']], proj_df], ignore_index=True)
        fig, ax = plt.subplots(figsize=(10,6))
        sns.lineplot(data=trend_df, x='Year', y='Population', label='Observed', ax=ax)
        sns.scatterplot(data=proj_df, x='Year', y='Population', label='Projected', ax=ax)
        ax.set_title('Population Trend by Year')
        ax.set_xlabel('Year')
        ax.set_ylabel('Population')
        ax.legend()
        st.subheader("Nationwide Population Trend")
        st.pyplot(fig)

        # 5) 지역별 5년 변화량 & 변화율
        reg = orig_df[orig_df['지역']!='전국'].replace('-', '0').copy()
        reg['Year']       = reg['연도'].astype(int)
        reg['Population'] = pd.to_numeric(reg['인구'], errors='coerce')
        reg = reg.dropna(subset=['Population'])
        region_map = {
            '서울특별시':'Seoul','부산광역시':'Busan','대구광역시':'Daegu',
            '인천광역시':'Incheon','광주광역시':'Gwangju','대전광역시':'Daejeon',
            '울산광역시':'Ulsan','세종특별자치시':'Sejong','경기도':'Gyeonggi',
            '강원도':'Gangwon','충청북도':'Chungbuk','충청남도':'Chungnam',
            '전라북도':'Jeonbuk','전라남도':'Jeonnam','경상북도':'Gyeongbuk',
            '경상남도':'Gyeongnam','제주특별자치도':'Jeju'
        }
        reg['Region'] = reg['지역'].map(region_map)

        pivot = reg.pivot_table(index='Region', columns='Year', values='Population')
        years = sorted(pivot.columns)
        if len(years) > 1:
            last_year = years[-1]
            year_5ago = years[-6] if len(years)>5 else years[0]
            piv2 = pivot.dropna(subset=[year_5ago, last_year])
            piv2['Change'] = piv2[last_year] - piv2[year_5ago]
            piv2['Rate']   = piv2['Change'] / piv2[year_5ago] * 100
            piv2 = piv2.sort_values('Change', ascending=False)

            # Absolute change
            fig1, ax1 = plt.subplots(figsize=(8,6))
            sns.barplot(x=piv2['Change']/1000, y=piv2.index, ax=ax1)
            ax1.set_title('5-Year Population Change')
            ax1.set_xlabel('Change (Thousands)')
            for i, v in enumerate(piv2['Change']/1000):
                ax1.text(v+0.5, i, f"{v:.1f}", va='center')
            st.pyplot(fig1)

            # Change rate
            fig2, ax2 = plt.subplots(figsize=(8,6))
            sns.barplot(x=piv2['Rate'], y=piv2.index, ax=ax2)
            ax2.set_title('5-Year Population Change Rate')
            ax2.set_xlabel('Rate (%)')
            for i, v in enumerate(piv2['Rate']):
                ax2.text(v+0.5, i, f"{v:.1f}%", va='center')
            st.pyplot(fig2)

        # 6) 연도별 증감 상위 100건 테이블
        yearly = reg[['Region','Year','Population']].sort_values(['Region','Year'])
        diff_df = (
            yearly
            .groupby('Region')
            .apply(lambda g: g.assign(Diff=g['Population'].diff()))
            .reset_index(drop=True)
            .dropna(subset=['Diff'])
        )
        top100 = diff_df.sort_values('Diff', ascending=False).head(100)

        def hl(val):
            return 'background-color: lightblue' if val>0 else 'background-color: lightcoral'
        styled = (
            top100[['Region','Year','Population','Diff']]
            .style
            .applymap(hl, subset=['Diff'])
            .format({"Population":"{:,}", "Diff":"{:,}"})
        )
        st.subheader("Top 100 Year-over-Year Changes")
        st.write(styled)


        tabs = st.tabs([
            "1. 목적 & 절차",
            "2. 데이터셋 설명",
            "3. 데이터 로드 & 품질 체크",
            "4. Datetime 특성 추출",
            "5. 시각화",
            "6. 상관관계 분석",
            "7. 이상치 제거",
            "8. 로그 변환"
        ])

        


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