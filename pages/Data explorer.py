import streamlit as st
import pandas as pd
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import plotly.express as px
import utils

st.set_page_config(layout="wide")

st.title("Data Explorer")



# Allow user to choose drive number and to select sensor
with st.sidebar:
    drive_nr = st.selectbox(
        "Choose drive number",
        range(1,4)
    )
    sensor = st.selectbox(
        "Choose sensor",
        ["Accelerometer", "Magnetometer", "GNSS", "Gyrometer", "Temperature Sensor"]
    )
    timeslice = st.selectbox(
        "Entire dataset or point in time?",
        ["Point in time", "Entire data set"]
    )
    if timeslice == "Point in time":
        timestamp = st.number_input("Type in timestamp of interest", value=1577218796.6,) #e.g. "1,577,218,796.81"
        timespan = st.number_input("Type in timespan of interest (seconds)", value=10)
        st.write("e.g. 10 seconds = +/- 5 seconds")

with st.columns(3)[1]:
    st.subheader(f"Frame at timestamp: {timestamp}")
    st.image("data/example_image.png")

# Initiate dictionary to convert user selected sensor to the csv tag
sensor_dic = {"Accelerometer": "acc", "Magnetometer": "mag", "GNSS":"dop", "Gyrometer": "gyro", "Temperature Sensor":"temp"}
sensor_locs = {"acc":["dashboard", "below_suspension", "above_suspension"], 
        "mag": ["dashboard", "above_suspension"],
        "gyro":["dashboard", "below_suspension", "above_suspension"], 
        "temp": ["below_suspension", "above_suspension"]
}

# Load files
gps_df = utils.load_csv(f"data/{drive_nr}/dataset_gps.csv")
dataset_gps_mpu_left = pd.read_csv(f"data/{drive_nr}/dataset_gps_mpu_left.csv")

#Gets the closest time to timestamp in the df and filters out all rows within given time frame
def get_timeslice(df, col, stamp, span):
    slyce = df[(df[col]-stamp).abs() < 10]
    return slyce

if timeslice == "Point in time":
    plot_data = get_timeslice(dataset_gps_mpu_left, "timestamp", timestamp, timespan)
else:
    plot_data = dataset_gps_mpu_left


# fig = px.histogram(dataset_gps_mpu_left, x="acc_x_dashboard", nbins=200)
# st.plotly_chart(fig)

def plot_2d_xyz(df, sensor, locs):
    st.header(sensor + " readings")
    var = sensor_dic[sensor]
    cols = st.columns(len(locs))
    
    for col, loc in zip(cols, locs):

        x_col = var + "_x_" + loc
        y_col = var + "_y_" + loc
        z_col = var + "_z_" + loc

        with col:
            if sensor == "Temperature Sensor":
                fig = px.line(df, x="timestamp", y=var+ "_" + loc, title=" ".join(loc.split("_")).capitalize())
                st.plotly_chart(fig, use_container_width=True)
                continue
            fig = px.line(title=" ".join(loc.split("_")).capitalize())
            fig.add_scatter(x=df["timestamp"], y=df[x_col], name= "X axis")
            fig.add_scatter(x=df["timestamp"], y=df[y_col], name= "Y axis")
            fig.add_scatter(x=df["timestamp"], y=df[z_col], name= "Z axis")
            st.plotly_chart(fig, use_container_width=True)

for sensor in ["Accelerometer",  "Gyrometer", "Magnetometer", "Temperature Sensor"]:
    
   plot_2d_xyz(plot_data, sensor, locs=sensor_locs[sensor_dic[sensor]])
   pass

# Since all sensors are present at the dashboard and above/below the suspension, this generates histograms and plots over time for each sensor location and axis
for location in ["dashboard", "below_suspension", "above_suspension"]:
   # utils.plot_1d_3col(slyce, "acc", location, "Distribution")
   # utils.plot_2d_3col(slyce, "acc", location, "Over time")
    pass

#Show data
if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(gps_df.head())
    st.write(dataset_gps_mpu_left.head())
