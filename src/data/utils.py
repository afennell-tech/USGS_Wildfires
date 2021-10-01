import os
from pathlib import Path

import sqlite3
from configparser import ConfigParser

import pandas as pd

# Global variables/Magic numbers; They are specific to the location of data_loading.py
PROJ_PATH = str(Path(__file__).parent.resolve().parent.resolve().parent)
DATA_CFG_PATH = os.path.join(PROJ_PATH, 'configs', 'data_cfg.ini')


def get_data_config(path=DATA_CFG_PATH) -> ConfigParser:
    """Returns a configParser that uses the dataset configuration file.
    """
    config = ConfigParser() # create
    config.read(path) # populate using corresponding file
    return config 


def get_sql_connection(sql_file): 
    """Returns a Connection object that represents the input db.
    """
    return sqlite3.connect(sql_file)


def get_table(table_name, conn):
    """Returns a df for table from Connection object.
    """
    print(f"Loading from sqlite database, this may take a while.")
    query = "Select * from {}".format(table_name)
    return pd.read_sql_query(query, conn)


def process_fpa_fod_time(df, cont=False):
    col = 'CONT_TIME' if cont else 'DISCOVERY_TIME'
    # convert to string so we can set the null values to '0000.0'
    df[col] = df[col].astype(str) 
    # null values are now the string 'nan'; get the index of these values
    index = df[df[col] == 'nan'].index
    # update the null values to '0000.0'
    df.loc[index, col] = '0000.0'
    # get the index of invalid time values
    index = df[df[col].str.len() < 5].index
    # update the invalid time values to '0000.0'
    df.loc[index, col] = '0000.0'
    return df

def insert_time_fpa_fod(row):
    time = pd.to_datetime(row['DISCOVERY_TIME'], format='%H%M')
    row['FIRE_DATE'] = row['FIRE_DATE'].replace(hour=time.hour, minute=time.minute)
    return row


def insert_time_fpa_fod_cont(row):
    time = pd.to_datetime(row['CONT_TIME'], format='%H%M')
    row['FIRE_CONT_DATE'] = row['FIRE_CONT_DATE'].replace(hour=time.hour, minute=time.minute)
    return row


def fire_size_class(row):
    """Bins fire_size (in acres) based on fpa_fod dataset splits
    """
    size = row['FIRE_SIZE']
    if 0 < size <= 0.25: 
        return 'A'
    if 0.25 < size < 10:
        return 'B'
    if 10 <= size < 100: 
        return 'C'
    if 100 <= size < 300: 
        return 'D'
    if 300 <= size < 1000: 
        return 'E'
    if 1000 <= size < 5000: 
        return 'F'
    if 5000 < size: 
        return 'G'