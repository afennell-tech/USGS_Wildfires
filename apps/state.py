import streamlit as st 
import datetime

import pandas as pd
import geopandas as gpd
import numpy as np
import wordcloud
from PIL import Image

from bokeh.plotting import figure
from bokeh.models import  LinearColorMapper, ColumnDataSource
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
    st.write('Use the sliders and selection boxes below to query the data. '
        'Check out the resulting graphics for a deeper look into the specified data.')

    col1, col2, col3 = st.columns([3,1,3]) 

    # play around with "Input widgets" - selectbox
    with col2: 
        selected_state = st.selectbox("State", np.unique(county_df.STUSPS.values).tolist(), index=4)
    
    st.write(f'Selected State is {selected_state}')

    # get years from data to use for the select_slider choices
    # play around with "Input widgets" - select_slider
    selected_years = st.select_slider(label='Range of Years', options=ALL_YEARS,
                                value=(ALL_YEARS[0], ALL_YEARS[-1]))
    
    # filter years
    select_fires_df = load_fire_data(s3_cli=s3, years=tuple([selected_years[0], selected_years[1]]))

    st.write(f'Range of months is {selected_years[0]} to {selected_years[1]}')
    month_names = select_fires_df.index.month_name().unique().tolist()
    # play around with "Input widgets" - select_slider
    selected_months = st.select_slider(label='Range of Months', options=month_names,
                                value=(month_names[0], month_names[-1]))
    
    # get unique months from data to use for the select_slider choices
    sorted_months = [datetime.date(1900, x, 1).strftime('%B') 
                     for x in sorted(select_fires_df.index.month.unique().tolist())]
    first_month, last_month = selected_months
    first_month_idx = sorted_months.index(first_month)
    last_month_idx = sorted_months.index(last_month) + 1

    # filter by months
    select_fires_df = select_fires_df[select_fires_df.index.month_name().isin(sorted_months[first_month_idx:last_month_idx])]
    
    st.write(f'Range of months is {selected_months[0]} to {selected_months[1]}')

    # get unique fire size class from data to use for the select_slider choices
    fire_size_classes = sorted(select_fires_df.FIRE_SIZE_CLASS.values.unique().tolist())
    # get input from slider
    selected_fs_class = st.select_slider(label='Range of Fire Size Classes', options=fire_size_classes, 
                                        value=(fire_size_classes[0], fire_size_classes[-1]))

    # create endpoints and indices
    left_endpoint, right_endpoint = selected_fs_class
    begin_ind = fire_size_classes.index(left_endpoint)
    end_ind = fire_size_classes.index(right_endpoint) + 1

    # filter by fire size class
    select_fires_df = select_fires_df[select_fires_df.FIRE_SIZE_CLASS.isin(
                                        fire_size_classes[begin_ind: end_ind])]

    st.write(f'Selected Range of Fire Size Classes is {left_endpoint} to {right_endpoint}')

    # prepare data used for plotting states
    select_state_county_df = county_df[county_df.values == selected_state]
    select_fires_df = select_fires_df[select_fires_df.values == selected_state]

    # st.write(select_state_county_df)

    # prepare x,y points for p.circle
    # st.write(select_fires_df)
    fires_by_state_xs = select_fires_df.geometry.values.x
    fires_by_state_ys = select_fires_df.geometry.values.y

    # prepare x,y points for p.multi_polygons
    N=len(select_state_county_df) 
    select_county_source = ColumnDataSource({ 
        'x': [get_MultiPoly(select_state_county_df.iloc[i]['geometry'],'x') for i in range(0,N)],
        'y': [get_MultiPoly(select_state_county_df.iloc[i]['geometry'],'y') for i in range(0,N)],
        'n': [i for i in range(0,N)],
        'county':[select_state_county_df.iloc[i]['NAME'] for i in range(0,N)],
        })

    # create first figure object to use for plotting states
    p = figure(title="Fires by State",match_aspect=True,aspect_ratio=1)
    # create plot for county layer
    p.multi_polygons(xs='x',ys='y', source=select_county_source,
            fill_color={'field': 'n', 'transform': LinearColorMapper(palette=palette,low=0,high=len(select_county_source.data['x']))},
            fill_alpha=0.5, line_color="black", line_width=0.5)
    # create plot for fire location points
    p.circle(fires_by_state_xs, fires_by_state_ys, size=5, color='red')

    # plot on dashboard
    # st.write(show(p))
    with col3: 
        st.bokeh_chart(p, use_container_width=True)

# selected_state_boundary_df = state_df[state_df.values == selected_state]
# st.write(selected_state_boundary_df.astype('object'))
# state_boundaries = gv.Polygons(selected_state_boundary_df.geometry)
# st.write(show(hv.render(state_boundaries, backend='bokeh')))

    # group by class of fire size
    grouped_data = select_fires_df.groupby(['FIRE_SIZE_CLASS']).size()
    with col1: 
        st.write('Fire Class Counts for ' + selected_state)
        st.bar_chart(grouped_data)

    # # top 5 most frequent county and top 5 most safe county
    # df_last = select_fires_df.groupby('COUNTY').size().sort_values()[-5:]
    # last_5 = pd.DataFrame({'county': df_last.index, 'fire count': df_last.to_list()})#.index.tolist()
    # df_fst = select_fires_df.groupby('COUNTY').size().sort_values()[:5]
    # first_5 = pd.DataFrame({'county': df_fst.index, 'fire count': df_fst.to_list()})

    # col1, col2 = st.columns(2)

    # with col1:
    #     st.title(f'Counties with least frequent fires {selected_state} during the selected time slot')
    #     st.dataframe(first_5)

    # with col2:
    #     st.title(f'Counties with most frequent fires in State {selected_state} during the selected time slot')
    #     st.dataframe(last_5)
        
    # freqs = dict(select_fires_df.SPECIFIC_CAUSE.apply(lambda x: x.strip().split('/')[0]).value_counts())
    
    cause_counts = select_fires_df.SPECIFIC_CAUSE.apply(lambda x: x.strip().split('/')[0]).value_counts()
    counts = cause_counts.values
    causes = cause_counts.index
    df_temp = pd.DataFrame({'Fire general causes': causes, 'counts': counts})
    st.write('\n')
    cola, colb = st.columns([3, 2])
    with colb:
        st.write('Top 6 fire causes')
        st.table(df_temp.head(6))
    freqs = dict(cause_counts)
    wc = wordcloud.WordCloud(max_font_size=30, background_color="white").fit_words(freqs).to_array()
    image = Image.fromarray(wc)
    with cola:
        st.image(image, width=None)
        st.write(f'Word cloud for State {selected_state} in the selected time span')