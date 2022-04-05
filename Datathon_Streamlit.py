import streamlit as st
import numpy as np
import folium
from streamlit_folium import folium_static
import pandas as pd
import geopandas as gpd
from annotated_text import annotated_text

# READING IN DATA
df = pd.read_csv("broadband_survey.csv")
nc_counties = gpd.read_file('NC Counties2.geojson')
nc_data = pd.read_csv("county_data.csv")


def df_from_hdf(hdf="./aggregate/database.h5", name="broadband_survey"):
    return pd.read_hdf(hdf, key=name)


# aggregate = df_from_hdf(key="year_county_survey")
# st.write(aggregate)
# DATA PREPROCESSING
df = df.loc[df["state_code"] == 37]  # only NC

nc_data["joiner"] = nc_data["county_name"].str.split(
    pat=" County", expand=True)[0]
nc_data["joiner"] = nc_data["joiner"].str.upper()
# join assignment csv to precinct shapefile
nc_counties_join = nc_counties.merge(
    nc_data, left_on='CO_NAME', right_on='joiner', how='left')
# geographic dissolve of precincts based on assignment column
nc_counties_dissolve = nc_counties_join.dissolve(by='county_name')
nc_counties_dissolve['county_name'] = nc_counties_dissolve.index.copy()
null_columns = nc_counties_dissolve.columns[nc_counties_dissolve.isnull(
).any()]


# create mapper from full name to abbreviation
full_county_names = list(df["county_name"].unique())

abbr_county_names = list(
    nc_counties_join["CO_NAME"].unique())

full_to_abbr_names = {'All': 'All'}
for full_name in full_county_names:
    for abbr_name in abbr_county_names:
        if full_name.split()[0].lower() == abbr_name.lower():
            full_to_abbr_names[full_name] = abbr_name

st.sidebar.title("Choose your metrics:")

selectbox_options = [
    "All", *sorted(df["county_name"].value_counts().index.to_list())]
full_county = st.sidebar.selectbox(
    'County Name',
    selectbox_options,
)

# User options
abbr_chosen = full_to_abbr_names[full_county]

# PAGE FORMATTING
# st.markdown("<h1 style='text-align: center; color: white;"
#             "'>Tracking the NC Digital Divide: A Report Card Dashboard 📄 </h1>",
#             unsafe_allow_html=True)


m = folium.Map(location=[35.6516, -79.92], tiles="CartoDB positron",
               name="Light Map", zoom_start=7, attr="My Data Attribution")

textColor = "#262730"

nc_avg_per_access = round(nc_counties_join['per_access'].mean() * 100, 2)
data_using = None

colors = {
    "lower than average": "#ff7a7a",
    "average": "#ffda33",
    "higher than average": "#00a627",
}
if abbr_chosen == "All":
    st.markdown("# Tracking the NC Digital Divide: A Report Card Dashboard 📄")
    # find the average of the column per_access in nc_counties_join

    # st.markdown("#### Overall, " + str(nc_avg_per_access) +
    #             "% of people have access to broadband")
    annotated_text(
        (str(nc_avg_per_access) + "%", "higher than national average", "#ff7a7a"),
        " of families do not have internet at all ",
    )

    st.write("")
    annotated_text(
        "An estimated ",
        ("500,000", "high", "#ff7a7a"),
        " of students in NC do not have access to high-speed internet at home ",
    )
    st.write("")

    annotated_text(
        "Black, Hispanic, and Native American households are over ",
        ("10%", "more likely", colors["lower than average"]),
        " to have a broadband internet subscription than white or Asian households.",
    )

    st.markdown("### The Goal")
    annotated_text(
        ("2 million", "by 2030", "#00a627"),
        " of adults with post-secondary degree by 2030.",
    )

    st.write("")
    annotated_text(
        ("80%", "by 2025", "#00a627"),
        " of households to have at least 100 Mbps download and 20 Mbps upload speeds.",
    )

    st.write("")
    annotated_text(
        ("100%", "by 2025", "#00a627"),
        " of households with kids to have broadband internet access.",
    )

    # 2 million adults
    # broadband internet access

    # annotated_text(
    #     "The average percentage of people in the North Carolina state have access to broadband is ",
    #     (str(nc_avg_per_access) + "%", "low", "#ff7a7a"),
    # )

    data_using = nc_counties_join
else:
    data_using = nc_counties_join.loc[nc_counties_join["CO_NAME"]
                                      == abbr_chosen]

    spec_per = round(
        float(data_using["per_access"].to_string().split()[1]) * 100, 2)
    st.markdown("# " + full_county + "'s grade report 📄")
    # per_access_string = "#### " + \
    #     str(spec_per) + "% have access to broadband internet"
    # st.write(per_access_string)
    level = None
    if spec_per < nc_avg_per_access:
        level = "lower than average"
    elif spec_per > nc_avg_per_access:
        level = "higher than average"
    else:
        level = "average"
    annotated_text(
        "There are ",
        (str(spec_per), "%", colors[level]),
        " (" + level + ")" + " of people in " + full_county +
        " who have access to broadband internet",
    )


# folium.Marker(
#     location=[34.9790, -79.2461],
#     popup="Mt. Hood Meadows",
#     icon=folium.Icon(icon="cloud"),
# ).add_to(m)

st.write("")
folium.Choropleth(
    geo_data=data_using,
    name="choropleth",
    data=data_using,
    columns=["county_code", "per_access"],
    key_on='feature.properties.county_code',
    fill_color="Purples",
    fill_opacity=1.0,
    line_opacity=0.4,
    legend_name='25/3 Broadband Access (% by County)',
).add_to(m)

# st.write(nc_data)


folium.LayerControl().add_to(m)
folium_static(m, width=850, height=500)
m


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
