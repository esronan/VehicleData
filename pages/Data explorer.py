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
        range(1,10)
    )
    sensor = st.selectbox(
        "Choose sensor",
        ["Accelerometer", "Magnetometer", "GNSS", "Gyrometer", "Temperature Sensor"]
    )

# Initiate dictionary to convert user selected sensor to the csv tag
sensor_dic = {"Accelerometer": "acc", "Magnetometer": "mag", "GNSS":"dop", "Gyrometer": "gyro", "Temperature Sensor":"temp"}


# Load files
gps_coords = utils.load_csv(f"data/dataset_gps ({drive_nr}).csv")
dataset_gps_mpu_left = pd.read_csv("data/dataset_gps_mpu_left.csv")


    
# fig = px.histogram(dataset_gps_mpu_left, x="acc_x_dashboard", nbins=200)
# st.plotly_chart(fig)


# Since all sensors are present at the dashboard and above/below the suspension, this generates histograms and plots over time for each sensor location and axis
for location in ["dashboard", "below_suspension", "above_suspension"]:
    utils.plot_1d_3col(dataset_gps_mpu_left, "acc", location, "Distribution")
    utils.plot_2d_3col(dataset_gps_mpu_left, "acc", location, "Over time")

st.video()

#Show data
if st.checkbox('Show raw data'):
    st.subheader('Raw data')
    st.write(gps_coords.head())
    st.write(dataset_gps_mpu_left.head())
