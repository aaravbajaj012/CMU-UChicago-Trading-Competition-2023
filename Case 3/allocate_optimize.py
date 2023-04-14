import numpy as np
import pandas as pd
import scipy

#########################################################################
## Change this code to take in all asset price data and predictions    ##
## for one day and allocate your portfolio accordingly.                ##
#########################################################################

N_DAYS = 252
N_RUNS = 5

PCT_TRAINING = 0.5

all_data = pd.read_csv('Training Data_Case 3.csv',header=0, index_col=0)

# get the first int(len(all_data) * PCT_TRAINING) rows of data
data = all_data.iloc[:int(len(all_data) * PCT_TRAINING), :]



def SR(weights, mean, cov):
    norm_weights = weights / np.sum(weights)

    if any([x < 0 for x in norm_weights]):
        raise Exception("Negative weights not allowed")
    
    return np.dot(norm_weights, mean) / np.sqrt(np.dot(norm_weights.T, np.dot(cov, norm_weights)))


def allocate_portfolio(asset_prices):
    global data
    # add asset_prices as a new row to data using pd.concat (DO NOT USE pd.append)
    data = pd.concat([data, pd.DataFrame([asset_prices], columns=data.columns)], ignore_index=True)

    df_returns = data.pct_change()
    df_returns = df_returns.dropna()

    mean = np.array(df_returns.mean())
    cov = np.array(df_returns.cov())

    best_SR = None
    best_SR_weights = None

    for i in range(N_RUNS):
        try:
            res = scipy.optimize.minimize(lambda x: -SR(x, mean, cov), np.random.rand(10), method="L-BFGS-B", bounds=((0, 1), ) * 10)
            res_weights = res.x
            res_SR = SR(res_weights, mean, cov)

            if best_SR == None or res_SR > best_SR:
                best_SR = res_SR
                best_SR_weights = res_weights
        except:
            pass

    return best_SR_weights

def grading(testing): #testing is a pandas dataframe with price data, index and column names don't matter
    weights = np.full(shape=(len(testing.index),10), fill_value=0.0)
    for i in range(0,len(testing)):
        # print(i, "/", len(testing))
        unnormed = np.array(allocate_portfolio(list(testing.iloc[i,:])))
        positive = np.absolute(unnormed)
        normed = positive/np.sum(positive)
        weights[i]=list(normed)
    capital = [1]
    for i in range(len(testing) - 1):
        # print(i, "/", len(testing) - 1)
        shares = capital[-1] * np.array(weights[i]) / np.array(testing.iloc[i,:])
        capital.append(float(np.matmul(np.reshape(shares, (1,10)),np.array(testing.iloc[i+1,:]))))
    returns = (np.array(capital[1:]) - np.array(capital[:-1]))/np.array(capital[:-1])
    return (np.mean(returns) / np.std(returns)) * (252 ** 0.5), capital, weights


# testing_data = all_data.iloc[int(len(all_data) * PCT_TRAINING):, :]

for i in range(1, 10):
    pct_training = i / 10
    testing_data = all_data.iloc[int(len(all_data) * (pct_training)):, :]
    data = all_data.iloc[:int(len(all_data) * pct_training), :]
    print("training/testing:", str(int(pct_training * 100)) + "/" + str(int((1 - pct_training) * 100)), "-- sharpe ratio:", grading(testing_data)[0])