import streamlit as st
import pandas as pd
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import plotly.express as px
import utils

st.set_page_config(layout="wide")
st.title("Passive vehicle sensor data")



drive_details = utils.load_csv("data/drive_details.csv")
drive_details = drive_details.set_index('DataSet')
#Allow user to choose drive number
with st.sidebar:
    drive_nr = st.selectbox(
        "Choose drive number",
        range(1,10)
    )
    
    st.write(drive_details)

#Load files
gps_coords = utils.load_csv(f"data/dataset_gps ({drive_nr}).csv")
dataset_gps_mpu_left = utils.load_csv("data/dataset_gps_mpu_left.csv")


# Calculate distance driven
dist_driven = utils.dist_driven(gps_coords)

# Calculate max speed and mean speed
max_speed = gps_coords["speed_meters_per_second"].max()
avg_speed = gps_coords["speed_meters_per_second"].mean()

# Calculate min and max elevation
max_elevation = gps_coords["elevation"].max()
min_elevation = gps_coords["elevation"].min()

# Calculate time taken 
time_taken = gps_coords["timestamp"].max() - gps_coords["timestamp"].min() 


#Create a set of 5 metrics that summarise the ride
st.subheader("Drive metrics")

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)


kpi1.metric(
    label="Top speed (m/s)",
    value=round(max_speed,1)
)
kpi2.metric(
    label="Average speed (m/s)",
    value=round(avg_speed,1)
)
kpi3.metric(
    label="Max elevation (m)",
    value=round(max_elevation, 1)
)
kpi4.metric(
    label="Total time (minutes)",
    value=round(time_taken/60, 1)
)
kpi5.metric(
    label="Total distance (km)",
    value=round(dist_driven, 1)
)






##### COMFORT METRICS #####


st.subheader("Comfort metrics")


df = utils.calc_acceleration(gps_coords, "elapsed_time_seconds", "speed_meters_per_second")


agg_limit = 3
decel, accel = utils.calc_agg_accels(df, "acceleration", "elapsed_time_seconds", agg_limit)

#Calculate sharp turns by a 90 degree bearing change in one time
turn_limit = 90
turns = utils.calc_sharp_turns(df, "bearing", "elapsed_time_seconds", turn_limit)



# Showing 5 metrics related to comfort
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

kpi1.metric(
    label=f"Instances of aggressive acceleration (>{agg_limit} m/s)",
    value=accel
)
kpi2.metric(
    label=f"Instances of aggressive deceleration (>{agg_limit} m/s)",
    value=decel
)
kpi3.metric(
    label=f"Instances of aggressive turns (bearing change > {turn_limit})",
    value=turns
)
kpi4.metric(
    label="Total time (minutes)",
    value=round(time_taken/60, 1)
)
kpi5.metric(
    label="Total distance (km)",
    value=round(dist_driven, 1)
)


##### PRECISION METRICS #####


st.subheader("Sensor precision metrics")
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

avg_hdop = gps_coords["hdop"].mean()
avg_pdop = gps_coords["pdop"].mean()
avg_vdop = gps_coords["vdop"].mean()



total_poor_dop = utils.calc_poor_dop(gps_coords, "hdop", "elapsed_time_seconds")


kpi1.metric(
    label=f"Instances of aggressive acceleration (>{agg_limit} m/s)",
    value=accel,
    #delta=round(avg_price_now)-round(avg_price_then), 
    #delta_color="inverse"
)
kpi2.metric(
    label=f"Instances of aggressive deceleration (>{agg_limit} m/s)",
    value=decel
    #delta=dearest_borough.title(),
   # delta_color = "inverse"
)
kpi3.metric(
    label=f"Instances of aggressive turns (bearing change > {turn_limit})",
    value=turns,
   # delta=int(avg_sal_now-avg_sal_then),
   # delta_color="inverse"
)
kpi4.metric(
    label="Total time (minutes)",
    value=round(time_taken/60, 1)
    #delta=dearest_borough.title(),
   # delta_color = "inverse"
)
kpi5.metric(
    label="Total distance (km)",
    value=round(dist_driven, 1)
    #delta=dearest_borough.title(),
   # delta_color = "inverse"
)



##### DRIVE METRICS #####

#GOOGLE MAPS SPEED
orig_coord = df.iloc[0]['latitude'], df.iloc[0]['longitude']

df["dist_to_origin"] = df.apply(lambda x: geodesic((x["latitude"], x["longitude"]), orig_coord).km, axis=1)
max_dist_ind = df["dist_to_origin"].idxmax()
dest_coord = (df.at[max_dist_ind, 'latitude'], df.at[max_dist_ind, 'longitude'])



import googlemaps
from datetime import datetime

gmaps = googlemaps.Client(key='AIzaSyDWsxdWTWXdKe2IAZJMyNV4MVpZaR1hql4')#

now = datetime.now()
directions_result = gmaps.directions(orig_coord,
                                     dest_coord,
                                     mode="driving",
                                     avoid="ferries",
                                     departure_time=now
                                    )

#st.write(directions_result[0]['legs'][0]['distance']['text'])
#st.write(directions_result[0]['legs'][0]['duration']['text'])


##### DRIVE MAP #####




st.subheader("Drive map")
y = st.selectbox("Pick a variable to view", ["Drive path", "Speed", "Altitude"])
if y == "Drive path":
    plot_data = utils.get_colours(gps_coords, "timestamp")
    st.write("Drive begins with the blue points and ends with the yellow points")
elif y == "Speed":
    plot_data = utils.get_colours(gps_coords, "speed_meters_per_second")
    st.write("Blue points are higher speed, yellow points are lower speed")
elif y == "Altitude":
    plot_data = utils.get_colours(gps_coords, "elevation")
    st.write("Blue points are at higher altitudes, yellow points are at lower altitudes")



fig = px.scatter_mapbox(plot_data,
                        lat='latitude',
                        lon='longitude',
                        color='elevation',
                        zoom=11.5,  # Adjust the zoom level as needed
                        title="Drive map",
                        color_continuous_scale="Viridis")       
fig.update_layout(mapbox_style="open-street-map",  # You can choose different Mapbox styles
                  mapbox=dict(
                      center=dict(lat=df['latitude'].mean(), lon=df['longitude'].mean()),  # Center the map around the data
                      layers=[]  # Remove additional Mapbox layers (e.g., roads)
                  ))              
st.plotly_chart(fig, use_container_width=True)
#st.map(plot_data, size=0.05, color="colour", use_container_width=True)






if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(gps_coords.head())
    st.write(dataset_gps_mpu_left.head())