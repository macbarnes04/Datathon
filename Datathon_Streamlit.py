import streamlit as st
import numpy as np
import folium
from streamlit_folium import folium_static
import pandas as pd
import geopandas as gpd
from annotated_text import annotated_text
import altair as alt

st.set_page_config(
    page_title="NCSSM - Broadband Report",
)


# READING IN DATA
df = pd.read_csv("broadband_survey.csv")
nc_counties = gpd.read_file('NC Counties2.geojson')
nc_data = pd.read_csv("county_data.csv")


def df_from_hdf(hdf="database.h5", name="broadband_survey"):
    return pd.read_hdf(hdf, key=name)


aggregate = df_from_hdf(name="year_county_survey")
var_data = df_from_hdf(name="year_county_variability")

st.write(var_data)
st.write(var_data['variability'].describe())
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

st.sidebar.title("Choose a county:")

selectbox_options = [
    "All", *sorted(df["county_name"].value_counts().index.to_list())]
full_county = st.sidebar.selectbox(
    'Generate report',
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
        (str(25) + "%", "higher than national average", "#ff7a7a"),
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
    folium.LayerControl().add_to(m)
    folium_static(m, width=850)
else:
    data_using = nc_counties_join.loc[nc_counties_join["CO_NAME"]
                                      == abbr_chosen]

    spec_per = round(
        float(data_using["per_access"].to_string().split()[1]) * 100, 2)
    st.markdown("# " + full_county + "'s Report 📄")
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
        (str(spec_per), "%", colors[level]),
        " (" + level + " in nc)" + " of people in " + full_county +
        " have access to broadband internet",
    )

    st.write("")

    data_agg = aggregate.loc[aggregate["county_name"] == full_county]

    data_agg.sort_values(by="year", inplace=True)
    years = data_agg["year"].unique()
    per_access_year = data_agg["per_access"].to_list()

    variable_agg = var_data.loc[aggregate["county_name"] == full_county]
    variable_agg.sort_values(by="date", inplace=True)
    var_years = variable_agg["date"].unique()
    var_by_year = variable_agg["variability"].to_list()

    df_using = df.loc[df["county_name"] == full_county]
    df_using_filtered = df_using.query(
        "(dl_speed >= 100) and (ul_speed >= 20)")

    X = df_using_filtered['X']
    Y = df_using_filtered['Y']

    coords_use = np.array(list(zip(Y, X)))

    df = pd.DataFrame(
        coords_use,
        columns=['lat', 'lon'])

    st.map(df)
    st.markdown(
        "##### Survey indicated that " + str(len(df_using_filtered)) + " people who indicated on the survey have access to broadband internet in " + full_county + " (out of " + str(len(df_using)) + " people).")


# folium.Marker(
#     location=[34.9790, -79.2461],
#     popup="Mt. Hood Meadows",
#     icon=folium.Icon(icon="cloud"),
# ).add_to(m)


# st.write(nc_data)


# individualized charts

def get_vari_score(score):
    min_cutoff = 0.0030
    mid_cutoff = 0.0240
    max_cutoff = 0.0732

    score = round(score, 2)
    if score > max_cutoff:
        level = "higher than average"
        annotated_text(
            (str(score), "sufficient", colors[level]),
        )
        st.markdown(
            "**Maintain Data Collection Methods**")
        st.markdown(
            "- Maintain quantity of data being collected while priortizing quality of data (collect additional neccesary information and ensure surveys are accurately representative of the population)")
    elif score > mid_cutoff:
        level = "average"
        annotated_text(
            (str(score), "progressive", colors[level]),
        )
        st.markdown(
            "**Put more resources and efforts into collecting accurate analytical data**")
        st.markdown(
            "- Data is being collected at a fair rate however quality and quantity could be improved")
        st.markdown(
            "- Prioritize quality over quantity first")

        st.markdown(
            "- Data is being collected at a fair rate however quality and quantity could be improved")

        st.markdown(
            "- Spread out surveyors around the counties")

    elif score > min_cutoff:
        level = "lower than average"
        annotated_text(
            (str(score), "insufficient", colors[level]),
        )

        st.markdown(
            "**Step 1: Seriously Refine Data Collection Methods**")
        st.markdown(
            "- Confirm county-level survey data is being compared to census data to ensure data is accurately collected")
        st.markdown(
            "**Step 2: Aggressively Address Survey Cause**")

        st.markdown(
            "- Properly address the issues that cause such a lack of broadband access")

    st.write("")


if full_county != "All":
    # BROADBAND CHART
    st.markdown("## " + full_county + "'s Statistics")

    col1, col2 = st.columns(2)
    avgs = [nc_avg_per_access for _ in range(len(per_access_year))]

    per_access_year = np.array(per_access_year)*100
    access_chart_lines = np.array(
        list(zip(per_access_year, avgs)))

    with col1:
        chart_data = pd.DataFrame(
            access_chart_lines, columns=[full_county, "NC Average"], index=years)

        st.write(full_county + ": Broadband access vs. Time")
        st.line_chart(chart_data)
        chart_data_var = pd.DataFrame(
            var_by_year, columns=["variability"], index=years)

    with col2:
        st.write("blah blah blah")

    col1_1, col2_1 = st.columns(2)

    with col1_1:
        st.write(full_county + ": Quality of Survey Data vs. Time")
        st.line_chart(chart_data_var)

    with col2_1:
        get_vari_score(np.average(var_by_year))

    # source = chart_data.reset_index().melt('x', var_name='category', value_name='y')

    # line_chart = alt.Chart(chart_data).mark_line().encode(
    #     alt.X(title='Year'),
    #     alt.Y(title='Amount in liters'),
    # ).properties(
    #     title='Sales of consumer goods'
    # )

    # st.altair_chart(line_chart)


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
