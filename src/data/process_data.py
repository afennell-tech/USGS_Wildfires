import os

# PACKAGE_PARENT = '..'
# SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
# sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from pathlib import Path
import shutil

import pandas as pd
import geopandas as gpd
from tqdm import tqdm
tqdm.pandas()

from src.data.utils import insert_time_fpa_fod, insert_time_fpa_fod_cont
from src.data.utils import process_fpa_fod_time, fire_size_class

# Global variables / Magic numbers
# CURR_PATH = str(Path(__file__).parent.resolve())
PROJ_PATH = str(Path(__file__).parent.resolve().parent.resolve().parent)
RAW_DATA_PATH = os.path.join(PROJ_PATH, 'data', 'raw') 
PROC_DATA_PATH = os.path.join(PROJ_PATH, 'data', 'processed')
DATA_CFG_PATH = os.path.join(PROJ_PATH, 'configs', 'data_cfg.ini')
CLEAN_CFG_PATH = os.path.join(PROJ_PATH, 'configs', 'proc_data_cfg.ini')


def clean_fpa_fod(in_df, *args):
    # check if we should drop (specified) columns; otherwise, keeps all columns in original in_df
    drop_cols = False if 'keep_cols' in args else True

    if drop_cols: 
        # only keep specified columns
        out_df = in_df[
            ['FIRE_YEAR', 'DISCOVERY_DATE', 'DISCOVERY_DOY', 
            'DISCOVERY_TIME', 'CONT_DATE', 'CONT_DOY', 'CONT_TIME',
            'NWCG_CAUSE_CLASSIFICATION', 'NWCG_GENERAL_CAUSE', 'FIRE_SIZE', 
            'FIRE_SIZE_CLASS', 'LATITUDE', 'LONGITUDE', 'STATE',
            'COUNTY', 'FIPS_CODE', 'FIPS_NAME']
        ]
    else:   
        out_df = in_df

    # create a geometry column with Point objects
    print('Creating a geometry column with Point objects ...')
    out_df = gpd.GeoDataFrame(out_df,geometry=gpd.points_from_xy(out_df.LONGITUDE, out_df.LATITUDE))
    # always drop LONG and LAT after creating the xy point
    out_df.drop(columns=['LONGITUDE', 'LATITUDE'], inplace=True) 

    # enforce common naming convention for specific columns
    out_df.rename( 
        columns=
        {
            'NWCG_GENERAL_CAUSE': 'SPECIFIC_CAUSE',
            'NWCG_CAUSE_CLASSIFICATION': 'GENERAL_CAUSE',
            'DISCOVERY_DATE': 'FIRE_DATE',
            'CONT_DATE': 'FIRE_CONT_DATE'
        }, 
        inplace=True
    )

    # only use memory we need 
    out_df['FIRE_YEAR'] = out_df['FIRE_YEAR'].progress_apply(
        pd.to_numeric, downcast="unsigned")
    out_df['FIRE_SIZE'] = pd.to_numeric(out_df['FIRE_SIZE'], downcast='float')
    
    # Handle null values in `DISCOVERY_TIME` before proceeding with processing `FIRE_DATE` feature
    print("Handling null values in DISCOVERY_TIME ...")
    out_df = process_fpa_fod_time(out_df)
    # Handle null values in `CONT_TIME` before proceeding with processing `FIRE_CONT_DATE` feature
    print("Handling null values in CONT_TIME ...")
    out_df = process_fpa_fod_time(out_df, cont=True)

    # Fill the null values in `CONT_DOY` with a nonsensical value, `400.0`
    #   - allows the column to be properly converted to int
    out_df = out_df.fillna(value={'CONT_DOY': 400.0})
    out_df['CONT_DOY'] = pd.to_numeric(out_df['CONT_DOY'], downcast='integer')

    # handle edge case where `CONT_DOY` is less than `DISCOVERY_DOY`
    print("Creating a temporary column for FIRE_CONT_YEAR ...")
    index = out_df[out_df['DISCOVERY_DOY'].astype(int) > out_df['CONT_DOY'].astype(int)].index
    out_df['FIRE_CONT_YEAR'] = out_df['FIRE_YEAR'].astype(int)
    out_df.loc[index, 'FIRE_CONT_YEAR'] = out_df.loc[index, 'FIRE_CONT_YEAR'].astype(int) + 1

    # convert columns to string before applying to_datetime function
    out_df = out_df.astype({
        'FIRE_YEAR': 'str', 
        'FIRE_CONT_YEAR': 'str',
        'DISCOVERY_DOY': 'str', 
        'CONT_DOY': 'str'
    })
    # process date of fire
    print("Processing date of fire ...")
    out_df['FIRE_DATE'] = pd.to_datetime(
        out_df['FIRE_YEAR'] + ' ' + out_df['DISCOVERY_DOY'], format='%Y %j', utc=True)
    # process date of fire (contained)
    print("Processing date of fire (contained) ...")
    out_df['FIRE_CONT_DATE'] = pd.to_datetime(
        out_df['FIRE_CONT_YEAR'] + ' ' + out_df['CONT_DOY'], format='%Y %j',
        utc=True, errors='coerce')
    # remove the .0 so that the times are in correct %H%M format
    out_df['DISCOVERY_TIME'] = out_df['DISCOVERY_TIME'].str[:-2]
    out_df['CONT_TIME'] = out_df['CONT_TIME'].str[:-2]
    # process time of fire
    print("Finally, processing time of fire ...")
    out_df = out_df.progress_apply(lambda row: insert_time_fpa_fod(row), axis=1)
    # process time of fire (contained)
    print("Finally, processing time of fire (contained) ...")
    out_df = out_df.progress_apply(lambda row: insert_time_fpa_fod_cont(row), axis=1)
    # always drop YEAR, DOY and TIME after processing
    out_df.drop(columns=['DISCOVERY_DOY', 'DISCOVERY_TIME', 'CONT_DOY',
                        'CONT_TIME', 'FIRE_YEAR', 'FIRE_CONT_YEAR'], inplace=True)

    # handle other null values (trivial)
    out_df.fillna({'GENERAL_CAUSE': 'Missing data/not specified/undetermined'}, inplace=True)

    # convert respective classes to category type
    for col in ['GENERAL_CAUSE', 'SPECIFIC_CAUSE', 'FIRE_SIZE_CLASS', 'STATE']:
        out_df[col] = out_df[col].astype('category')

    # since `FIRE_DATE` is nicely formatted and has *datetime64 dtype*, use it as the index of the df
    #   - sorting the index allows for better data slicing
    print("Setting the index to the FIRE_DATE column ...")
    out_df = out_df.set_index('FIRE_DATE').sort_index()

    # save file to correct location
    save_dir = os.path.join(PROC_DATA_PATH, 'fpa_fod')
    os.makedirs(save_dir, exist_ok=True)
    save_file = 'clean_fpa_fod.pkl' if drop_cols else 'clean_fpa_fod_all.pkl'
    out_df.to_pickle(os.path.join(save_dir, save_file))

    # delete the data/raw/fpa_fod dir for the user since processed data has been saved
    if os.path.isdir(os.path.join(RAW_DATA_PATH, 'fpa_fod')):
        delete_raw = input('Would you like to delete the raw data used for processing the fpa_fod dataset (y/[n])?')
        if delete_raw == 'y':
            print('Removing the data/raw/fpa_fod directory now ...')
            shutil.rmtree(os.path.join(RAW_DATA_PATH, 'fpa_fod'))
        else: 
            print('The raw data will remain in the data/raw/fpa_fod directory')

    return out_df 


