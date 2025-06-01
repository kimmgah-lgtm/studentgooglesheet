import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(layout="wide", page_title="학생 점수 대시보드")

st.title("📚 학생 점수 대시보드")
st.write("구글 시트에서 학생 점수 데이터를 가져와 시각화합니다.")

# Google Sheets 연결
try:
    conn = st.connection("gsheets", type="gsheets")
except Exception as e:
    st.error(f"Google Sheets 연결에 실패했습니다: {e}")
    st.info("Google Sheets 인증 정보가 올바르게 설정되었는지 확인해주세요. 'streamlit-gsheets-connection' 패키지가 설치되어 있는지 확인하세요.")
    st.stop()

# --- 시트 선택 기능 ---
WORKSHEET_NAMES = ["국어", "수학", "사회", "과학"]  # 실제 워크시트 이름으로 변경

selected_worksheet_name = st.sidebar.selectbox(
    "데이터를 가져올 시트를 선택하세요:",
    WORKSHEET_NAMES
)

if not selected_worksheet_name:
    st.warning("선택된 시트가 없습니다. 시트를 선택해주세요.")
    st.stop()

@st.cache_data(ttl=600)
def load_data(worksheet_name):
    try:
        df = conn.read(worksheet=worksheet_name, ttl=600)
        df = df.dropna(how="all")
        return df
    except Exception as e:
        st.error(f"'{worksheet_name}' 시트에서 데이터를 불러오는 데 실패했습니다: {e}")
        return pd.DataFrame()

df = load_data(selected_worksheet_name)

if df.empty:
    st.info("선택된 시트에서 데이터를 찾을 수 없습니다. 시트 내용을 확인해주세요.")
    st.stop()

# 데이터 전처리 및 확인
if "이름" not in df.columns:
    st.error("데이터에 '이름' 컬럼이 없습니다. 구글 시트의 첫 번째 열 이름을 '이름'으로 설정하거나, 코드에서 컬럼 이름을 수정해주세요.")
    st.dataframe(df)
    st.stop()

# 점수 컬럼 추출
score_columns = [col for col in df.columns if col != "이름"]

# 점수 데이터를 숫자로 변환
for col in score_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# 전체 평균 계산
overall_averages = df[score_columns].mean().reset_index()
overall_averages.columns = ["단원", "평균 점수"]

# --- 사이드바에 이름 목록 표시 ---
st.sidebar.header("학생 선택")
student_names = [name for name in df["이름"].tolist() if pd.notna(name)]

if not student_names:
    st.sidebar.warning("학생 이름을 찾을 수 없습니다. '이름' 컬럼을 확인해주세요.")
    st.stop()

selected_student = st.sidebar.radio("학생 이름을 클릭하세요:", student_names)

# --- 선택된 학생의 데이터 시각화 ---
if selected_student:
    st.header(f"{selected_student} 학생의 점수 대시보드")

    student_data = df[df["이름"] == selected_student].iloc[0]
    student_scores = pd.DataFrame({
        "단원": score_columns,
        "점수": [student_data[col] for col in score_columns]
    })

    plot_df = pd.merge(overall_averages, student_scores, on="단원", how="left")
    plot_df.columns = ["단원", "전체 평균", "내 점수"]

    fig = px.line(
        plot_df,
        x="단원",
        y=["전체 평균", "내 점수"],
        title=f"{selected_student} 학생 점수 및 전체 평균 비교",
        labels={"value": "점수", "variable": "구분"},
        markers=True
    )

    fig.update_layout(
        hovermode="x unified",
        xaxis_title="단원",
        yaxis_title="점수",
        legend_title="범례",
        font=dict(family="Arial", size=12, color="RebeccaPurple"),
        width=800,
        height=500
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("세부 점수")
    st.dataframe(plot_df.set_index("단원"))

else:
    st.info("왼쪽 사이드바에서 학생을 선택하여 대시보드를 확인하세요.")
