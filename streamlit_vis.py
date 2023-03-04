import streamlit as st
import pandas as pd 
import altair as alt 
from altair import pipe, limit_rows, to_values
import geopandas as gpd
from vega_datasets import data
t = lambda data: pipe(data, limit_rows(max_rows=10000), to_values)
alt.data_transformers.register('custom', t)
alt.data_transformers.enable('custom')

df = pd.read_csv("ev_data.csv")

st.set_page_config(
    page_title="Electric Vehicles",
    page_icon="🧊",
    layout="wide",
)



def plot_altair(df):
    for c in df.columns:
        print(c)

    print(df['State'].unique())
    # Clean Dataset
    df = df.dropna()
    #df = df.drop(df.index[df['Model Year'] != 2022])
    df = df.drop(df.index[df['State'] != 'WA'])
    df = df.drop(df.index[df['Electric Range'] <= 100])
    df = df.drop(df.index[df['Model Year'] < 2020])
    df = df.reset_index()
    print(df.iloc[-1])

    reduced_string = "BONNEVILLE POWER"
    for eu in df['Electric Utility'].unique():
        if reduced_string in eu:
            df.loc[df['Electric Utility'] == eu, 'Electric Utility'] = reduced_string

    for eu in df['Electric Utility'].unique():
        if df.loc[df['Electric Utility'] == eu, 'Electric Utility'].count() < 500:
            df.loc[df['Electric Utility'] == eu, 'Electric Utility'] = "Other"

    df.reset_index(drop=True, inplace=True)
    print(df['Electric Utility'].unique())

    df.loc[df['Electric Utility'] == 'PUGET SOUND ENERGY INC||CITY OF TACOMA - (WA)', 'Electric Utility'] = "CITY OF TACOMA"
    df.loc[df['Electric Utility'] == 'CITY OF SEATTLE - (WA)|CITY OF TACOMA - (WA)', 'Electric Utility'] = "CITY OF SEATTLE"

    # electric utility vs make bar chart, zoom in to see make?
    df['Vehicle Location'] = df['Vehicle Location'].apply(lambda x: x.split("(")[1].split(")")[0])
    df['lon'] = df['Vehicle Location'].apply(lambda x: float(x.split(" ")[0]))
    df['lat'] = df['Vehicle Location'].apply(lambda x: float(x.split(" ")[1]))

    interval = alt.selection_multi(encodings=['color'])

    #gdf = gpd.read_file('https://raw.githubusercontent.com/python-visualization/folium/master/tests/us-states.json', driver='GeoJSON')
    gdf = alt.topo_feature('https://raw.githubusercontent.com/python-visualization/folium/master/tests/us-states.json', feature='states')
    print(gdf)

    regions = alt.topo_feature(data.us_10m.url, 'counties')

    #gdf = gdf[gdf.id=='WA']
    inline_data = regions
    base = alt.Chart(inline_data, title='Location of Registered EVs').mark_geoshape(
        stroke='gray', 
        fill=None
    ).properties(
        width=500,
        height=500,
    ).transform_calculate(state_id = "(datum.id / 1000)|0").transform_filter((alt.datum.state_id)==53)

    plot_scheme = "set3"

    pts = alt.Chart(df).mark_circle().encode(
        latitude='lat',
        longitude='lon',
        color=alt.Color('Make', scale=alt.Scale(scheme=plot_scheme)),
        opacity=alt.value(0.8),
    ).transform_filter(interval)

    base = base + pts

    city_data = {'city': ['Seatle', 'Olympia', 'Tacoma', 'Spokane', 'Vancouver'],
                'lat': [47.608013, 47.0379, 47.2529, 47.6588, 45.6280],
                'lon': [-122.335167, -122.9007, -122.4443, -117.4260, -122.6739]}
    cities = pd.DataFrame(city_data)
    cities1 = cities.loc[cities['city'] != 'Spokane']
    cities2 = cities.loc[cities['city'] == 'Spokane']
    cities1 = cities1.loc[cities1['city'] != 'Olympia']
    cities3 = cities.loc[cities['city'] == 'Olympia']
    cities1 = cities1.loc[cities1['city'] != 'Vancouver']
    cities4 = cities.loc[cities['city'] == 'Vancouver']

    city_chart = alt.Chart(cities1).mark_point().encode(
        latitude='lat',
        longitude='lon',
        color=alt.value("black"),
    ).mark_text(dx=35, dy=-5, size=20, align='left', baseline='middle').encode(text='city')
    city_chart2 = alt.Chart(cities2).mark_point().encode(
        latitude='lat',
        longitude='lon',
        color=alt.value("black"),
    ).mark_text(dx=-20, dy=-5, size=20, align='right', baseline='middle').encode(text='city')

    city_chart3 = alt.Chart(cities3).mark_point().encode(
        latitude='lat',
        longitude='lon',
        color=alt.value("black"),
    ).mark_text(dx=20, dy=-15, size=20, align='right', baseline='middle').encode(text='city')
    city_chart4 = alt.Chart(cities4).mark_point().encode(
        latitude='lat',
        longitude='lon',
        color=alt.value("black"),
    ).mark_text(dx=22, dy=-18, size=20, align='left', baseline='middle').encode(text='city')



    base = base + city_chart + city_chart2 + city_chart3 + city_chart4


    bar_chart = alt.Chart(df, title='Electric Utility Customers with EVs').mark_bar(size=30).encode(
        y='Electric Utility',
        x='count(Electric Utility):Q',
        tooltip=['Electric Utility', 'Make', 'count(Electric Utility):Q'],
        color=alt.Color('Make', scale=alt.Scale(scheme=plot_scheme)),
    ).interactive(
    ).transform_filter(
        interval
    ).properties(
        width=500,
        height=250
    )

    car_chart = alt.Chart(df, title='Registered 2020 or newer EVs in Washington').mark_bar().encode(
        y='Make',
        x='count(Make):Q',
        tooltip=['Make', 'count(Make):Q'],
        color=alt.condition(interval, "Make", alt.value('lightgray'))
    ).properties(
        width=500,
        height=250
    ).interactive(
    ).add_selection(
        interval
    )

    car_chart.properties(
        title='Electric Vehicles in WA'
    )



    text = alt.Chart({'values':[{}]}).mark_text(
        align="center", baseline="middle"
    ).encode(
        x=alt.value(250),  # pixels from left
        y=alt.value(125),  # pixels from top
        opacity=alt.value(0.4),
        text=alt.value([f"Click to select!"]))
    car_chart = car_chart + text


    chart = car_chart | bar_chart 
    chart = alt.vconcat(chart, base).configure_legend(unselectedOpacity=1.0, symbolFillColor='Make')

    chart = chart.properties(
        title=alt.TitleParams('Electric Vehicles (EVs) and Utitlities', fontSize=30, anchor='middle', 
                                subtitle=['2020 and newer EVs registered in the State of Washington']),
    )
    return chart

alt_plot = plot_altair(df)
st.altair_chart(alt_plot)