map_val_to_cause = {
    1: 'Lightning', 
    2: 'Equipment Use', 
    3: 'Smoking', 
    4: 'Campfire', 
    5: 'Debris', 
    6: 'Railroad', 
    7: 'Arson', 
    8: 'Playing with Fire', 
    9: 'Miscellaneous', 
    10: 'Vehicle', 
    11: 'Power Line', 
    12: 'Firefighter Training', 
    13: 'Non-Firefighter Training',
    14: 'Unknown/Unidentified', 
    15: 'Structure', 
    16: 'Aircraft', 
    17: 'Volcanic', 
    18: 'Escaped Prescribed Burn', 
    19: 'Illegal Alien Campfire'
}

map_val_to_fpa_fod_cause = {
    1: 'Natural', 
    2: 'Equipment and vehicle use',
    3: 'Smoking',
    4: 'Recreation and ceremony', 
    5: 'Debris and open burning', 
    6: 'Railroad operations and maintenance', 
    7: 'Arson/incendiarism', 
    8: 'Misuse of fire by a minor', 
    9: 'Other causes', 
    10: 'Equipment and vehicle use', 
    11: 'Power generation/transmission/distribution',
    12: 'Other causes', 
    13: 'Other causes', 
    14: 'Missing data/not specified/undetermined',
    15: 'Other causes',
    16: 'Other causes',
    17: 'Natural',
    18: 'Other causes',
    19: 'Recreation and ceremony',
}

map_val_to_c_method = {
    1: 'GPS Ground', 
    2: 'GPS Air', 
    3: 'Infrared',      
    4: 'Other Imagery', 
    5: 'Photo Interpretation',
    6: 'Hand Drawn', 
    7: 'Mixed Collection Methods',
    8: 'Unknown'
}

