import streamlit as st
import numpy as np
import folium
from streamlit_folium import folium_static
import pandas as pd
import geopandas as gpd

df = pd.read_csv("broadband_survey.csv")
df = df.loc[df["state_code"] == 37]
primaryColor = "#FF8B3D"
st.markdown("<h1 style='text-align: center; color: black;"
            "'>Tracking the NC Digital Divide: A Report Card Dashboard 📄 </h1>",
            unsafe_allow_html=True)
st.title("")

st.sidebar.title("Choose A County:")

page = st.sidebar.selectbox(
    '',
    df["county_name"].value_counts().index.to_list(),
)

st.sidebar.button("Generate Report Card", on_click=None)


# DEFINITIONS


# def generate_plan():
#     precint_names = pd.read_json("PrecintNames.json")
#     pef = [precint_names, model_predict()]
#     nc_precs = gpd.read_file('NC_precs_all_data.geojson')
#     nc_precs_join = nc_precs.merge(pef, left_on='loc_prec', right_on='Precint_ID', how='left')
#     nc_precs_dissolve = nc_precs_join.dissolve(by='assignment')
#     nc_precs_dissolve['assign'] = nc_precs_dissolve.index.copy()
#     return nc_precs_dissolve
#
#
# def create_map():
#     m = folium.Map(location=[35.6516, -80.3018], tiles="CartoDB positron", name="Light Map",
#                    zoom_start=7, attr="My Data Attribution")
#     folium.Choropleth(
#         geo_data=nc_precs_dissolve,
#         name="choropleth",
#         data=nc_precs_dissolve,
#         columns=["assign", "ID"],
#         key_on='feature.properties.assign',
#         fill_color="YlOrRd",
#         fill_opacity=0.7,
#         line_opacity=0.1,
#     ).add_to(m)
#     return m


# # SIDEBAR PREFERENCES
#
# st.sidebar.title("Choose A State:")
# state_mode = st.sidebar.selectbox(
#     'What state would you like to generate a map for?',
#     ['North Carolina']
# )
# st.sidebar.title("Decide Your Metrics:")
# st.sidebar.subheader("Cut Edges")
# cut_edges_input = st.sidebar.slider(
#     'Select a cut edges score',
#     574.0, 621.0
# )
# st.sidebar.subheader("Mean-Median")
# pf_input = st.sidebar.number_input(
#     "Desired mean-median score"
# )
# st.sidebar.title("Generate Map:")
# generate = st.sidebar.button("Generate Map")
# st.sidebar.header("Download Map")
# shape_dl = st.sidebar.checkbox("Download .SHP")
# geojson_dl = st.sidebar.checkbox("Download .GEOJSON")
# pef_dl = st.sidebar.checkbox("Download Equivalency File")
# download = st.sidebar.button("Download Files")
# st.markdown("<h1 style='text-align: center; color: black;"
#             "'>Set Preferences and Click Generate Map to see Districting Plan 🗺️ </h1>",
#             unsafe_allow_html=True)
#
# read in precinct shapefile
nc_counties = gpd.read_file('NC Counties2.geojson')
# 25/3 data
nc_data = pd.read_csv("county_data.csv")
# read in assignment file
# check for unique ID column to match length of precinct df
# nc_counties['loc_prec'].nunique()
# len(nc_precs)


nc_data["joiner"] = nc_data["county_name"].str.split(pat=" County",expand=True)[0]
nc_data["joiner"] = nc_data["joiner"].str.upper()
# join assignment csv to precinct shapefile
nc_counties_join = nc_counties.merge(nc_data, left_on='CO_NAME', right_on='joiner', how='left')
# geographic dissolve of precincts based on assignment column
nc_counties_dissolve = nc_counties_join.dissolve(by='county_name')
nc_counties_dissolve['county_name'] = nc_counties_dissolve.index.copy()
null_columns = nc_counties_dissolve.columns[nc_counties_dissolve.isnull().any()]

#
# nc_precs_dissolve.to_file('r"/Users/macbarnes/Desktop/Data/nc_precs_dissolve.geojson"', driver='GeoJSON')
#
# nc_precs_dissolve.to_file('r"/Users/macbarnes/Desktop/NC_precs/nc_precs_dissolve.shp"')


m = folium.Map(location=[35.6516, -79.92], tiles="CartoDB positron", name="Light Map",
               zoom_start=7, attr="My Data Attribution")
folium.Choropleth(
    geo_data=nc_counties_join,
    name="choropleth",
    data=nc_counties_join,
    columns=["county_code", "per_access"],
    key_on='feature.properties.county_code',
    fill_color="Purples",
    fill_opacity=0.7,
    line_opacity=0.1,
    legend_name='25/3 Broadband Access (% by County)',
).add_to(m)


folium.LayerControl().add_to(m)
folium_static(m, width=850, height=500)
m





