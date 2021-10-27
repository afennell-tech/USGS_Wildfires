import streamlit as st
import pandas as pd
import geopandas as gpd

FIRE_DATA = 'data/subset.pkl'
st.write('Our dashboard starts here!')
# st.slider('ex', 1992, 2018,)

# Load shapefiles for state, county and division ("regions")
# state_df = gpd.read_file('data/state')
# county_df = gpd.read_file('data/county')
# div_df = gpd.read_file('data/division')

@st.cache
def load_boundary_data():
    state = gpd.read_file('data/state')
    county = gpd.read_file('data/county')
    div = gpd.read_file('data/division')
    return state, county, div

@st.cache
def load_fire_data():
    fire_df = pd.read_pickle(FIRE_DATA)
    return fire_df

# load boundary data for map plots on first run
state_df, county_df, div_df = load_boundary_data()
# load fire related dataset on first run
# fire_df = load_fire_data()
fire_df = load_fire_data()

state = st.selectbox("State", fire_df.STATE.values.unique(), index=0)
st.write(f'state:{state}')
min_val = 0
max_val = int(fire_df.FIRE_SIZE.max())
fire_size = st.slider(label="Range of Fire Size", value=(min_val, max_val))
st.write(f'fire size: {fire_size}')
# st.write(choice_dict[choice])
# x = st.slider('Year', fpa_fod.index.year[0], fpa_fod.index.year[-1])
# st.write('x={x}')
# val = st.date_input('year of fire', fpa_fod.index.year[0])
# st.write(f'val is {val}')
# fpa_fod = pd.read_pickle('data/clean_fpafod.pkl')
# first_five = fpa_fod[0:5]
# st.write(first_five.astype('object'))
# st.dataframe(data=fpa_fod)