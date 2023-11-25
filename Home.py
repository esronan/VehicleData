import streamlit as st
import pandas as pd
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Passive vehicle sensor data")
with st.sidebar:
    drive_nr = st.selectbox(
        "Choose drive number",
        range(1,10)
    )
gps_coords = pd.read_csv(f"data/dataset_gps ({drive_nr}).csv")

dataset_gps_mpu_left = pd.read_csv("data/dataset_gps_mpu_left.csv")
st.write(dataset_gps_mpu_left)
st.write(gps_coords)

def dist_driven(df):
    i = 0
    dists = []
    for j in df[["latitude", "longitude"]].values:
        if i == 0: 
            current = j
            i+=1
        else:
            dists.append(geodesic(current, j).km)
            current = j
            i+=1
    return sum(dists)

dist_driven = dist_driven(gps_coords)

def get_var(data, col, area, year):
    mask = (data["area"]== area) & (data["date"] == year)
    val = data[mask][col].iloc[0]
    return val


max_speed = gps_coords["speed_meters_per_second"].max()
avg_speed = gps_coords["speed_meters_per_second"].mean()

max_elevation = gps_coords["elevation"].max()
min_elevation = gps_coords["elevation"].min()

time_taken = gps_coords["timestamp"].max() - gps_coords["timestamp"].min() 

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

def calc_acceleration(df, time_col, velocity_col):
    df["acceleration"] = df[velocity_col].diff()/df[time_col]
    return df
df = calc_acceleration(gps_coords, "elapsed_time_seconds", "speed_meters_per_second")

#Calculate episodes of aggressive acceleration and deceleration, defined by being above a certain threshold of acceleration, and assuming that sequential high acceleration measurements are part of the same episode
def calc_agg_accels(df, acc_col, elapsed_time_col, agg_limit):

    #Initialise column with time elapsed since aggressive deceleration episode
    df["decel_time_elaps"] = 0

    #Initialise aggressive decel index and time elapsed since
    agg_ind = 0
    time_elaps = 0

    #Iterrate through rows and find aggressive deceleration episodes and calculate time elapsed since last
    for i, row in df.iterrows():
        time_elaps += row[elapsed_time_col]
        if row[acc_col] < -agg_limit:
            df.at[i,"decel_time_elaps"] = time_elaps
            agg_ind = i
            time_elaps = 0
    
    #Initialise column with time elapsed since aggressive deceleration episode
    df["accel_time_elaps"] = 0

    #Initialise aggressive decel index and time elapsed since
    agg_ind = 0
    time_elaps = 0

    #Iterrate through rows and find aggressive deceleration episodes and calculate time elapsed since last
    for i, row in df.iterrows():
        time_elaps += row[elapsed_time_col]
        if row[acc_col] > agg_limit:
            df.at[i,"accel_time_elaps"] = time_elaps
            agg_ind = i
            time_elaps = 0
    

    decel = sum((df["acceleration"] < -agg_limit) & (df["decel_time_elaps"] > 5))
    accel = sum((df["acceleration"] > agg_limit) & (df["accel_time_elaps"] > 5))


    return decel, accel

agg_limit = 3
decel, accel = calc_agg_accels(df, "acceleration", "elapsed_time_seconds", agg_limit)

#calculate amount of sharp turns from the GPS bearing data, assuming that 90 degrees in under a second is a sharp turn, and that multiple 90 degrees turns sequentially is the same turn
def calc_sharp_turns(df, bearing_col, elapsed_time_col, turn_limit):

    df["bearing_turn"] = df[bearing_col].diff()

    #Initialise column with time elapsed since aggressive deceleration episode
    df["turn_time_elaps"] = 0

    #Initialise aggressive decel index and time elapsed since
    turn_ind = 0
    time_elaps = 0

    #Iterrate through rows and find aggressive deceleration episodes and calculate time elapsed since last
    for i, row in df.iterrows():
        time_elaps += row[elapsed_time_col]
        if abs(row["bearing_turn"]) > turn_limit:
            df.at[i,"turn_time_elaps"] = time_elaps
            turn_ind = i
            time_elaps = 0

    #sum all the turns above bearing threshold that did not occur in the same movement (i.e. sequentially)
    turns = sum((abs(df["bearing_turn"]) > turn_limit) & (df["turn_time_elaps"] > 5))# & (df[elapsed_time_col] < 2))

    return turns

turn_limit = 90
turns = calc_sharp_turns(df, "bearing", "elapsed_time_seconds", turn_limit)




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

