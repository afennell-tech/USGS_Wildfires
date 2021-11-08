import boto3
import pandas as pd
import geopandas as gpd
import numpy as np
from io import StringIO
from shapely.geometry.polygon import Polygon
# from shapely.geometry.multipolygon import MultiPolygon

# function credit: https://stackoverflow.com/questions/60201306/bokeh-patches-not-loading-multipolygons-with-cds
def get_MultiPoly(mpoly,coord_type='x'):
    """Returns the coordinates ('x' or 'y') for the exterior and interior of MultiPolygon digestible by multi_polygons in Bokeh"""
    
    if coord_type == 'x':
        i=0
    elif coord_type == 'y':
        i=1
    
    # Get the x or y coordinates
    c = [] 
    if isinstance(mpoly,Polygon):
        mpoly = [mpoly]
    for poly in mpoly: # the polygon objects return arrays, it's important they be lists or Bokeh fails
        exterior_coords = poly.exterior.coords.xy[i].tolist();
        
        interior_coords = []
        for interior in poly.interiors:
            if isinstance(interior.coords.xy[i],list):
                interior_coords += [interior.coords.xy[i]];
            else:
                interior_coords += [interior.coords.xy[i].tolist()];
        c.append([exterior_coords, *interior_coords])
    return c


def plot_sim_animation(df, bokeh_fig, st_fig):
    #convert lon/lat to x, y coords and add to figure
    fires_group_xs = df.geometry.values.x
    fires_group_ys = df.geometry.values.y
    
    bokeh_fig.circle(fires_group_xs, fires_group_ys, size=1, color='red')
    st_fig.bokeh_chart(bokeh_fig) #show figure for given year


def subset_fire_data(session, bucket, key, start_year=None, end_year=None, state=None, only_contig=True):
    query = ''
    if start_year is not None and end_year is not None:
        start_year = start_year.astype('int') if not isinstance(start_year, int) else start_year
        end_year = end_year.astype('int') if not isinstance(end_year, int) else end_year
        # query by year range
        query = f"""SELECT FIRE_DATE, \"FIRE_CONT_DATE\", \"GENERAL_CAUSE\", \"SPECIFIC_CAUSE\",
                      \"FIRE_SIZE\", \"FIRE_SIZE_CLASS\", \"STATE\", \"geometry\"
                    FROM s3object 
                    WHERE CAST(\"YEAR\" AS INT) >= {start_year} AND CAST(\"YEAR\" AS INT) <= {end_year}"""
    elif start_year is None or end_year is None:
        single_year = start_year if start_year is not None else end_year
        single_year = single_year.astype('int') if not isinstance(single_year, int) else single_year

        if only_contig:
            where_cond = f"""WHERE CAST(\"YEAR\" AS INT) = {single_year} 
                                    AND \"STATE\" NOT LIKE 'HI'
                                    AND \"STATE\" NOT LIKE 'AK'
                                    AND \"STATE\" NOT LIKE 'DC'
                                    AND \"STATE\" NOT LIKE 'PR'"""
        else: 
            where_cond = f"""WHERE CAST(\"YEAR\" AS INT) = {single_year}"""
        # query by year
        query = f"""SELECT FIRE_DATE, \"FIRE_CONT_DATE\", \"GENERAL_CAUSE\", \"SPECIFIC_CAUSE\",
                      \"FIRE_SIZE\", \"FIRE_SIZE_CLASS\", \"STATE\", \"geometry\"
                    FROM s3object 
                    {where_cond}"""
    elif state is not None: 
        query = f"""SELECT FIRE_DATE, \"FIRE_CONT_DATE\", \"GENERAL_CAUSE\", \"SPECIFIC_CAUSE\",
                  \"FIRE_SIZE\", \"FIRE_SIZE_CLASS\", \"STATE\", \"geometry\"
                    FROM s3object 
                    WHERE \"STATE\" LIKE '{state}'"""
    resp = session.select_object_content(
        Bucket=bucket,
        Key=key,
        ExpressionType='SQL',
        Expression=query,
        InputSerialization = {'CSV': {"FileHeaderInfo": "Use"}},
        OutputSerialization = {'CSV': {}},
    )

    records = [] 
    for event in resp['Payload']:
        if 'Records' in event:
            records.append(event['Records']['Payload'])

    # converting the byte strings to strings and then joining them together
    # to form one large string
    file_str = ''.join(r.decode('utf-8') for r in records)
    # doing StringIO(file_str) so it looks like CSV file to pd.read_csv()
    select_df = pd.read_csv(StringIO(file_str), 
                       names=['FIRE_DATE', 'FIRE_CONT_DATE', 'GENERAL_CAUSE', 'SPECIFIC_CAUSE', 'FIRE_SIZE', 
                              'FIRE_SIZE_CLASS', 'STATE', 'geometry'])
    
    # fix DATE columns
    select_df['FIRE_DATE'] = pd.to_datetime(select_df['FIRE_DATE'])
    select_df['FIRE_CONT_DATE'] = pd.to_datetime(select_df['FIRE_CONT_DATE'])

    # fix CATEGORICAL columns
    for col in ['GENERAL_CAUSE', 'SPECIFIC_CAUSE', 'FIRE_SIZE_CLASS', 'STATE']:
        select_df[col] = select_df[col].astype('category')

    # fix NUMERIC columns 
    select_df['FIRE_SIZE'] = pd.to_numeric(select_df['FIRE_SIZE'], downcast='unsigned')
    # select_df['LON'] = pd.to_numeric(select_df['LON'], downcast='float')
    # select_df['LAT'] = pd.to_numeric(select_df['LAT'], downcast='float')

    # fix GEOMETRY column
    select_df['geometry'] = gpd.GeoSeries.from_wkt(select_df['geometry'])
    # select_geo_df = gpd.GeoDataFrame(select_df, geometry='geometry')

    # make DATETIME index
    select_df = select_df.set_index('FIRE_DATE').sort_index()
    
    return select_df