
import numpy as np
import pandas as pd
from scipy.optimize import minimize


# read the historical price data from the csv file called Training Data_Case 3.csv
historical_price_data = pd.read_csv('Training Data_Case 3.csv', index_col=0)

# split up the data into training and testing
price_data = historical_price_data.iloc[:int(len(historical_price_data)*0.5),:]
testing = historical_price_data.iloc[int(len(historical_price_data)*0.5):,:]

ALPHA = 0.05


def calculate_risk_contribution(weights, cov_matrix):
    """
    Calculate the risk contribution of each asset in the portfolio.
    """
    portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
    asset_volatility = np.sqrt(np.diag(cov_matrix))
    risk_contribution = (weights * asset_volatility) / np.sqrt(portfolio_variance)
    return risk_contribution

def calculate_cvar(weights, returns, alpha):
    """
    Calculate the Conditional Value at Risk (CVaR) of the portfolio.
    """
    portfolio_returns = np.dot(returns, weights)
    sorted_returns = np.sort(portfolio_returns)
    index = int(np.ceil(alpha * len(portfolio_returns)))
    cvar = np.mean(sorted_returns[:index])
    return cvar

def risk_parity_allocation_with_cvar(alpha):
    """
    Perform risk parity allocation based on historical price data with CVaR.
    """
    # Calculate returns from price data
    returns = price_data.pct_change().dropna().values

    # Estimate covariance matrix
    cov_matrix = np.cov(returns.T)

    # Initialize equal weights
    n_assets = cov_matrix.shape[0]
    init_weights = np.ones(n_assets) / n_assets

    # Define optimization function for risk parity with CVaR
    def risk_parity_objective_with_cvar(weights, cov_matrix, alpha):
        risk_contributions = calculate_risk_contribution(weights, cov_matrix)
        # Minimize the difference between CVaR-based risk contributions and actual risk contributions
        cvar = calculate_cvar(weights, returns, alpha)
        return np.sum((risk_contributions - cvar) ** 2)

    # Set constraints for optimization
    constraints = [{'type': 'eq', 'fun': lambda x: np.sum(x) - 1}, # sum of weights must be 1
                   {'type': 'ineq', 'fun': lambda x: x}, # weights must be non-negative
                   {'type': 'ineq', 'fun': lambda x: 1 - x}] # weights must be less than or equal to 1

    # Run optimization
    result = minimize(risk_parity_objective_with_cvar, init_weights, args=(cov_matrix, alpha),
                      method='SLSQP', constraints=constraints)

    # Get optimal weights
    weights = result.x

    return weights

def allocate_portfolio(new_prices):
    global price_data

    alpha = ALPHA

    # Add new prices to price data
    price_data = pd.concat([price_data, pd.DataFrame([new_prices], columns = price_data.columns)], ignore_index=True)

    # Perform risk parity allocation with CVaR
    weights = risk_parity_allocation_with_cvar(alpha)

    return weights

#def grading(testing, alpha): #

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

# test different train test splits
for i in range(1,10):
     price_data = historical_price_data.iloc[:int(len(historical_price_data)*0.1*i),:]
     testing = historical_price_data.iloc[int(len(historical_price_data)*0.1*i):,:]
     sharpe_ratio, capital, weights = grading(testing)
     print(sharpe_ratio)


# print the Sharpe ratio
print(sharpe_ratio)
