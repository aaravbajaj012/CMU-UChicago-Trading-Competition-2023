import numpy as np
import pandas as pd
from scipy.optimize import minimize

# read the historical price data from the csv file called Training Data_Case 3.csv
historical_price_data = pd.read_csv('Training Data_Case 3.csv', index_col=0)

# split up the data into training and testing
price_data = historical_price_data.iloc[:int(len(historical_price_data)*0.7),:]
testing = historical_price_data.iloc[int(len(historical_price_data)*0.7):,:]

# Define the covariance matrix and mean returns

mean_returns = price_data.mean()

def allocate_portfolio(asset_prices):

    global price_data

    price_data = pd.concat([price_data, pd.DataFrame([asset_prices], columns = price_data.columns)], ignore_index=True)
    returns = price_data.pct_change().dropna()

    returns_data = price_data.pct_change().dropna() # calculate returns from price data and remove NaNs
    covariance_matrix = returns_data.cov() # estimate covariance matrix
    # This function takes in a vector of asset prices for one day and returns the weights of the stocks in the portfolio
    # Implement Markowitz portfolio optimization

    # Define the objective function for minimizing portfolio risk (negative of portfolio return)
    def objective_function(weights):
        portfolio_return = np.dot(weights, mean_returns)
        portfolio_risk = np.sqrt(np.dot(weights, np.dot(covariance_matrix, weights)))
        return -portfolio_return / portfolio_risk

    # Define the constraints for portfolio weights (sum of weights = 1)
    constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})

    # Define the bounds for portfolio weights (0 <= weight <= 1)
    bounds = [(0, 1)] * len(asset_prices)

    # Initialize the initial guess for portfolio weights (equal weights)
    initial_guess = np.ones(len(asset_prices)) / len(asset_prices)

    # Minimize the objective function subject to constraints and bounds
    result = minimize(objective_function, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)
    optimal_weights = result.x

    return optimal_weights


def grading(testing):
    # This function calculates the Sharpe ratio of the portfolio based on the weights obtained from the allocate_portfolio() function
    weights = np.full(shape=(len(testing.index),10), fill_value=0.0)
    for i in range(len(testing)):
        unnormed = np.array(allocate_portfolio(list(testing.iloc[i,:])))
        positive = np.absolute(unnormed)
        normed = positive/np.sum(positive)
        weights[i] = list(normed)
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
