#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Functions script
# Import modules
import glob
import os
import pandas as pd
import geopandas as gpd
import contextily as ctx
import matplotlib.pyplot as plt
from pyproj import CRS
from datetime import datetime, timedelta


def mergeTweetsWithMunicipality(tweetsWithLocale, municipalities):
    # Loading tweets data with home location of users
    users = gpd.read_file(tweetsWithLocale)
    # Loading Finland municipalities
    finland = gpd.read_file(municipalities)
    old_crs = finland.crs
    # Aligning CRS
    finland = finland.to_crs(users.crs)
    # Merging user data by municipality
    merged = gpd.sjoin(finland, users, how='inner', op='contains')
    # Removing finns tweeting in home municipality
    bef = len(merged)
    merged = merged[merged['NAMEFIN'] != merged['home_municipality']]
    aft = len(merged)
    print(f'Finns tweeting in home municipality dropped: {bef-aft}')
    print(f'New number of tweets in dataset:{aft}')
    merged['date'] = pd.to_datetime(merged['created_at'])
    # Add YearMonth for easier slicing later
    merged['YR'] = merged['date'].dt.year
    merged['MN'] = merged['date'].dt.month
    merged['YearMonth'] = merged['date'].map(lambda x: 100 * x.year + x.month)
    return merged


def foreignerOrFinn(tw_data, finland):
    """ Output a dataframe with number of Finns and Foreigners that have tweeted in each polygon."""
    old_crs = finland.crs
    grouped = tw_data.groupby('NAMEFIN')
    # Make copy of Finland dataset
    foreignersOrFinns = finland.copy()
    # Adding columns for visitors
    foreignersOrFinns['foreigners'] = 0
    foreignersOrFinns['finns_visiting'] = 0
    # Finding number of user groups
    for key, group in grouped:
        # Count number of users
        identified_users = group['homeLoc'].count()
        # Find number of users per country
        countries = group['homeLoc'].value_counts()
        # Find finnish users
        finns = int(countries[0])
        # Subtract finns from total
        foreigners = int(identified_users - finns)
        # Set values for each group
        foreignersOrFinns.loc[foreignersOrFinns['NAMEFIN']
                              == key, ['finns_visiting']] = finns
        foreignersOrFinns.loc[foreignersOrFinns['NAMEFIN']
                              == key, ['foreigners']] = foreigners

    # Change to plotting CRS
    foreignersOrFinns = foreignersOrFinns.to_crs(old_crs)
    return foreignersOrFinns


def dissolveToRegions(municipalityData, regions):
    municipalityData = municipalityData.to_crs(regions.crs)
    regions.crs == municipalityData.crs
    merged = gpd.sjoin(regions, municipalityData, how='inner', op='contains')
    return merged


def twitterComparisonFinnsForeigners(filenames, labels):
    i = 0
    quant = ['Less than 20%', '20-40%', '40-60%', '60-80%', 'More than 80%']
    for season in filenames:
        # Only files that end with '.gpkg'
        full_path = 'regions_seasons/' + season + '.gpkg'
        # Read file to geoDataFrame
        df = gpd.read_file(full_path)
        df = df.to_crs('epsg:3067')
        df['foreigners'] = df['foreigners'].astype(int)
        df['finns_visiting'] = df['finns_visiting'].astype(int)
        fig, axes = plt.subplots(ncols=2, figsize=(12, 10))
        ax11 = axes[0]
        ax12 = axes[1]
        # Visualize the travel times into 9 classes using "Quantiles" classification scheme
        df.plot(ax=ax11, column="finns_visiting", linewidth=0.03, cmap="YlOrRd",
                legend=True, scheme="quantiles", k=5, alpha=1, legend_kwds={'loc': 'upper left'})
        ax11.set_title('Finns')
        df.plot(ax=ax12, column="foreigners", linewidth=0.03, cmap="YlOrRd", legend=True,
                scheme="quantiles", k=5, alpha=1, legend_kwds={'loc': 'upper left'})
        ax12.set_title('Foreigners')
        ax11.axis('off')
        ax12.axis('off')
        leg11 = ax11.get_legend()
        #for text, label in zip(leg11.get_texts(), quant):
            #text.set_text(label)
        leg12 = ax12.get_legend()
        #for text, label in zip(leg12.get_texts(), quant):
            #text.set_text(label)
        tit = 'Visitors by Region \n Twitter Users - ' + labels[i]
        fig.suptitle(tit)
        # Remove the empty white-space around the axes
        # plt.tight_layout()
        outfp = "maps/tw_Finn_Foreigners_" + labels[i] + ".png"
        i += 1
        plt.savefig(outfp, dpi=600)
        plt.show()


