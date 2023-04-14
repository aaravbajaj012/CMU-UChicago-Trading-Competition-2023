import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Importing the dataset

# Read the futures_2020 and futures_2021 and futures_2022 data from the csv file
futures_2020 = pd.read_csv('futures_2020.csv')
futures_2021 = pd.read_csv('futures_2021.csv')
futures_2022 = pd.read_csv('futures_2022.csv')

# Read the weather_2020 and weather_2021 and weather_2022 data from the csv file
weather_2020 = pd.read_csv('weather_2020.csv')
weather_2021 = pd.read_csv('weather_2021.csv')
weather_2022 = pd.read_csv('weather_2022.csv')

# for each column in futures_2022, plot the data
# have a legend for each column
# make the ylim scale from 45 to 60
# make the title "Futures 2022"

plt.figure(figsize=(10, 6))
for column in futures_2022:
    if column:
        plt.plot(futures_2022[column], label=column)
plt.legend()
plt.ylim(48, 62)
plt.title('Futures 2022')
plt.show()  


# for each column in weather_2022, plot the data
# have a legend for each column
# make the ylim scale from 45 to 60
# make the title "Weather 2022"
# plot the expiry lines for each future

plt.figure(figsize=(10, 6))
for column in weather_2022:
    if column:
        plt.plot(weather_2022[column], label=column)
plt.axvline(x=21, color='r', linestyle='--')
plt.axvline(x=42, color='r', linestyle='--')
plt.axvline(x=63, color='r', linestyle='--')
plt.axvline(x=84, color='r', linestyle='--')
plt.axvline(x=105, color='r', linestyle='--')
plt.axvline(x=126, color='r', linestyle='--')
plt.axvline(x=147, color='r', linestyle='--')
plt.axvline(x=168, color='r', linestyle='--')
plt.axvline(x=189, color='r', linestyle='--')
plt.axvline(x=210, color='r', linestyle='--')
plt.axvline(x=231, color='r', linestyle='--')
plt.axvline(x=252, color='r', linestyle='--')
plt.legend()
plt.ylim(-3, 3)
plt.title('Weather 2022')
plt.show()

# look for a correlation between the futures and weather
# try to fit a regression line to the data
# plot the regression line on top of the data

