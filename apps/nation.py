import streamlit as st 
import pandas as pd
import geopandas as gpd
import boto3


from bokeh.plotting import figure
from bokeh.models import  LinearColorMapper, ColumnDataSource
from bokeh.palettes import Inferno256 as palette

from src.app.helper import get_MultiPoly, subset_fire_data, plot_sim_animation

# ...

S3_BUCKET = 'usgswildfires'
FIRE_DATA_KEY = 'fire-data/clean_fpa_fod.csv'
STATE_KEY = 'shapefile/state.zip'
CONTIG_STATE_KEY = 'shapefile/contiguous-state.zip'
ALL_YEARS = [y for y in {x.year for x in pd.date_range(start="1992", end="2018")}]


# initialize client to help fetch from aws s3 bucket containing dashboard data
@st.cache(allow_output_mutation=True)
def connect_to_s3():
    return boto3.client('s3')

@st.cache
def load_boundary_data():
    state = gpd.read_file(f"zip+s3://{S3_BUCKET}/{STATE_KEY}")
    contig_state = gpd.read_file(f"zip+s3://{S3_BUCKET}/{CONTIG_STATE_KEY}")
    return state, contig_state

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
    state_df, contig_state_df = load_boundary_data()
    st.write('Below is a simulation of all fires in the US. '
            'Be warned! This simulation takes anywhere from 5 - 10 minutes to fully execute due to the '
            'due to the size of the dataset.')

    # Simulation using all contiguous states
    st.write('Click `Begin` to vizualize wildfires over the entire contiguous United States from 1992 to 2018.')
    start_sim_button = st.button('Begin')
    sim = figure(title="Fires by Year Simulation",match_aspect=True,aspect_ratio=2)
    sim_plot = st.empty()
    N = len(contig_state_df)
    select_year_source = ColumnDataSource({ 
                'x': [get_MultiPoly(contig_state_df.iloc[i]['geometry'],'x') for i in range(0,N)],
                'y': [get_MultiPoly(contig_state_df.iloc[i]['geometry'],'y') for i in range(0,N)],
                'n': [i for i in range(0,N)],
                'state':[contig_state_df.iloc[i]['NAME'] for i in range(0,N)],
                })

    # add maps, but without any fires plotted on top
    sim.multi_polygons(xs='x',ys='y', source=select_year_source,
                    fill_color={'field': 'n', 'transform': LinearColorMapper(palette=palette,low=0,high=len(select_year_source.data['x']))},
                    fill_alpha=0.5, line_color="black", line_width=0.5)
    sim_plot.bokeh_chart(sim)
    
    sim_progress = st.empty()
    # run simulation across years as desired by user
    if(start_sim_button):
        for year in ALL_YEARS: 
            # st.write(year)
            # st.write(tuple([year, None]))
            year_df = load_fire_data(s3_cli=s3, years=tuple([year, None]))
            if year_df.shape[0] != 0:
                plot_sim_animation(year_df, bokeh_fig=sim, st_fig=sim_plot)
                sim_progress.info(f'Wildfire data from {year} has been plotted!')
        sim_progress.empty()

   