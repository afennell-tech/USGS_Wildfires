import streamlit as st
import pandas as pd

import geoviews as gv
import holoviews as hv
from bokeh.plotting import show, figure
from bokeh.models import  MultiPolygons, ColorMapper, LinearColorMapper, ColumnDataSource
from bokeh.palettes import Inferno256 as palette
from bokeh.layouts import row, column

import geopandas as gpd
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon
# from bokeh.io import show, output_file
import matplotlib.pyplot as plt

# constants HERE
FIRE_DATA = 'data/subset.pkl'

# set page config and layout
st.set_page_config(layout='wide')

# helper message
st.write('Our dashboard starts here!')

@st.cache
def load_boundary_data():
    state = gpd.read_file('data/state')
    county = gpd.read_file('data/county')
    div = gpd.read_file('data/division')
    return state, county, div

@st.cache
def load_fire_data():
    fires_df = pd.read_pickle(FIRE_DATA)
    return fires_df

# HELPER FUNCTIONS NEED TO BE MOVED TODO !!!
# function credit: https://stackoverflow.com/questions/60201306/bokeh-patches-not-loading-multipolygons-with-cds
def get_MultiPoly(mpoly,coord_type='x'):
    """Returns the coordinates ('x' or 'y') for the exterior and interior of MultiPolygon digestible by multi_polygons in Bokeh"""
    
    if coord_type == 'x':
        i=0
    elif coord_type == 'y':
        i=1
    
    # Get the x or y coordinates
    c = [] 
    if isinstance(mpoly,Polygon):
        mpoly = [mpoly]
    for poly in mpoly: # the polygon objects return arrays, it's important they be lists or Bokeh fails
        exterior_coords = poly.exterior.coords.xy[i].tolist();
        
        interior_coords = []
        for interior in poly.interiors:
            if isinstance(interior.coords.xy[i],list):
                interior_coords += [interior.coords.xy[i]];
            else:
                interior_coords += [interior.coords.xy[i].tolist()];
        c.append([exterior_coords, *interior_coords])
    return c

# load boundary data for map plots on first run
state_df, county_df, div_df = load_boundary_data()
# load fire related dataset on first run
fires_df = load_fire_data()

col1, col2, col3 = st.columns([3,1,3]) 

# play around with "Input widgets" - selectbox
with col2: 
    selected_state = st.selectbox("State", fires_df.STATE.values.unique(), index=0)
    st.write(f'Selected State is {selected_state}')

# define values for slider
# min_val = 0
# max_val = int(fires_df.FIRE_SIZE.max())
# play around with "Input widgets" - slider
# min_fire_size, max_fire_size = st.slider(label="Range of Fire Size", value=(min_val, max_val))
# st.write(f'Selected Range of Fire Size is {min_fire_size} to {max_fire_size}')

# get unique months from data to use for the select_slider choices
month_names = fires_df.index.month_name().unique().tolist()
# play around with "Input widgets" - select_slider
selected_months = st.select_slider(label='Range of Months', options=month_names,
                            value=(month_names[0], month_names[-1]))
st.write(f'Range of months is {selected_months[0]} to {selected_months[-1]}')

# get unique fire size class from data to use for the select_slider choices
fire_size_classes = sorted(fires_df.FIRE_SIZE_CLASS.values.unique().tolist())
# get input from slider
selected_fs_class = st.select_slider(label='Range of Fire Size Classes', options=fire_size_classes, 
                                     value=(fire_size_classes[0], fire_size_classes[-1]))
# create endpoints and indices
left_endpoint, right_endpoint = selected_fs_class
begin_ind = fire_size_classes.index(left_endpoint)
end_ind = fire_size_classes.index(right_endpoint)
st.write(f'Selected Range of Fire Size Classes is {left_endpoint} to {right_endpoint}')

# prepare data used for plotting states
select_state_county_df = county_df[county_df.values == selected_state]
select_fires_df = fires_df[fires_df.values == selected_state]

# filter by months
select_fires_df = select_fires_df[select_fires_df.index.month_name().isin(selected_months)]

# IF WE WANTED TO filter by fire size, numerically
# select_fires_df = select_fires_df.loc[select_fires_df.FIRE_SIZE > min_fire_size]
# select_fires_df = select_fires_df.loc[select_fires_df.FIRE_SIZE < max_fire_size]
# filter by fire size class
select_fires_df = select_fires_df[select_fires_df.FIRE_SIZE_CLASS.isin(
                                    fire_size_classes[begin_ind: end_ind])]
st.dataframe(select_fires_df.FIRE_SIZE_CLASS.value_counts())

# prepare x,y points for p.circle
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
    st.bar_chart(grouped_data)

# top 5 most frequent county and top 5 most safe county
df_last = select_fires_df.groupby('COUNTY').size().sort_values()[-5:]
last_5 = pd.DataFrame({'county': df_last.index, 'fire count': df_last.to_list()})#.index.tolist()
df_fst = select_fires_df.groupby('COUNTY').size().sort_values()[:5]
first_5 = pd.DataFrame({'county': df_fst.index, 'fire count': df_fst.to_list()})

col1, col2 = st.columns(2)

with col1:
    st.title(f'Counties with least frequent fires {selected_state} during the selected time slot')
    st.dataframe(first_5)

with col2:
    st.title(f'Counties with most frequent fires in State {selected_state} during the selected time slot')
    st.dataframe(last_5)