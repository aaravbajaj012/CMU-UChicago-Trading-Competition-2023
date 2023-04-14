import numpy as np
import pandas as pd
import scipy

#########################################################################
## Change this code to take in all asset price data and predictions    ##
## for one day and allocate your portfolio accordingly.                ##
#########################################################################



# read the historical price data from the csv file called Training Data_Case 3.csv
historical_price_data = pd.read_csv('Training Data_Case 3.csv', index_col=0)

# split up the data into training and testing
price_data = historical_price_data.iloc[:int(len(historical_price_data)*0.7),:]
testing = historical_price_data.iloc[int(len(historical_price_data)*0.7):,:]


def allocate_portfolio(asset_prices):
    #insert code here


def grading(testing): #testing is a pandas dataframe with price data, index and column names don't matter
    weights = np.full(shape=(len(testing.index),10), fill_value=0.0)
    for i in range(0,len(testing)):
        unnormed = np.array(allocate_portfolio(list(testing.iloc[i,:])))
        positive = np.absolute(unnormed)
        normed = positive/np.sum(positive)
        weights[i]=list(normed)
    capital = [1]
    for i in range(len(testing) - 1):
        shares = capital[-1] * np.array(weights[i]) / np.array(testing.iloc[i,:])
        capital.append(float(np.matmul(np.reshape(shares, (1,10)),np.array(testing.iloc[i+1,:]))))
    returns = (np.array(capital[1:]) - np.array(capital[:-1]))/np.array(capital[:-1])
    return np.mean(returns)/ np.std(returns) * (252 ** 0.5), capital, weights



# calculate the Sharpe ratio of the portfolio
sharpe_ratio, capital, weights = grading(testing)
# print the Sharpe ratio
print(sharpe_ratio)
