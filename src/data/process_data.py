import os

# PACKAGE_PARENT = '..'
# SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
# sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from pathlib import Path
from shapely.geometry import Point
import pandas as pd
import geopandas as gpd
from tqdm import tqdm
tqdm.pandas()

# Global variables / Magic numbers
# CURR_PATH = str(Path(__file__).parent.resolve())
PROJ_PATH = str(Path(__file__).parent.resolve().parent.resolve().parent)
RAW_DATA_PATH = os.path.join(PROJ_PATH, 'data', 'raw') 
PROC_DATA_PATH = os.path.join(PROJ_PATH, 'data', 'processed')
DATA_CFG_PATH = os.path.join(PROJ_PATH, 'configs', 'data_cfg.ini')
CLEAN_CFG_PATH = os.path.join(PROJ_PATH, 'configs', 'proc_data_cfg.ini')

def insert_time(row):
    if len(row['DISCOVERY_TIME']) < 3:
        return row
    else:
        time = pd.to_datetime(row['DISCOVERY_TIME'], format='%H%M')
        row['DISCOVERY_DATE'] = row['DISCOVERY_DATE'].replace(hour=time.hour, minute=time.minute)
        return row

def fpa_fod_clean(in_df):
    # only keep specified columns
    out_df = in_df[
        ['FOD_ID', 'FIRE_YEAR', 'DISCOVERY_DATE', 'DISCOVERY_DOY', 
        'DISCOVERY_TIME', 'NWCG_CAUSE_CLASSIFICATION', 'NWCG_GENERAL_CAUSE',
        'FIRE_SIZE', 'FIRE_SIZE_CLASS', 'LATITUDE', 'LONGITUDE', 'STATE']
        ]
        
    # create a geometry columns with Point objects
    out_df = gpd.GeoDataFrame(out_df,geometry=gpd.points_from_xy(out_df.LONGITUDE, out_df.LATITUDE))
    out_df.drop(columns=['LONGITUDE', 'LATITUDE'], inplace=True)

    # process DISCOVERY_DATE feature
    out_df['DISCOVERY_TIME'] = out_df['DISCOVERY_TIME'].progress_apply(
        lambda v: str(v)[:-2] if (str(v) != 'nan') & (len(str(v)) > 2) else '0000')    
    out_df['DISCOVERY_DATE'] = pd.to_datetime(out_df['FIRE_YEAR']*1000 + out_df['DISCOVERY_DOY'], format='%Y%j')
    out_df = out_df.progress_apply(lambda row: insert_time(row), axis=1)
    out_df.drop(columns=['DISCOVERY_DOY', 'DISCOVERY_TIME'], inplace=True)

    # only use memory we need
    out_df[['FOD_ID', 'FIRE_YEAR']] = out_df[['FOD_ID', 'FIRE_YEAR']].progress_apply(
        pd.to_numeric, downcast="signed")
    out_df['FIRE_SIZE'] = pd.to_numeric(out_df['FIRE_SIZE'], downcast='float')
    out_df = out_df.astype({'NWCG_CAUSE_CLASSIFICATION':'category', 'NWCG_GENERAL_CAUSE':'category',
                       'FIRE_SIZE_CLASS':'category', 'STATE':'category'})

    # handle null values (trivial; there is only 1)
    out_df.dropna(subset=['NWCG_CAUSE_CLASSIFICATION'], inplace=True)

    # save file to correct location
    save_dir = os.path.join(PROC_DATA_PATH, 'fpa_fod')
    os.makedirs(save_dir, exist_ok=True)
    out_df.to_pickle(os.path.join(save_dir, 'clean_fpa_fod.pkl'))

    # delete the data/raw/fpa_fod dir for the user since processed data has been saved
    os.removedirs(os.path.join(RAW_DATA_PATH, 'fpa_fod'))

    return out_df 

func_map = {
    'fpa_fod_clean': fpa_fod_clean
}

def clean_dataset(in_df):
    pass

# if "__main__":
#     save_dir = os.path.join(PROC_DATA_PATH, 'fpa_fod')
#     df = pd.read_pickle(os.path.join(save_dir, 'clean_fpa_fod.pkl'))
#     df.to_pickle(os.path.join(save_dir, 'success.pkl'))