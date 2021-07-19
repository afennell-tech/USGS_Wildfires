### Utilizing data_utils.py inside a jupyter notebook
```
# import the module
from src.data import data_utils
# view available datasets and corresponding descriptions
data_utils.print_available_datasets()
# download dataset (s) and follow prompts; input is *args
# Usage: data_utils.download_raw_datasets(dataset_1, ...)
# Ex. to download the fpa_fod and ca_fire_perimeters datasets
data_utils.download_raw_datasets('fpa_fod', 'ca_fire_perimeters')