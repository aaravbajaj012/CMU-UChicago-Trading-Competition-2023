import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy import optimize

# Importing the dataset

# Read the futures_2020 and futures_2021 and futures_2022 data from the csv file
futures_dfs = [pd.read_csv('futures_2020.csv'), pd.read_csv('futures_2021.csv'), pd.read_csv('futures_2022.csv')]

# Read the weather_2020 and weather_2021 and weather_2022 data from the csv file
weathers_dfs = [pd.read_csv('weather_2020.csv'), pd.read_csv('weather_2021.csv'), pd.read_csv('weather_2022.csv')]

# for each of the weather dataframes, check what the maximum daily change in weather index is
# print the maximum daily change in weather index for each year

for year in range(3):
    print(weathers_dfs[year]['weather'].diff().max())


# def obj_fn(shift, year):
#     return futures_dfs[year]['SBL'].cov(weathers_dfs[year]['weather'].rolling(shift).mean())


# shifts = []

# for year in range(3):
#     max_cov = None
#     max_shift = None
#     # Find the shift that maximizes the covariance by brute force
#     for i in range(2, 50):
#         if max_cov is None or obj_fn(i, year) > max_cov:
#             max_cov = obj_fn(i, year)
#             max_shift = i

#     shifts.append(max_shift)

# shifts = [20, 20, 20]

# # apply a rolling mean of 5 days to the weather data
# for year in range(3):
#     weathers_dfs[year]['weather'] = weathers_dfs[year]['weather'].rolling(shifts[year]).mean()

# # print the correlation between the futures and weather data
# for year in range(3):
#     print(futures_dfs[year]['SBL'].corr(weathers_dfs[year]['weather']))

# print(shifts)

# # plot the weather day and the SBL futures for each year on the same plot with two axes
# # plot all three plots on one figure as subplots

# # fig, axs = plt.subplots(3, 1, figsize=(10, 10))

# # for year in range(3):
# #     axs2 = axs[year].twinx()
    
# #     axs[year].plot(futures_dfs[year]['SBL'], label='SBL', color='red')
# #     axs[year].twinx().plot(weathers_dfs[year]['weather'], label='weather', color='blue')
# #     axs[year].set_title(f'Year {year}')
# #     axs[year].legend()


# # plt.show()


# # plot the weather on the x-axis and the SBL futures on the y-axis for each year on the same plot
# # plot all three plots on one figure as subplots

# # fig, axs = plt.subplots(3, 1, figsize=(10, 10))

# # for year in range(3):
# #     axs[year].scatter(weathers_dfs[year]['weather'], futures_dfs[year]['SBL'])
# #     axs[year].set_title(f'Year {year}')

# # plt.show()

# # # for each year, drop the NaN rows, and only keep the rows with indices that exist in both dataframes
# for year in range(3):
#     futures_dfs[year] = futures_dfs[year].dropna()
#     weathers_dfs[year] = weathers_dfs[year].dropna()

#     futures_dfs[year] = futures_dfs[year].loc[weathers_dfs[year].index]
#     weathers_dfs[year] = weathers_dfs[year].loc[futures_dfs[year].index]

# # # find the best fit line for each year and find the constants a and b for the equation y = ax + b
# # # print the a and b for each year

# mss = []
# bss = []

# for year in range(3):
#     m, b = np.polyfit(weathers_dfs[year]['weather'], futures_dfs[year]['SBL'], 1)

#     mss.append(m)
#     bss.append(b)

# m_slope, m_yint = np.polyfit([0, 1, 2], mss, 1)
# b_slope, b_yint = np.polyfit([0, 1, 2], bss, 1)

# for i in range(3, 7):
#     print("202" + str(i) + ": m =", m_slope * i + m_yint, " b =", b_slope * i + b_yint)