map_val_to_objective = {
    0: 'Unknown', 
    1: 'Suppression', 
    2: 'Resource Benefit'
}

def clean_ca_fire_perimeters(in_df, *args):
    # check if we should drop (specified) columns; otherwise, keeps all columns in original in_df
    drop_cols = False if 'keep_cols' in args else True      

    if drop_cols: 
        # drop the specified columns 
        out_df = in_df.drop(columns=['CONT_DATE', 'COMMENTS', 'REPORT_AC', 'FIRE_NUM'])

    # always drop STATE since we assume all fires are in CA only
    out_df.drop(columns=['STATE'], inplace=True)

    # enforce common naming convention for specific columns
    out_df.rename(
        columns=
        {
            'YEAR_':'FIRE_YEAR',
            'CAUSE':'SPECIFIC_CAUSE',
            'GIS_ACRES': 'FIRE_SIZE'
        }, 
        inplace=True
    )

    # put fire sizes into same bins used in fpafod
    out_df['FIRE_SIZE_CLASS'] = out_df['FIRE_SIZE']
    out_df['FIRE_SIZE_CLASS'] = out_df['FIRE_SIZE_CLASS'].progress_apply(fire_size_class)

    # map values to classes/categories as needed
    out_df['C_METHOD'] = out_df['C_METHOD'].replace(map_val_to_c_method)
    out_df['SPECIFIC_CAUSE_ORIG'] = out_df['SPECIFIC_CAUSE'].replace(map_val_to_cause)
    out_df['SPECIFIC_CAUSE'] = out_df['SPECIFIC_CAUSE'].replace(map_val_to_fpa_fod_cause)
    out_df['OBJECTIVE'] = out_df['OBJECTIVE'].replace(map_val_to_objective)

    # only use memory we need 
    out_df[['FIRE_YEAR']] = out_df[['FIRE_YEAR']].progress_apply(
        pd.to_numeric, downcast="signed")
    out_df[['FIRE_SIZE', 'Shape_Length', 'Shape_Area']] =  \
        out_df[['FIRE_SIZE', 'Shape_Length', 'Shape_Area']].progress_apply(
            pd.to_numeric, downcast='float'
        )
    out_df = out_df.astype({'SPECIFIC_CAUSE':'category', 'SPECIFIC_CAUSE_ORIG':'category',
                            'C_METHOD':'category', 'OBJECTIVE':'category', 
                            'FIRE_SIZE_CLASS':'category'})

    # process FIRE_DATE feature
    out_df['FIRE_DATE'] = out_df['FIRE_DATE'].str.replace('T00:00:00+00:00', '', regex=False)
    # setting utc=True allows for FIRE_DATE to have type datetime64[ns] (not entirely sure as to why)
    out_df['FIRE_DATE'] = pd.to_datetime(
        out_df['FIRE_DATE'], errors='coerce', infer_datetime_format=True, utc=True)

    # handle null values
    # dropping values
    out_df.dropna(
        subset=['AGENCY', 'FIRE_YEAR', 'UNIT_ID', 'FIRE_NAME', 'FIRE_DATE',
                'INC_NUM', 'ALARM_DATE', 'GIS_ACRES', 'FIRE_SIZE_CLASS'], 
        inplace=True
    )
    # filling values
    out_df['C_METHOD'].fillna('Unknown', inplace=True)
    out_df['SPECIFIC_CAUSE'].fillna('Unknown/Unidentified', inplace=True)
    
    # drop rows from earlier than 1950
    out_df['FIRE_YEAR'] = out_df[['FIRE_YEAR']].progress_apply(
        pd.to_numeric, downcast="signed")

    # save file to correct location
    save_dir = os.path.join(PROC_DATA_PATH, 'ca_fire_perimeters', 'firep')
    os.makedirs(save_dir, exist_ok=True)
    save_file = 'clean_firep.pkl' if drop_cols else 'clean_firep_all.pkl'
    out_df.to_pickle(os.path.join(save_dir, save_file))

    # delete the data/raw/fpa_fod dir for the user since processed data has been saved
    # if os.path.isdir(os.path.join(RAW_DATA_PATH, 'fpa_fod')):
    #     os.removedirs(os.path.join(RAW_DATA_PATH, 'fpa_fod'))

    return out_df 


def clean_dataset(in_df):
    pass

# if "__main__":
#     save_dir = os.path.join(PROC_DATA_PATH, 'fpa_fod')
#     df = pd.read_pickle(os.path.join(save_dir, 'clean_fpa_fod.pkl'))
#     df.to_pickle(os.path.join(save_dir, 'success.pkl'))