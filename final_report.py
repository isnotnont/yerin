#!/usr/bin/env python
# coding: utf-8

# In[108]:


#전처리
import re
import pandas as pd
import numpy as np
#시각화
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
# 지도
import folium
import geopandas as gpd
from folium.plugins import Draw
from folium.features import CustomIcon
from streamlit_folium import folium_static

sns.set_theme(style='whitegrid', font_scale=1.5)
sns.set_palette("pastel", n_colors=10)
plt.rc('font', family='Malgun Gothic')
plt.rc('axes', unicode_minus=False)


# In[109]:


st.set_page_config(
    page_title="유기동물, 보호소 현황",
    page_icon="☠",
    layout="centered")

st.sidebar.title('유기동물, 보호소 대시보드')
st.sidebar.caption('이 문서는 이용 현황 데이터와 분석 레포트가 페이지로 구분되어 있습니다.')

radio = st.sidebar.radio("열람하실 레포트를 선택하세요",
    ('Overview', 'Report', 'Advanced Report'))

@st.cache_data
def load_geodata():
    geojson_path = 'TL_SCCO_CTPRVN.json'
    gdf = gpd.read_file(geojson_path, encoding='utf-8')
    return gdf
gdf = load_geodata()
@st.cache_data(hash_funcs={pd.read_csv: lambda _: None})
def load_data():
    df = pd.read_csv('abandon_animal_geo2.csv')
    #보호소 이름 전처리 ()괄호 없애기
    df['careNm'] = df['careNm'].apply(lambda x: re.sub(r'\([^)]*\)', '', x))
    #발생일자 날짜 타입으로 변경
    df['happenDt'] = pd.to_datetime(df['happenDt'], format='%Y%m%d')    
    #processState 간소화
    df['processState_class'] = df['processState'].replace({ '종료(자연사)': 'Death',
                                                            '종료(안락사)': 'Death',
                                                            '종료(반환)': 'Alive',
                                                            '종료(기증)': 'Alive',
                                                            '종료(입양)': 'Alive',
                                                            '종료(방사)': 'Alive',
                                                            '종료(기타)': 'Alive',
                                                            '보호중': 'Under care'})
    return df

df = load_data()
if radio == 'Overview':
    st.title('Overview')     
    st.caption("Data Range: 20210221 ~ 20240220")
    
    with st.sidebar.container():
        st.markdown("[1. 유기동물 현황](#1._유기동물_현황)", unsafe_allow_html=True)
        st.markdown("[2. 보호소 현황](#2._보호소_현황)", unsafe_allow_html=True)
    
    st.header('1. 유기동물 현황', anchor = '1._유기동물_현황')
    st.metric(label="전체 유기동물 수", value='%d' % len(df))
    
    df1, df2 = st.columns((1, 1))
    with df1:
        multiselect_year = st.multiselect('Year', 
                                      df['happenDt'].dt.year.unique().tolist(),
                                      default=df['happenDt'].dt.year.unique().tolist()[3])    
    with df2:
        filtered_df = df[df['happenDt'].dt.year.isin(multiselect_year)]
        yearly_animal_count_filtered = filtered_df.groupby(filtered_df['happenDt'].dt.year).size()
        yearly_animal_count_filtered = yearly_animal_count_filtered.reindex(multiselect_year)
        yearly_animal_count_filtered.index.name = '연도'
        st.metric(label="선택된 연도 유기동물 수", value='%d' % yearly_animal_count_filtered.sum()) 
        
    fig = px.bar(
        yearly_animal_count_filtered, 
        x=yearly_animal_count_filtered.index, 
        y=yearly_animal_count_filtered.values,
        labels={'x':'연도', 'y':'유기동물 수'},
        title='선택 연도 유기동물 수',
        color_discrete_sequence=['dodgerblue']
    )
    fig.update_layout(xaxis={'type': 'category'}) #날짜형으롤 처리 안하고 카테고리형으로 처리해줌
    fig.update_traces(hoverlabel=dict(font=dict(size=16))) # 툴팁의 글자 크기를 16으로 지정
    fig.update_layout(yaxis=dict(range=[95000, 115000])) #y축 범위 설정

    st.plotly_chart(fig)
        
    st.header('2. 보호소 현황',anchor = '2._보호소_현황')
    st.metric(label="전체 보호소 수", value='%d' % len(df['careNm'].unique()))

    df1, df2 = st.columns((1, 1))
    with df1:
        multiselect_year = st.multiselect('Year', 
                                          df['happenDt'].dt.year.unique().tolist(),
                                          default=df['happenDt'].dt.year.unique().tolist()[:4],
                                          key='year_multiselect')  # Unique key added here
    with df2:        
        filtered_df = df[df['happenDt'].dt.year.isin(multiselect_year)]
        yearly_shelter_filtered = filtered_df.groupby(filtered_df['happenDt'].dt.year)['careNm'].nunique()
        yearly_shelter_filtered.index.name = '연도'
        st.metric(label="선택 연도 보호소 수", value='%d' % len(df['careNm'].unique()))          

    fig = px.bar(
        x=yearly_shelter_filtered.index,
        y=yearly_shelter_filtered.values,
        labels={'x': '연도', 'y': '보호소 수'},
        title='선택 연도 보호소 수',
        color_discrete_sequence=['dodgerblue']
        )
    fig.update_layout(xaxis={'type': 'category'})  
    st.plotly_chart(fig)

