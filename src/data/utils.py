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


def insert_time_fpa_fod(row):
    if len(row['DISCOVERY_TIME']) < 3:
        return row
    else:
        time = pd.to_datetime(row['DISCOVERY_TIME'], format='%H%M')
        row['DISCOVERY_DATE'] = row['DISCOVERY_DATE'].replace(hour=time.hour, minute=time.minute)
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