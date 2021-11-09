import streamlit as st 

import pandas as pd
import geopandas as gpd


from bokeh.plotting import figure
from bokeh.palettes import Inferno256 as palette

import boto3

from src.app.helper import get_MultiPoly, subset_fire_data

# ...

S3_BUCKET = 'usgswildfires'
FIRE_DATA_KEY = 'fire-data/clean_fpa_fod.csv'
COUNTY_KEY = 'shapefile/county.zip'
ALL_YEARS = [y for y in {x.year for x in pd.date_range(start="1992", end="2018")}]

# initialize client to help fetch from aws s3 bucket containing dashboard data
@st.cache(allow_output_mutation=True)
def connect_to_s3():
    return boto3.client('s3')


@st.cache
def load_boundary_data():
    county = gpd.read_file(f"zip+s3://{S3_BUCKET}/{COUNTY_KEY}")
    return county

@st.cache(hash_funcs={tuple: id, pd.DataFrame: lambda _: None}, ttl=60*10, max_entries=6) # FIXME need to debug caching with s3
def load_fire_data(s3_cli, years):
        if isinstance(years, tuple):
            # s_yr = years[0].astype('int') if not isinstance(years[0], int) and years[0] is not None else None
            # e_yr = years[1].astype('int') if not isinstance(years[1], int) and years[1] is not None else None
            s_yr = years[0]
            e_yr = years[1]
            # st.write(s_yr)
            # st.write(e_yr)
            out_df = subset_fire_data(s3_cli, S3_BUCKET, FIRE_DATA_KEY, start_year=s_yr, end_year=e_yr)
            return out_df
            
def app():
    # both will be stored in cache
    s3 = connect_to_s3()
    county_df = load_boundary_data()
    col1, col2 = st.columns([2,1])
    season_candidates = ['Spring', 'Summer', 'Fall', 'Winter']
    st.write('Note: Given that the start of a season varies by year, \
    we are considering the start of each season to be a fixed time.')
    st.write('i.e. Spring starts by 3/21, Summer starts by 6/21, Fall starts by 9/23, Winter starts by 12/20 (to 3/20 next year)')
    with col1:
        selected_years_new = st.select_slider(label='Range of Years for a season', options=ALL_YEARS,
                                value=(ALL_YEARS[-2], ALL_YEARS[-1]))

    with col2:
        selected_season = st.selectbox("Season", season_candidates, index=0)
    
#     st.write(selected_years_new)
    def get_season(Y, season):
        seasons = [('Winter', [(pd.Timestamp(year = Y, month = 1,  day = 1, tz = 'UTC'),  pd.Timestamp(year = Y, month = 3,  day = 20, tz = 'UTC')), (pd.Timestamp(year = Y, month = 12,  day = 21, tz = 'UTC'),  pd.Timestamp(year = Y, month = 12,  day = 31, tz = 'UTC'))]),
                   ('Spring', [(pd.Timestamp(year = Y, month = 3,  day = 21, tz = 'UTC'),  pd.Timestamp(year = Y, month = 6,  day = 20, tz = 'UTC'))]),
                   ('Summer', [(pd.Timestamp(year = Y, month = 6,  day = 21, tz = 'UTC'),  pd.Timestamp(year = Y, month = 9,  day = 22, tz = 'UTC'))]),
                   ('Fall', [(pd.Timestamp(year = Y, month = 9,  day = 23, tz = 'UTC'),  pd.Timestamp(year = Y, month = 12,  day = 20, tz = 'UTC'))])]
        list_of_time = dict(seasons)[season]
        return list_of_time
    
    # 
    def get_subset(selected_years_new, selected_season):
        all_times = []
        for year in range(selected_years_new[0], selected_years_new[-1]+1):
            all_times.extend(get_season(year, selected_season))
            
#         st.write(all_times)
#         st.write([type(x) for x in all_times[0]])
        tf_ser = pd.Series(df_for_season.index).apply(lambda x: any([k[0] <= x <= k[1] for k in all_times]))
#         st.dataframe(tf_ser)
        df = df_for_season[list(tf_ser)]
#         st.dataframe(df_for_season[list(tf_ser)].drop(columns=['geometry'], inplace = True))
        return df_for_season[list(tf_ser)]
    
    
    df_for_season = load_fire_data(s3_cli=s3, years=tuple([selected_years_new[0], selected_years_new[-1]]))
#     st.write(selected_years_new)
#     st.write(df_for_season.shape)
#     st.write(df_for_season.index.year.unique().tolist())
    colx, coly, colz = st.columns(3)
    with colx:
        colors = ['b','b','b','b']
        all_seasons = ['Spring', 'Summer', 'Fall', 'Winter']
        idx = all_seasons.index(selected_season)
        colors[idx] = 'r'
        count_dict = {
            'Spring': 0,
            'Winter': 0,
            'Summer': 0,
            'Fall': 0
        }
        for i in df_for_season.index:
            if i.month <=2 or (i.month == 3 and i.day <= 20) or (i.month == 12 and i.day >= 21):
                count_dict['Winter'] += 1
            elif (i.month >= 3 and i.month <6) or (i.month == 6 and i.day <=20):
                count_dict['Spring'] += 1
            elif (i.month >= 6 and i.month < 9) or (i.month == 9 and i.day <= 22):
                count_dict['Summer'] += 1
            else:
                count_dict['Fall'] += 1
        import matplotlib.pyplot as plt
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.barh(all_seasons, list(count_dict.values()), color = colors)
        ax.set_title('Total count of fires for the four seasons')
        ax.set_xlabel('fire counts')
        ax.set_ylabel('seasons')
        st.pyplot(fig)
        
    seasoned_df = get_subset(selected_years_new, selected_season)
    with coly:
        grouped_by_year = seasoned_df.groupby(seasoned_df.index.year).size()
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.plot(list(grouped_by_year.index), grouped_by_year)
        ax.set_title('Count of fires over a specific period of time in a season')
        ax.set_xlabel('time')
        ax.set_ylabel('count of fires')
        st.pyplot(fig)
#     st.table(grouped_by_year)
        
    with colz:
        grouped_by_class = seasoned_df.groupby(seasoned_df.FIRE_SIZE_CLASS).size()
        st.bar_chart(grouped_by_class)