elif radio == 'Report':
    with st.sidebar.container():
        st.markdown("[1. 유기동물_상태_현황](#1._유기동물_상태_현황)", unsafe_allow_html=True)
        st.markdown("[2. 보호소 현황](#2._보호소_현황)", unsafe_allow_html=True)  
    
    st.title('Report')
    st.header('1. 유기동물_상태_현황', anchor='#1._유기동물_상태_현황')
    st.caption('데이터 구간: 202102~202402')      
    
    col1, col2 = st.columns([1, 3])
    selected_option = col1.radio("파이 차트 선택", ["유기동물 상태", "성별", "중성화 여부"])
    if selected_option == "유기동물 상태":
        labels = df["processState_class"].value_counts().index.tolist() 
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie(df["processState_class"].value_counts(), autopct='%1.1f%%', shadow=True)
        ax.set_title("유기동물 상태")
        ax.legend(labels, loc="best")
        col2.pyplot(fig)             
    elif selected_option == "성별":        
        labels = df["sexCd"].value_counts().index.tolist()
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie(df["sexCd"].value_counts(), autopct='%1.1f%%', shadow=True)
        ax.set_title("성별")
        ax.legend(labels, loc="best")
        col2.pyplot(fig) 
    elif selected_option == "중성화 여부":
        df['neuterYn'] = df['neuterYn'].replace({'Y': 'Yes', 'N': 'No', 'U': 'Unknown'})      
        labels = df["neuterYn"].value_counts().index.tolist() 
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie(df['neuterYn'].value_counts()[['Yes', 'No', 'Unknown']], autopct='%1.1f%%', shadow=True)
        ax.set_title("중성화 여부")
        ax.legend(labels, loc="best")
        col2.pyplot(fig)   
    
    col1, col2 = st.columns([1, 3])
    selected_option = col1.radio("그래프 선택", ["중성화 여부", "성별"])
    if selected_option == "중성화 여부":
        grouped_data = df.groupby(['processState_class', 'neuterYn']).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(10, 6))
        grouped_data.plot(kind='bar', stacked=True, ax=ax)
        ax.set_title('유기동물 상태별 중성화 여부')
        ax.set_xlabel('유기동물 상태')
        ax.set_ylabel('빈도')
        ax.legend(title='중성화 여부', labels=['알 수 없음', '중성화', '중성화되지 않음'])
        plt.xticks(rotation=0)
        col2.pyplot(fig)
    elif selected_option == "성별":
        grouped_data = df.groupby(['processState_class', 'sexCd']).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(10, 6))
        grouped_data.plot(kind='bar', stacked=True, ax=ax)
        ax.set_title('유기동물 상태별 성별')
        ax.set_xlabel('유기동물 상태')
        ax.set_ylabel('빈도')
        ax.legend(title='성별')
        plt.xticks(rotation=0)
        col2.pyplot(fig)
        