def calc_poor_dop(df, dop_col, elapsed_time_col):
    total_time = 0
    for i, row in df.iterrows():
        if abs(row[dop_col]) > 20: #20 = poor precision
            total_time += df.at[i,elapsed_time_col]
    return total_time

total_poor_dop = calc_poor_dop(gps_coords, "hdop", "elapsed_time_seconds")
st.write(total_poor_dop)

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
st.write(dest_coord)


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

def min_max_scaler(df, col, type="size"):
    
    df["size"] = (df[col]-df[col].min())/(df[col].max()-df[col].min())
    if type == "colour":
        df["colour"] = df["size"].apply(lambda x: (255*x, abs(255*(1-x)),0))
    return df

#generate a hex colour gradient along the time dimension
def get_colours(df, col):
    norm = mcolors.Normalize(vmin=df[col].min(), vmax=df[col].max())
    colormap = plt.cm.viridis
    df['colour'] = df[col].apply(lambda x: mcolors.to_hex(colormap(norm(x))))
    return df



st.subheader("Drive map")
y = st.selectbox("Pick a variable to view", ["Drive path", "Speed", "Altitude"])
if y == "Drive path":
    plot_data = get_colours(gps_coords, "timestamp")
    st.write("Drive begins with the blue points and ends with the yellow points")
elif y == "Speed":
    plot_data = get_colours(gps_coords, "speed_meters_per_second")
    st.write("Blue points are higher speed, yellow points are lower speed")
elif y == "Altitude":
    plot_data = get_colours(gps_coords, "elevation")
    st.write("Blue points are at higher altitudes, yellow points are at lower altitudes")



fig = px.scatter_mapbox(plot_data,
                        lat='latitude',
                        lon='longitude',
                        color='elevation',
                        zoom=11.5,  # Adjust the zoom level as needed
                        title="Plotly Map with Fixed View and Roads",
                        color_continuous_scale="Viridis")       
fig.update_layout(mapbox_style="open-street-map",  # You can choose different Mapbox styles
                  mapbox=dict(
                      center=dict(lat=df['latitude'].mean(), lon=df['longitude'].mean()),  # Center the map around the data
                      layers=[]  # Remove additional Mapbox layers (e.g., roads)
                  ))              
st.plotly_chart(fig, use_container_width=True)
#st.map(plot_data, size=0.05, color="colour", use_container_width=True)

def plot_2d_3col(df, variable, sensor_location, title):
    st.header(title)
    col1, col2, col3 = st.columns(3)
    with col1: 
        y_col = variable + "_x_" + sensor_location
        fig = px.line(dataset_gps_mpu_left, x="timestamp", y=y_col, title='X axis')
        st.plotly_chart(fig, use_container_width=True)
    with col2: 
        y_col = variable + "_y_" + sensor_location
        fig = px.line(dataset_gps_mpu_left, x="timestamp", y=y_col, title='Y axis')
        st.plotly_chart(fig, use_container_width=True)
    with col3: 
        y_col = variable + "_z_" + sensor_location
        fig = px.line(dataset_gps_mpu_left, x="timestamp", y=y_col, title='Z axis')
        st.plotly_chart(fig, use_container_width=True)

def plot_1d_3col(df, variable, sensor_location, title):
    st.header(title)
    col1, col2, col3 = st.columns(3)
    with col1: 
        x_col = variable + "_x_" + sensor_location
        fig = px.histogram(dataset_gps_mpu_left, x=x_col, histfunc="count", title='X axis')
        st.plotly_chart(fig, use_container_width=True)
    with col2: 
        x_col = variable + "_y_" + sensor_location
        fig = px.histogram(dataset_gps_mpu_left, x=x_col, histfunc="count", title='Y axis')
        st.plotly_chart(fig, use_container_width=True)
    with col3: 
        x_col = variable + "_z_" + sensor_location
        fig = px.histogram(dataset_gps_mpu_left, x=x_col, histfunc="count", title='Z axis')
        st.plotly_chart(fig, use_container_width=True)
    
fig = px.histogram(dataset_gps_mpu_left, x="acc_x_dashboard", nbins=200)
st.plotly_chart(fig)


plot_2d_3col(dataset_gps_mpu_left, "acc", "dashboard", "Accelerometer")
plot_1d_3col(dataset_gps_mpu_left, "acc", "dashboard", "Accelerometer")
# with col1: 
#     fig = px.line(dataset_gps_mpu_left, x="timestamp", y="acc_x_dashboard", title='Accelerometer (X axis)')
#     st.plotly_chart(fig, use_container_width=True)



if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(gps_coords)