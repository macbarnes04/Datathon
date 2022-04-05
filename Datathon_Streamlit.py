import streamlit as st
import numpy as np
import folium
from streamlit_folium import folium_static
import pandas as pd
import geopandas as gpd
from annotated_text import annotated_text
import altair as alt

st.set_page_config(
    page_title="NCSSM - Broadband Progress Report",
)


# READING IN DATA
df = pd.read_csv("broadband_survey.csv")
nc_counties = gpd.read_file('NC Counties2.geojson')
nc_data = pd.read_csv("county_data.csv")


def df_from_hdf(hdf="database.h5", name="broadband_survey"):
    return pd.read_hdf(hdf, key=name)


aggregate = df_from_hdf(name="year_county_survey")
var_data = df_from_hdf(name="year_county_variability")
racial_data = pd.read_csv('2counties_racial.csv')
# st.write(aggregate)
# st.write(aggregate['per_access'].describe())
# st.write(var_data['variability'].describe())
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
    'Generate progress report',
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
    "average": "#d1ae0f",
    "higher than average": "#00a627",
}
if abbr_chosen == "All":
    st.markdown(
        "# Tracking the NC Digital Divide: A Progress Report 📄")
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
    st.markdown("# " + full_county + "'s Progress Report 📄")
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


def get_broad_score(score):
    mid_cutff = 40
    max_cutoff = 60

    score = round(score, 2)

    if score > max_cutoff:
        level = "higher than average"
        annotated_text(
            (str(score), "sufficient", colors[level]),
        )
        st.markdown(
            "**Continue Making Progress**")
        st.markdown("- This means that the county is faring well in its progress. However, this also means that this county should look into ensuring its systems of progress are able to be sustained. Further, this county should additionally look at its overall progress in relation to the state goals to ensure that it is on track to meet the State intended 2025 and 2030 goals.")
    elif score > mid_cutff:
        level = "average"
        annotated_text(
            (str(score), "progressing", colors[level]),
        )

        st.markdown("**Observe Other County’s Goals and Actions**")
        st.markdown("- This progressing rating means that in relation to other counties, this county is averaging well in terms of progress. However, there is room for improvement. This means that it could be in the best interest to inspect what other counties are doing to increase their progress towards the 2025 and 2030 goals.")
    else:
        level = "lower than average"
        annotated_text(
            (str(score), "insufficient", colors[level]),
        )
        st.markdown(
            "**Step 2: Observe Overall Progress to Ensure Preparedness**")
        st.markdown("- Since this rating is relative, it means that this county could be averaging relatively well in relation to other counties but be on or off-track in terms of the state’s overall goals. This county should consider both of these metrics and make decisions about resource allocation, ways to increase community engagement, and ensuring methods of access are equitable.")
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
            (str(score), "progressing", colors[level]),
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

    else:
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


def get_racial(score):
    score = round(np.abs(score).to_list()[0], 2)

    if score > 0.1:
        level = "lower than average"
        annotated_text(
            (str(score), "insufficient", colors[level]),
        )
        st.markdown(
            "**Understand Racial Compositions**")
        st.markdown(
            "- Starting with county-level populations, understand neighborhood racial compostions and the reason why certain groups are more prevalant in those areas")
        st.markdown(
            "- Take into consideration the ratios of minority races to majority races in the county population that have broadband access."
        )
        st.markdown(
            "- Understand why minority races lack broadband access."
        )

        st.markdown(
            "**Approach diversity causation by underlying reasons above**")
        st.markdown(
            "- Poverty and lack of financial resources: promote financial literacy, government financial aid, create job opportunities, raise minimal wage, relive areas of poverty focus such as food, shelter, and health care"
        )
        st.markdown(
            "- Lack of education: promote the development of schools, fund schools, hire high-quality educators, develop and refine educational policies, create educational programs for underrepresented children"
        )

        st.markdown("**Strongly encourage racial equity**")
        st.markdown(
            "- Prioritize providing broadband access to races that don’t have it to balance the racial disparity."
        )
        st.markdown(
            "- Develop environmental and cultural acceptance in geographic locations (Foster diverse cultural shops/attractions to attract races and make them want to migrate)"
        )
        st.markdown(
            "- Integrate educational establishments such as libraries in certain school districts to attract excluded racial groups in search of better opportunities"
        )

        st.markdown("**Integrate infrastructure and initaite plans**")
        st.markdown(
            "- Set strict timelines and deadlines for integration of solutions"
        )
        st.markdown(
            "- Progress towards goals")
    else:
        level = "higher than average"
        annotated_text(
            (str(score), "Sufficient", colors[level]),
        )

        st.markdown("**Maintain racial equity**")
        st.markdown(
            "- Racial equity within the county is prevalant and many miniority groups are given the same broadband access as majority racial groups."
        )
        st.markdown(
            "- Continue providing access to all racial groups within the county"
        )

        st.markdown(
            "- Focus more on the racial groups and the locations within the county that aren’t up to par yet")


if full_county != "All":
    # BROADBAND CHART
    st.markdown("## " + full_county + "'s Statistics")

    col1, col2 = st.columns(2)

    per_access_year = np.array(per_access_year)*100

    good_fit = np.linspace(per_access_year[0], 80, 5)

    access_chart_lines = np.array(
        list(zip(per_access_year, good_fit)))

    with col1:

        chart_data = pd.DataFrame(
            access_chart_lines, columns=[full_county, "On track"], index=(years))

        st.write(full_county + ": Broadband access vs. Time")
        st.line_chart(chart_data)

    with col2:
        get_broad_score(per_access_year[-1])

    col1_1, col2_1 = st.columns(2)

    with col1_1:
        chart_data_var = pd.DataFrame(
            var_by_year, columns=["variability"], index=years)
        st.write(full_county + ": Quality of Survey Data vs. Time")
        st.line_chart(chart_data_var)

    with col2_1:
        get_vari_score(np.average(var_by_year))

    # st.write(racial_data)

    if (abbr_chosen == "BUNCOMBE" or abbr_chosen == "BURKE"):
        col1_2, col2_2 = st.columns(2)

        with col1_2:
            st.write(full_county + ": % Access by Race")
            racial_data = racial_data.loc[racial_data["county"] == abbr_chosen]
            racial_data_use = racial_data["white_access"] + \
                racial_data["black_access"]
            np_arr = racial_data[["black_access", "white_access",
                                  "latino_access"]].iloc[0].to_numpy()

            st.write()
            chart_data_var = pd.DataFrame(
                np_arr,
                columns=["% Access"],
                index=["Black", "White", "Latino"]
            )
            print(chart_data_var)
            # pd.DataFrame(
            #    racial_data_use, index=("White", "Black"))
            # st.write(full_county + ": Quality of Survey Data vs. Time")
            st.bar_chart(chart_data_var)

        with col2_2:
            # get_vari_score(np.average(var_by_year))
            get_racial(racial_data["black_access"] -
                       racial_data["white_access"])

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
