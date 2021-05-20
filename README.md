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

### Initial conda environment setup:
0. Download [miniconda](https://docs.conda.io/en/latest/miniconda.html) or [anaconda](https://www.anaconda.com/products/individual#Downloads) if necessary.
- Run `conda --version` to verify that conda is installed and running on your system
- If you get an error message, make sure you closed and re-opened the terminal window after installing, or do it now. Then verify that you are logged into the same user account that you used to install Anaconda or Miniconda. 
2. Navigate to the **USGS_Wildfires** directory on your local machine (see **Setting up git locally** if needed).
- If using a **Windows** machine, search for and open "Anaconda Prompt" from the Start menu
4. Run `conda env create -f environment.yml` to create a new conda environment for this project.
- The **environment.yml** file should already be in the current working directory after cloning the git repo.
- To see your different conda environments run `conda info --envs`.
5. Run `conda activate usgs_wildfires_env` to activate the environment for this project.
6. Run `python -m ipykernel install --user --name=usgs_wildfires_env` to add the conda environment to jupyter.
7. Run `jupyter lab` to open the project directory in jupyterlab. Be sure to use the **usgs_wildfires_env** kernel so that python uses the proper environment when executing code. 
8. If you wish to deactivate the conda environment, run `conda deactivate usgs_wildfires_env`. You may choose to do this at the end of a coding/work session.

The conda [getting started](https://conda.io/projects/conda/en/latest/user-guide/getting-started.html#starting-conda) documentation can also be helpful if needed. 

### After conda environment setup: 
1. Assuming the conda environment has already been setup correctly, only the following steps from **Initial conda environment setup** should be executed for a new coding/work session: 
- Navigate to proper directory (**Step 2**)
- Activate environment (**Step 5**)
- Open jupyterlab (**Step 7**)
- Deactviate environment upon finishing the session (**Step 8**)
