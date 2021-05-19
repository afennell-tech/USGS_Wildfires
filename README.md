# USGS_Wildfires

## See below for help getting started: 

### Setting up git locally:
0. On your local machine, open the terminal and navigate to the directory you plan to store this repository in.
1. Clone the git repository with the following: `git clone https://github.com/afennell-tech/USGS_Wildfires.git`.
- This will create a new directory titled USGS_Wildfires inside of the current directory.
- Run `cd USGS_Wildfires` to navigate into the directory and `ls` to view what it contains.
2. Run `mkdir data` to create a directory to store the data.
3. Click [here](https://drive.google.com/file/d/1sdfNJyBJ6jOEdY8QqayVqwXGMGV9rV0Z/view?usp=sharing) to download the data file created in [Data_Preparation.ipynb](https://github.com/afennell-tech/USGS_Wildfires/blob/main/Data_Preparation.ipynb).
- Notice that within the linked notebook, the data file used is titled **FPA_FOD_20170508.sqlite**. This file contains the spatial database of wildfires that occurred in the United States from 1992 to 2015 from [this](https://www.kaggle.com/rtatman/188-million-us-wildfires) Kaggle competition and if interested, the zip file can be downloaded by clicking [here](https://www.kaggle.com/rtatman/188-million-us-wildfires/download).
- **Note:** The csv file is a subset of the **Fires** table from the original database and only contains 10 columns (the original table contains 39 columns).
4. Move the downloaded file, **fires_df.csv**, into the data folder that we created in step 2. From the **USGS_Wildfires** directory, type `ls data` to ensure the csv file is now stored in the correct location.  
