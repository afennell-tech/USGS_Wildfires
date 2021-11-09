import streamlit as st 
import pandas as pd
import boto3

S3_BUCKET = 'usgswildfires'
FIRE_DATA_KEY = 'fire-data/clean_fpa_fod.csv'
ALL_YEARS = [y for y in {x.year for x in pd.date_range(start="1992", end="2018")}]


# initialize client to help fetch from aws s3 bucket containing dashboard data
@st.cache
def connect_to_s3():
    return boto3.client('s3')


def app(): 
    st.title('Welcome to the USGS Wildfires Dashboard!')
    st.write("Here is some insight on our dashboard and the data used to create it: ")
    st.markdown('The Fire Program Analysis fire-occurrence database (FPA FOD) contains a spatial database of wildfires that transpired from 1992 to 2018. This dataset contains over 2,166,753 fires over 26 years across 50 states. An estimated 164 million acres are recorded to have been burned in the process. The original dataset includes the District of Columbia (D.C) and Puerto Rico, however, this analysis has omitted those regions.')
    st.markdown('The core data elements present in the dataset are the date the fire was discovered, as well as the corresponding time if the information was available, the final fire size, as in the total acres burned, and the point location for the origin of the fire, represented using longitude and latitude.')
    st.markdown('This dashboard utilizes the geo-referenced wildfire records to create interactive maps, where users can toggle different locations, time frames, and fire sizes. We combined Amazon S3 Select with Python streamlit framework to allow for queries to be executed against the database in real-time. Displaying the geospatial component of the wildfire records provides an additional viewpoint for domain experts to analyze and interpret the data.')
    st.markdown('We hope you enjoy our dashboard and find it useful!')
    
    