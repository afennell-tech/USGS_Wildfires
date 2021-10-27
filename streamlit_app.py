import streamlit as st
import pandas as pd
import geopandas as gpd

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

@st.cache(allow_output_mutation=True)
def load_fire_data():
    fire_df = pd.read_pickle('data/clean_fpa_fod.pkl')
    return fire_df

# load boundary data for map plots on first run
state_df, county_df, div_df = load_boundary_data()
# load fire related dataset on first run
fire_df = load_fire_data().copy()

choice = st.selectbox('ex', [0,1])
choice_dict = {
    0: fire_df.index.year[0],
    1: fire_df.index.year[1] 
}
st.write(choice_dict[choice])
# x = st.slider('Year', fpa_fod.index.year[0], fpa_fod.index.year[-1])
# st.write('x={x}')
# val = st.date_input('year of fire', fpa_fod.index.year[0])
# st.write(f'val is {val}')
# fpa_fod = pd.read_pickle('data/clean_fpafod.pkl')
# first_five = fpa_fod[0:5]
# st.write(first_five.astype('object'))
# st.dataframe(data=fpa_fod)