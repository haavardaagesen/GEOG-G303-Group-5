#!/usr/bin/env python
# coding: utf-8

# In[ ]:


# import necessary plugins

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString, Polygon


# In[ ]:


point_fp = (r"C:\Users\Alisa\Downloads\points_from2017.gpkg")

points = gpd.read_file(point_fp)


# In[ ]:


points


# In[ ]:


home_munc = (r"C:\Users\Alisa\Documents\Finnish_twitter_users_municipalities_by_uweeks_per_user.csv")

finnish_user = gpd.read_file(home_munc)


# In[ ]:


finnish_user


# In[ ]:


# complete a preliminary visualization of the points
get_ipython().run_line_magic('matplotlib', 'inline')
points.plot()


# In[ ]:


points.crs


# In[ ]:


# determine the type of the data in the column user_id for both dataframes
selection = finnish_user['user_id'].loc[1]

selection1 = points['user_id'].loc[1]

print(type(selection))
print(type(selection1))


# In[ ]:


# Because the user_id columns are different data types we must convert one before we conduct a join

finnish_user['user_id'] = finnish_user['user_id'].astype('int64')

finnish_user


# In[ ]:


join1 = finnish_user.merge(points, on='user_id')

join1


# In[ ]:


type(join1)


# In[ ]:


join1.drop('geometry_x', axis=1, inplace=True)

join1.rename(columns={"geometry_y": "geometry"}, inplace=True)

join1


# In[ ]:


# next we will need to further simplify our data by isolating only unique users
print(join1["user_id"].nunique())

join1 = join1.drop_duplicates(subset = ["user_id"])

join1


# In[ ]:


from geopandas import GeoDataFrame
# In joining the two dataframes, the points lost their geodataframe status so we must reassert that
type(join1)

crs = {'init': 'epsg:4326'}
gdf_join = GeoDataFrame(join1, crs=crs, geometry=join1['geometry'])

gdf_join


# In[ ]:


get_ipython().run_line_magic('matplotlib', 'inline')
import matplotlib.pyplot as plt

# Plot a map displaying home municipalities of users
fig, ax = plt.subplots(figsize=(8,12))

# Isolate the home municipality
gdf_join.plot(ax = ax, column = 'home_municipality')


# Currently the map displays the location of the geo-tagged tweet, color-coded with the home municipality of the user behind that tweet. Next we want to figure out how many users are actually from each municipality and conduct a visualization of number of users of each municipality. Finally, we will display the user movements by displaying which municipalities they tend to visit with different maps displaying each municipality's trends. 

# In[ ]:


import random

gdf_join['home_municipality'].unique()
gdf_join.groupby('home_municipality').home_municipality.count()
matching = [s for s in gdf_join['home_municipality'] if " or " in s]


for i in gdf_join['home_municipality']:
    if i in matching:
        cities = i.split(' or ')
        user_city = cities[random.randint(0, 1)]
        gdf_join.replace(to_replace=i, value=user_city, inplace=True)
        

gdf_join


# In[ ]:


region_fp = (r"C:\Users\Alisa\Documents\SuomenMaakuntajako_2018_10k.dbf")

#read in the appropriate dataframes
regions = gpd.read_file(region_fp)


# In[ ]:


regions


# In[ ]:


regions.crs
gdf_join = gdf_join.to_crs({'init': 'epsg:3067'})


# In[ ]:


# Make a copy because I'm going to drop points as I assign them to polys, to speed up subsequent search.
pts = gdf_join.copy() 

# We're going to keep a list of how many points we find.
pts_in_polys = []

# Loop over polygons with index i.
for i, poly in regions.iterrows():

    # Keep a list of points in this poly
    pts_in_this_poly = []

    # Now loop over all points with index j.
    for j, pt in pts.iterrows():
        if poly.geometry.contains(pt.geometry):
            # Then it's a hit! Add it to the list,and drop it so we have less hunting.
            pts_in_this_poly.append(pt.geometry)
            pts = pts.drop([j])

    # Append the number of points to the list
    pts_in_polys.append(len(pts_in_this_poly))

# Add the number of points for each poly to the dataframe.
regions['number of points'] = gpd.Series(pts_in_polys)

regions


# In[ ]:


gdf_join


# In[ ]:


# Determine the output path for the Shapefile
outfp = (r"C:\Users\Alisa\Documents\Finnish_users_geom_muncipalities_1.shp")

# Write the data into that Shapefile
gdf_join.to_file(outfp)


# In[ ]:




