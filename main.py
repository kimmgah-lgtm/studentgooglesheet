import streamlit as st
import pandas as pd
import plotly.express as px


# 페이지 설정
st.set_page_config(layout="wide", page_title="학생 점수 대시보드")

st.title("📚 학생 점수 대시보드")
st.write("구글 시트에서 학생 점수 데이터를 가져와 시각화합니다.")

# Google Sheets 연결
# .streamlit/secrets.toml에 설정된 'gsheets' 연결을 사용합니다.
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error(f"Google Sheets 연결에 실패했습니다: {e}")
    st.info("`.streamlit/secrets.toml` 파일에 구글 시트 공유 주소가 올바르게 설정되었는지 확인해주세요.")
    st.stop()

# --- 시트 선택 기능 ---
# 워크시트 이름 가져오기 (Google Sheets API를 통해 직접 가져올 수 있다면 더 좋습니다.)
# 현재 GSheetsConnection은 직접 워크시트 목록을 제공하지 않으므로,
# 임의의 목록을 사용하거나, 사용자가 직접 입력하도록 할 수 있습니다.
# 여기서는 예시로 워크시트 이름을 직접 지정합니다.
# 실제 시트에서 사용하고 있는 워크시트 이름으로 변경해주세요.
WORKSHEET_NAMES = ["국어", "수학", "사회", "과학"] # 여기에 실제 구글 시트의 워크시트 이름을 입력하세요.

selected_worksheet_name = st.sidebar.selectbox(
    "데이터를 가져올 시트를 선택하세요:",
    WORKSHEET_NAMES
)

if not selected_worksheet_name:
    st.warning("선택된 시트가 없습니다. 시트를 선택해주세요.")
    st.stop()

@st.cache_data(ttl=600) # 10분마다 데이터 새로고침
def load_data(worksheet_name):
    try:
        df = conn.read(worksheet=worksheet_name)
        # 빈 행 제거 (모든 값이 NaN인 행)
        df = df.dropna(how='all')
        # 첫 번째 행을 컬럼 헤더로 사용하고 데이터는 두 번째 행부터 시작
        # df.columns = df.iloc[0]
        # df = df[1:].reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"'{worksheet_name}' 시트에서 데이터를 불러오는 데 실패했습니다: {e}")
        return pd.DataFrame() # 빈 DataFrame 반환

df = load_data(selected_worksheet_name)

if df.empty:
    st.info("선택된 시트에서 데이터를 찾을 수 없습니다. 시트 내용을 확인해주세요.")
    st.stop()

# 데이터 전처리 및 확인 (예시 구글 시트 구조에 맞춤)
# 첫 번째 열을 '이름'으로 가정하고, 나머지를 점수 데이터로 가정합니다.
# 실제 구글 시트의 구조에 따라 이 부분을 조정해야 합니다.
# 예시 시트의 1행이 헤더이므로, 첫 행을 헤더로 설정합니다.

# '이름' 컬럼이 없으면 에러 처리
if '이름' not in df.columns:
    st.error("데이터에 '이름' 컬럼이 없습니다. 구글 시트의 첫 번째 열 이름을 '이름'으로 설정하거나, 코드에서 컬럼 이름을 수정해주세요.")
    st.dataframe(df) # 어떤 데이터가 로드되었는지 보여줌
    st.stop()

# '이름' 컬럼을 제외한 나머지 컬럼은 점수 데이터로 간주
score_columns = [col for col in df.columns if col != '이름']

# 점수 데이터를 숫자로 변환 (변환할 수 없는 값은 NaN으로)
for col in score_columns:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 전체 평균 계산
overall_averages = df[score_columns].mean().reset_index()
overall_averages.columns = ['단원', '평균 점수']


# --- 사이드바에 이름 목록 표시 ---
st.sidebar.header("학생 선택")
student_names = df['이름'].tolist()
# student_names 리스트에서 NaN 값 제거 (점수가 없는 학생 제외)
student_names = [name for name in student_names if pd.notna(name)]

if not student_names:
    st.sidebar.warning("학생 이름을 찾을 수 없습니다. '이름' 컬럼을 확인해주세요.")
    st.stop()

selected_student = st.sidebar.radio("학생 이름을 클릭하세요:", student_names)

# --- 선택된 학생의 데이터 시각화 ---
if selected_student:
    st.header(f"{selected_student} 학생의 점수 대시보드")

    student_data = df[df['이름'] == selected_student].iloc[0]
    student_scores = pd.DataFrame({
        '단원': score_columns,
        '점수': [student_data[col] for col in score_columns]
    })

    # 전체 평균과 학생 점수 데이터를 하나의 DataFrame으로 합치기
    plot_df = pd.merge(overall_averages, student_scores, on='단원', how='left')
    plot_df.columns = ['단원', '전체 평균', '내 점수']

    # 꺾은선 그래프 생성 (Plotly)
    fig = px.line(
        plot_df,
        x='단원',
        y=['전체 평균', '내 점수'],
        title=f'{selected_student} 학생 점수 및 전체 평균 비교',
        labels={'value': '점수', 'variable': '구분'},
        markers=True # 점을 표시
    )

    fig.update_layout(
        hovermode="x unified", # 마우스 오버 시 단원별 데이터 통합 표시
        xaxis_title="단원",
        yaxis_title="점수",
        legend_title="범례",
        font=dict(family="Arial", size=12, color="RebeccaPurple"),
        width=800, # 그래프 너비 조절
        height=500 # 그래프 높이 조절
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("세부 점수")
    st.dataframe(plot_df.set_index('단원'))

else:
    st.info("왼쪽 사이드바에서 학생을 선택하여 대시보드를 확인하세요.")
