import streamlit as st
import pandas as pd
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from geopy.distance import geodesic
import plotly.express as px

# Load CSV file and keep in memory once loaded
@st.cache_data
def load_csv(url):
    return pd.read_csv(url)

# Calculate total distance driven
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


# Scale a column in question to a range between min and max (to allow for a broader colour spectrum)
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

#Plot a sensor's reading in each axis against time
def plot_2d_3col(df, variable, sensor_location, title):
    st.header(title)
    col1, col2, col3 = st.columns(3)
    with col1: 
        y_col = variable + "_x_" + sensor_location
        fig = px.line(df, x="timestamp", y=y_col, title='X axis')
        st.plotly_chart(fig, use_container_width=True)
    with col2: 
        y_col = variable + "_y_" + sensor_location
        fig = px.line(df, x="timestamp", y=y_col, title='Y axis')
        st.plotly_chart(fig, use_container_width=True)
    with col3: 
        y_col = variable + "_z_" + sensor_location
        fig = px.line(df, x="timestamp", y=y_col, title='Z axis')
        st.plotly_chart(fig, use_container_width=True)

#Create a histogram of the values of a sensor's reading in each axis
def plot_1d_3col(df, variable, sensor_location, title):
    st.header(title)
    col1, col2, col3 = st.columns(3)
    with col1: 
        x_col = variable + "_x_" + sensor_location
        fig = px.histogram(df, x=x_col, histfunc="count", title='X axis')
        st.plotly_chart(fig, use_container_width=True)
    with col2: 
        x_col = variable + "_y_" + sensor_location
        fig = px.histogram(df, x=x_col, histfunc="count", title='Y axis')
        st.plotly_chart(fig, use_container_width=True)
    with col3: 
        x_col = variable + "_z_" + sensor_location
        fig = px.histogram(df, x=x_col, histfunc="count", title='Z axis')
        st.plotly_chart(fig, use_container_width=True)



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

# Calculate acceleration using difference in velocity between time points
def calc_acceleration(df, time_col, velocity_col):
    df["acceleration"] = df[velocity_col].diff()/df[time_col]
    return df

# Calculate amount of time with a poor level of DoP b
def calc_poor_dop(df, dop_col, elapsed_time_col):
    total_time = 0
    for i, row in df.iterrows():
        if abs(row[dop_col]) > 20: #20 = poor precision
            total_time += df.at[i,elapsed_time_col] #elapsed time is amount of time since last sensor reading
    return total_time

def label_data(df, label_df, label_classes):
    for key in label_classes.keys():
        label_df[key] = label_df[label_classes[key]].idxmax(axis=1)
    label_df = label_df[label_classes.keys()]
    
    df = pd.concat([df, label_df], axis=1)

    return df