def finnsTwitterOfficial(regional_names, official_data, labels, finland_fp):
    i = 0
    quant = ['Less than 20%', '20-40%', '40-60%', '60-80%', 'More than 80%']
    official_df = gpd.read_file(official_data)
    official_df = official_df.to_crs('epsg:3067')
    finland_finns = gpd.read_file(finland_fp)
    finland_finns = finland_finns.to_crs('epsg:3067')
    official_df['ID'] = official_df['ID'].astype(int)
    finland_finns['NATCODE'] = finland_finns['NATCODE'].astype(int)
    finland_finns = finland_finns.merge(
        official_df, left_on='NATCODE', right_on='ID')
    official_df = finland_finns.copy()
    official_df = official_df.rename(columns={'geometry_x': 'geometry'})
    official_df = official_df.drop('geometry_y', axis=1)
    official_df = official_df.set_geometry('geometry')
    for season in regional_names:
        # Only files that end with '.gpkg'
        full_path = 'regions_seasons/' + season + '.gpkg'
        # Read file to geoDataFrame
        df = gpd.read_file(full_path)
        df = df.to_crs('epsg:3067')
        #df['foreigners'] = df['foreigners'].astype(int)
        df['finns_visiting'] = df['finns_visiting'].astype(int)
        fig, axes = plt.subplots(ncols=2, figsize=(12, 10))
        ax11 = axes[0]
        ax12 = axes[1]
        # Visualize the travel times into 9 classes using "Quantiles" classification scheme
        df.plot(ax=ax11, column="finns_visiting", linewidth=0.03, cmap="YlOrRd",
                legend=True, scheme="quantiles", k=5, alpha=1, legend_kwds={'loc': 'upper left'})
        ax11.set_title('Twitter Users')
        official_column = str(official_df.columns[i + 8])
        # print(official_column)
        official_df.plot(ax=ax12, column=official_column, linewidth=0.03, cmap="YlOrRd",
                         legend=True, scheme="quantiles", k=5, alpha=1, legend_kwds={'loc': 'upper left'})
        ax12.set_title('Official Statistics')
        ax11.axis('off')
        ax12.axis('off')
        leg11 = ax11.get_legend()
        #for text, label in zip(leg11.get_texts(), quant):
            #text.set_text(label)
        leg12 = ax12.get_legend()
        #for text, label in zip(leg12.get_texts(), quant):
            #text.set_text(label)
        tit = 'Finnish Visitors by Region \n ' + labels[i]
        fig.suptitle(tit)
        # plt.tight_layout()
        outfp = 'maps/TW_vs_Official_Finns_' + labels[i] + '.png'
        plt.savefig(outfp, dpi=600)
        i += 1
        plt.show()


def foreignersTwitterOfficial(regional_names, official_data, labels, finland_fp):
    i = 0
    quant = ['Less than 20%', '20-40%', '40-60%', '60-80%', 'More than 80%']
    official_df = gpd.read_file(official_data)
    official_df = official_df.to_crs('epsg:3067')

    official_df['ID'] = official_df['ID'].astype(int)
    finland_foreigners = gpd.read_file(finland_fp)
    finland_foreigners = finland_foreigners.to_crs('epsg:3067')
    finland_foreigners['NATCODE'] = finland_foreigners['NATCODE'].astype(int)
    finland_foreigners = finland_foreigners.merge(
        official_df, left_on='NATCODE', right_on='ID')
    official_df = finland_foreigners.copy()
    official_df = official_df.rename(columns={'geometry_x': 'geometry'})
    official_df = official_df.drop('geometry_y', axis=1)
    official_df = official_df.set_geometry('geometry')
    for season in regional_names:
        # Only files that end with '.gpkg'
        full_path = 'regions_seasons/' + season + '.gpkg'
        # Read file to geoDataFrame
        df = gpd.read_file(full_path)
        df = df.to_crs('epsg:3067')
        #df['foreigners'] = df['foreigners'].astype(int)
        df['finns_visiting'] = df['finns_visiting'].astype(int)
        fig, axes = plt.subplots(ncols=2, figsize=(12, 10))
        ax11 = axes[0]
        ax12 = axes[1]
        # Visualize the travel times into 9 classes using "Quantiles" classification scheme
        df.plot(ax=ax11, column="foreigners", linewidth=0.03, cmap="YlOrRd", legend=True,
                scheme="quantiles", k=5, alpha=1, legend_kwds={'loc': 'upper left'})
        ax11.set_title('Twitter Users')
        official_column = str(official_df.columns[i + 8])
        official_df.plot(ax=ax12, column=official_column, linewidth=0.03, cmap="YlOrRd",
                         legend=True, scheme="quantiles", k=5, alpha=1, legend_kwds={'loc': 'upper left'})
        ax12.set_title('Official Statistics')
        ax11.axis('off')
        ax12.axis('off')
        leg11 = ax11.get_legend()
        #for text, label in zip(leg11.get_texts(), quant):
            #text.set_text(label)
        leg12 = ax12.get_legend()
        #for text, label in zip(leg12.get_texts(), quant):
            #text.set_text(label)
        tit = 'Foreign Visitors by Region \n - ' + labels[i]
        fig.suptitle(tit)
        # plt.tight_layout()
        outfp = 'maps/TW_vs_Official_Foreigners_' + labels[i] + '.png'
        plt.savefig(outfp, dpi=600)
        i += 1
        plt.show()


