import os
from pathlib import Path
from src.data.process_data import fpa_fod_clean
import wget 
import zipfile
from configparser import ConfigParser

import pandas as pd
import geopandas as gpd
import fiona
import sqlite3

from  .process_data import fpa_fod_clean

# Global variables/Magic numbers; They are specific to the location of data_loading.py
PROJ_PATH = str(Path(__file__).parent.resolve().parent.resolve().parent)
RAW_DATA_PATH = os.path.join(PROJ_PATH, 'data', 'raw') 
PROC_DATA_PATH = os.path.join(PROJ_PATH, 'data', 'processed')
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

# FIXME This will be changed; for now, only loads the fpa_fod (ie from kaggle) dataset
def load_processed_dataset(dataset):

    if dataset != 'fpa_fod':
        print(f"{dataset} does not have any processing methods. Use load_raw_datasets() instead.")
        return None 

    data_cfg = get_data_config()
    # dataset_path = os.path.join(PROC_DATA_PATH, *data_cfg[key][descr].split(','))
    dataset_path = os.path.join(PROC_DATA_PATH, *data_cfg[dataset]['clean'].split(','))
    if not os.path.exists(dataset_path):
        # create the processed dataset to continue with loading 
        dfs, _ = load_raw_datasets(dataset)
        clean_df = fpa_fod_clean(dfs[0])
    else: 
        clean_df = pd.read_pickle(dataset_path)
    
    return clean_df

# FIXME set raw=False once data processing scripts are complete
# def fetch_datasets(*args, raw=True):
#     # ensure the data/raw and data/processed directories exist
#     os.makedirs(RAW_DATA_PATH, exist_ok=True) 
#     os.makedirs(PROC_DATA_PATH, exist_ok=True)

#     if raw: 
#         print("\n Loading raw datasets \n")
#         return load_raw_datasets(args)
#     else: 
#         print("\n Loading processed datasets \n")
#         return load_processed_datasets(args)


# def load_processed_datasets(**kwargs):
#     """TODO add docstring

#     Arguments: 
#         kwargs: For k,v in kwargs.items(), k must be the name of a raw dataset, and 
#                 v should be the description of the processed dataset. The value of v 
#                 will be used as the key to find the file path from the data config file.
#     """
#     # first, we need to check if the processed dataset exists
#     df_list = []
#     df_names = []
#     data_cfg = get_data_config()

#     for key, descr in kwargs.items():
#         dataset_path = os.path.join(PROC_DATA_PATH, *data_cfg[key][descr].split(','))
#         # _, fname = os.path.split(dataset_path)
#         # fname, ext = tuple(fname.split('.'))
#         # ext = '.' + ext
#         if not os.path.exists(dataset_path):
#             # create the processed dataset to continue with loading 
#             create_processed_dataset(key)
#     # if it doesn't, then pass respective dataset into `create_processed_dataset()`
#     # else, 
#     pass


# def create_processed_dataset(dataset):
#     raw_dfs, df_names = load_raw_datasets(dataset)
#     proc_dfs = []
#     # process each raw df in the list
#     for df in raw_dfs: 
#         proc_dfs.append(clean_dataset(df))

#     return proc_dfs

#     config['Trained Model Details']={'model_file_name' :'classfication_epoch100.h5'}
#     with open(filename, 'w') as configfile:
#         config.write(configfile)
    

def load_raw_datasets(*args):
    """TODO add docstring

    Arguments: 
        args: Each arg in args must be the name of a raw dataset
    """
    df_list = []
    df_names = []
    data_cfg = get_data_config()

    for arg in args:
        dataset_path = os.path.join(RAW_DATA_PATH, *data_cfg['Raw Paths'][arg].split(','))
        _, fname = os.path.split(dataset_path)
        fname, ext = tuple(fname.split('.'))
        ext = '.' + ext
        if not os.path.exists(dataset_path):
            # download dataset in order to continue with loading 
            download_raw_datasets(arg)
        # use geopandas if .gdb file (geodatabase)
        if ext == '.gdb':
            layers = fiona.listlayers(dataset_path)
            if len(layers) == 0: 
                print(f'\n The .gdb file contains 0 layers, so {fname} will not be loaded \n')
                continue 

            elif len(layers) == 1: 
                print(f"\n Loading {fname} \n")
                df_list.append(gpd.read_file(dataset_path))
                df_names.append(fname.strip(ext))

            else: 
            # file contains multiple layers, so prompt user to specify what layers to load
                print(f'\n {fname} has the following layers: \n {layers} \n')
                keep_layers = input('What layers you would like to keep? Enter the layer names with 1 space '
                                    'in between, or enter `all` to load all layers. \n')
                if keep_layers == 'all' or keep_layers == '`all`':
                    keep_layers = layers 
                else: 
                    keep_layers = keep_layers.split(' ')
                # load each layer
                for i, layer in enumerate(keep_layers): 
                    df_layer = fname.strip(ext) + f'_{layer}'
                    print(f"\n Loading {df_layer} \n")
                    df_list.append(gpd.read_file(dataset_path, layer=i))
                    df_names.append(df_layer)

        elif ext == '.sqlite':
            print(f"\n Loading {fname} \n")
            df_list.append(get_table(data_cfg[ext][arg], 
                                        get_sql_connection(dataset_path)))
            df_names.append(fname.strip(ext))

    print(f"The list of dfs contains the following datasets (in this order): \n {df_names}")
    return df_list, df_names
    

def download_raw_datasets(*args):
    """Docstring TODO here.

    Longer description TODO here.
    
    """
    data_urls = subset_raw_datasets(args)
    downloaded_files = {} # keys=dataset_name, values=list containing the file names extracted after unzipping
    # use wget to download all urls in data_urls (the values)
    for name, url in data_urls.items():
        dataset_path = os.path.join(RAW_DATA_PATH, name)
        download = False
        try:
            os.makedirs(dataset_path)
        except FileExistsError:
            dir = os.listdir(dataset_path) # getting the list of directories
            if len(dir) != 0:
                print(f'\n {os.path.join(RAW_DATA_PATH, name)} is an existing directory and is not empty. \n'
                    f'This suggests the original {name} dataset has been downloaded in the past.')
                still_download = input(f"Do you want to re-download the original {name} dataset (y/[n])?")
                if still_download == 'y':
                    download = True
                elif still_download == 'n':
                    continue # move to next selected dataset, or terminate if last entry
            # directory is empty, so download the zipfile; no need to ask
            else: 
                download = True
        else: 
            download = True
        finally: 
            if download: 
                os.chdir(dataset_path)
                print(f"\n Downloading {name} to {dataset_path} directory")
                zip_name = f"{name}.zip"
                wget.download(url, zip_name) # file download
                with zipfile.ZipFile(zip_name, 'r') as zip_ref:
                    downloaded_files[name] = zip_ref.infolist()
                    zip_ref.extractall()
                os.remove(zip_name) # delete zip file after it is unzipped

    print("\n Done downloading \n")
    return [key for key in data_urls.keys()]
                

def delete_raw_datasets(): 
    """potential function: use to delete raw datasets if user chooses after they have 
    been properly processed/prepared + saved locally for future access; they can redownload 
    raw data again if needed, but won't be using it; it's just a waste of space then!
    """
    pass


# should i make one function to subset datasets? add keyword argument to indicate raw/processed? LATER ON
def subset_raw_datasets(args):
    """Docstring TODO here.

    Longer description TODO here.
    
    """
    data_cfg = get_data_config()
    available_urls = dict(data_cfg['Datasets'].items())
    desired_urls = {} 
    # if all datasets are desired, no subsetting necessary
    if 'all' in args:
        print(f"\n Selected datasets: {[key for key in available_urls.keys()]} \n")
        return available_urls
    # parse provided input arguments and retrieve the corresponding url, if possible.
    for arg in args:
        # infinite loop is okay; we want to continuously prompt user
        while(True):
            if arg in available_urls:
                desired_urls[arg] = available_urls[arg]
                break
            # prompt user 
            else: 
                print(f'\n {arg} is not an available dataset. Here are the remaining datasets to choose from:')
                # print_available_datasets() <- too much output
                print(f'\n{[k for k,v in available_urls.items() if k not in desired_urls.keys()]}')
                arg = input('\n Please re-enter the correct name of the dataset '
                                'you wish to download, or simple type C to skip this entry. \n')
                if arg == 'C':
                    break
    print(f"\n Selected datasets: {[key for key in desired_urls.keys()]} \n")
    return desired_urls


def print_available_datasets():
    """Prints info on all available datasets.
    
    Retrieves and prints all keys from the [Datasets] section in data_cfg.ini.
    For each key, the corresponding value from the [Descriptions] section is 
    also printed to provide a specific description of each dataset.
    """
    data_cfg = get_data_config()
    print("The available datasets are: \n")
    for idx, key in enumerate(data_cfg['Datasets'], 1):  
        print(f"{idx}.) {key}\n- {data_cfg['Descriptions'][key]} \n")

# if "__main__":
    # pass
    # print_available_datasets()
    # datasets = download_raw_datasets('all')
    # print(datasets)
    # subset_available_datasets()
    # datasets = fetch_datasets('ca_fire_perimeters') 
    # print()
    # pass