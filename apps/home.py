import streamlit as st 
import pandas as pd
import boto3

S3_BUCKET = 'usgswildfires'
FIRE_DATA_KEY = 'fire-data/clean_fpa_fod.csv'
ALL_YEARS = [y for y in {x.year for x in pd.date_range(start="1992", end="2018")}]


# initialize client to help fetch from aws s3 bucket containing dashboard data
@st.cache(allow_output_mutation=True)
def connect_to_s3():
    return boto3.client('s3')


def app(): 
    st.title('Home')
    st.write("This is a sample home page in the mutliapp.")
    st.write("See `apps/home.py` to know how to contribute.")