def officialComparison(official_finns, official_foreigners, labels, finland_fp):
    i = 0
    quant = ['Less than 20%', '20-40%', '40-60%', '60-80%', 'More than 80%']
    official_finns = gpd.read_file(official_finns)

    official_finns = official_finns.to_crs('epsg:3067')
    official_finns['ID'] = official_finns['ID'].astype(int)
    finland_finns = gpd.read_file(finland_fp)
    finland_finns = finland_finns.to_crs('epsg:3067')

    finland_finns['NATCODE'] = finland_finns['NATCODE'].astype(int)
    finland_foreigners = finland_finns.copy()
    finland_finns = finland_finns.merge(
        official_finns, left_on='NATCODE', right_on='ID')
    official_finns = finland_finns.copy()
    official_finns = official_finns.rename(columns={'geometry_x': 'geometry'})
    official_finns = official_finns.drop('geometry_y', axis=1)
    official_finns = official_finns.set_geometry('geometry')

    official_foreigners = gpd.read_file(official_foreigners)
    official_foreigners = official_foreigners.to_crs('epsg:3067')
    official_foreigners['ID'] = official_foreigners['ID'].astype(int)
    finland_foreigners['NATCODE'] = finland_foreigners['NATCODE'].astype(int)
    finland_foreigners = finland_foreigners.merge(
        official_foreigners, left_on='NATCODE', right_on='ID')
    official_foreigners = finland_foreigners.copy()
    official_foreigners = official_foreigners.rename(
        columns={'geometry_x': 'geometry'})
    official_foreigners = official_foreigners.drop('geometry_y', axis=1)
    official_foreigners = official_foreigners.set_geometry('geometry')
    for label in labels:
        fig, axes = plt.subplots(ncols=2, figsize=(12, 10))
        ax11 = axes[0]
        ax12 = axes[1]
        official_finns_column = str(official_finns.columns[i + 8])
        # Visualize the travel times into 9 classes using "Quantiles" classification scheme
        official_finns.plot(ax=ax11, column=official_finns_column, linewidth=0.03, cmap="YlOrRd",
                            legend=True, scheme="quantiles", k=5, alpha=1, legend_kwds={'loc': 'upper left'})
        ax11.set_title('Finnish visitors')
        official_foreigners_column = str(official_foreigners.columns[i + 8])
        official_foreigners.plot(ax=ax12, column=official_foreigners_column, linewidth=0.03, cmap="YlOrRd",
                                 legend=True, scheme="quantiles", k=5, alpha=1, legend_kwds={'loc': 'upper left'})
        ax12.set_title('Foreign visitors')
        ax11.axis('off')
        ax12.axis('off')
        leg11 = ax11.get_legend()
        #for text, label in zip(leg11.get_texts(), quant):
            #text.round(0)
            #print(text)
            #print(type(text))
            #text.set_text(text.round(0))
        leg12 = ax12.get_legend()
        #for text, label in zip(leg12.get_texts(), quant):
            #text.set_text(label)
        tit = 'Visitors by Reigion \n Official statistics - ' + \
            labels[i]
        fig.suptitle(tit)
        outfp = 'maps/Official_Finns_Foreigners_' + labels[i] + '.png'
        plt.savefig(outfp, dpi=600)
        i += 1
        plt.show()