elif radio == 'Advanced Report':    
    st.sidebar.container().markdown("[1. 보호소 별 점수](#1.보호소_별_점수)", unsafe_allow_html=True)
    st.header('1. 보호소 별 점수', anchor='1.보호소 별 점수')
    st.caption('데이터 구간: 202102~202402')
    adopted_animals = df[df['processState_class'] == 'Alive']
    adoptions_by_shelter_with_location = adopted_animals.groupby(['careNm', 'lat', 'lng']).size().reset_index(name='Adoptions')
    adoptions_by_shelter_df = adoptions_by_shelter_with_location 
    conditions = [
        (adoptions_by_shelter_df['Adoptions'] >= 800),
        (adoptions_by_shelter_df['Adoptions'] <= 100),
        (adoptions_by_shelter_df['Adoptions'] < 800) & (adoptions_by_shelter_df['Adoptions'] >100)
        ]
    # 분류에 따른 레이블
    labels = ['Good', 'Bad', 'Okay']
    # 새로운 열에 분류 결과 저장
    adoptions_by_shelter_df['Adoptions_Group'] = np.select(conditions, labels)

    hill1, hill2, hill3 = st.columns(3)
    with hill1:
        good_shelters = adoptions_by_shelter_df[adoptions_by_shelter_df['Adoptions_Group'] == 'Good']
        st.metric(label="Good😄", value=f'{good_shelters.shape[0]} 개')
    with hill2:
        okay_shelters = adoptions_by_shelter_df[adoptions_by_shelter_df['Adoptions_Group'] == 'Okay']
        st.metric(label="Okay😐", value=f'{okay_shelters.shape[0]} 개')
    with hill3:
        bad_shelters = adoptions_by_shelter_df[adoptions_by_shelter_df['Adoptions_Group'] == 'Bad']
        st.metric(label="Bad🙁", value=f'{bad_shelters.shape[0]} 개')

    option = st.selectbox('Select Data', ["Good", "Okay", "Bad"])
    filtered_data = adoptions_by_shelter_df[adoptions_by_shelter_df['Adoptions_Group'] == option]
    df_sorted = filtered_data.sort_values(by='Adoptions', ascending=False)    
    
    SuperShelter = st.sidebar.slider('SuperShelter',1,13,1)  
    adoptions_by_shelter_df_sort = adoptions_by_shelter_df.sort_values(by='Adoptions', ascending=False)
    st.write('Top', SuperShelter,'in' )    
    st.write(adoptions_by_shelter_df_sort[0:SuperShelter])
    
    mymap = folium.Map(location=[36.5, 127.5], zoom_start=6.5,tiles='cartodbpositron')
    Draw(export=True).add_to(mymap)   
    
    folium.GeoJson(
        gdf,
        style_function=lambda x: {
            'color': 'black',  # 경계선 색상을 초록색으로 설정
            'fillColor': 'white',
            'weight': 5 
        },
        name='geojson'
    ).add_to(mymap)    
    
    link_url = "https://www.karma.or.kr/human_boardA/animal_board.php?act=list&bid=animal"   
    
    for idx, row in filtered_data.iterrows():       
        tooltip_text = f"{row['careNm']} ({row['Adoptions']} 개 입양)"
        link_text = "Click here to visit Website"  # 링크 텍스트 설정
        popup_text = f"<div style='font-size: 8pt; font-weight: bold; width:200px; height: 60px;'>{row['careNm']}:<br> {row['Adoptions']}개<br><a href='{link_url}' target='_blank'>{link_text}</a></div>"
        tooltip_text = f"{row['careNm']} ({row['Adoptions']} 개 입양)"
        if option == "Good":
            icon = folium.Icon(color='blue', icon='smile', icon_color='white', prefix='fa')  
        elif option == "Bad":
            icon = folium.Icon(color='red', icon='frown', icon_color='white', prefix='fa')  
        else:
            icon = folium.Icon(color='green', icon='meh', icon_color='white', prefix='fa') 
        # 마커 추가
        folium.Marker(
            location=[row['lat'], row['lng']],
            popup=popup_text,
            tooltip = tooltip_text,
            icon=icon  
        ).add_to(mymap)         

    # 지도 출력
    folium_static(mymap)
st.sidebar.text("----------------------------------")
st.sidebar.text('산대특 시각화 프로젝트\n24년 3월 00일\n')
st.sidebar.text('권재현\n심재윤\n유동훈\n정예린')
st.sidebar.text("----------------------------------")
st.sidebar.text("데이터 출처:\n")







