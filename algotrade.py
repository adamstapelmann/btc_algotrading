#########################################################
# Evaluates which action to perform (buy/sell/hold) and #
# places an order to Coinbase Pro if necessary          #
#                                                       #
# This is intended to be called once a day              #
#########################################################

###########
# IMPORTS #
###########

import pandas
import datetime
from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import cbpro
from datetime import datetime
import numpy
import hmac
import requests
import hashlib
import time
import base64
from requests.auth import AuthBase

#############
# CONSTANTS #
#############

# Coinbase Pro API information
# https://docs.pro.coinbase.com/#api
CBPRO_PASSPHRASE = ''
CBPRO_SECRET = ''
CBPRO_API_KEY = ''

# Coinbase pro API base url
CBPRO_BASE_URL = 'https://api.pro.coinbase.com/'

# CSV file we'll read and write data to
FILE_NAME = 'C:/Users/afsta/Repo/btc_algotrading/venv/pandas_historical_data.csv'

##########################
# COINBASE REQUEST CLASS #
##########################


# Create custom authentication for Exchange
class CoinbaseExchangeAuth(AuthBase):
    def __init__(self, api_key, secret_key, passphrase):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase

    def __call__(self, request):
        timestamp = str(time.time())
        message = timestamp + request.method + request.path_url + (request.body or '')
        hmac_key = base64.b64decode(self.secret_key)
        signature = hmac.new(hmac_key, message.encode('ascii'), hashlib.sha256)
        signature_b64 = base64.b64encode(signature.digest()).decode('utf-8')

        request.headers.update({
            'CB-ACCESS-SIGN': signature_b64,
            'CB-ACCESS-TIMESTAMP': timestamp,
            'CB-ACCESS-KEY': self.api_key,
            'CB-ACCESS-PASSPHRASE': self.passphrase,
            'Content-Type': 'application/json'
        })
        return request


#######################
# GET HISTORICAL DATA #
#######################

# Read in data from csv to a pandas dataframe
pd = pandas.read_csv(FILE_NAME)
pd.set_index("Date", inplace=True)

#######################
# GET QUOTE FOR TODAY #
#######################

# Private cbpro API request for current quote
auth = CoinbaseExchangeAuth(CBPRO_API_KEY, CBPRO_SECRET, CBPRO_PASSPHRASE)
quote = requests.get(CBPRO_BASE_URL + 'products/BTC-USD/stats', auth=auth).json()

# Get datetime and price from api response
dt = datetime.now()
price = float(quote['last'])

##############################
# CALCULATE RELEVANT METRICS #
##############################

# Calculate 5 day moving average
interval = 5
index = 'MA' + str(interval)
# Average case
if pd[index].size > interval - 1:
    ma5prev = float(pd[index][0])
    priceLast = float(pd['Open*'][interval - 1])
    ma5 = (interval * ma5prev + price - priceLast) / interval
# We have to calculate the first average
elif pd[index].size == interval - 1:
    ma5 = pd['Open*'].mean()
# Default for base cases
else:
    ma5 = numpy.nan

##########################
# UPDATE HISTORICAL DATA #
##########################

# Today's date
date_today = datetime.date(datetime.now())

# The most recent date in our historical data set
last_recorded_date = pd.index.tolist()[0]

# Update historical data if we're out of date
if date_today != datetime.strptime(last_recorded_date, '%Y-%m-%d').date():
    # Get relevant data points
    open_price = quote['open']
    high = quote['high']
    low = quote['low']
    volume = quote['volume']

    # Add data to a row and then to the dataframe
    row = [[open_price, high, low, numpy.nan, numpy.nan, numpy.nan, float(ma5)]]
    row_df = pandas.DataFrame(row, index=[date_today], columns=pd.columns)
    pd = pandas.concat([row_df, pd])
    pd.index.name = "Date"

    # Write our dataframe to the csv
    pd.to_csv(FILE_NAME)

##########################
# EVALUATE TRADE DETAILS #
##########################

# Get account data from API
auth = CoinbaseExchangeAuth(CBPRO_API_KEY, CBPRO_SECRET, CBPRO_PASSPHRASE)
data = requests.get(CBPRO_BASE_URL + 'accounts', auth=auth).json()

# Determine how much USD and BTC we have
available_btc = 0
available_usd = 0
for obj in data:
    if obj['currency'] == "BTC":
        available_btc = float(obj['available'])
    if obj['currency'] == "USD":
        available_usd = float(obj['available'])

# Relevant data points for today
maSmall = float(pd['Open*'][0])
maBig = float(pd['MA5'][0])

# Relevant data points for yesterday
maSmallPrev = float(pd['Open*'][1])
maBigPrev = float(pd['MA5'][1])

# Determine trend for yesterday and today
trendPrev = maSmallPrev > maBigPrev
trend = maSmall > maBig

###############
# PLACE ORDER #
###############

# Make the trade
if maBig < maSmall and trend != trendPrev:  # BUY (Gonna go up)
    # Always spend all money
    post_obj = {'product_id': 'BTC-USD', 'side': 'buy', 'funds': str(available_usd), 'type': 'market'}
    data = requests.post(url=CBPRO_BASE_URL + 'orders', data=json.dumps(post_obj), auth=auth)
if maSmall < maBig and trend != trendPrev:  # SELL (Gonna go down)
    # Always sell all btc
    post_obj = {'product_id': 'BTC-USD', 'side': 'sell', 'size': str(available_btc), 'type': 'market'}
    data = requests.post(url=CBPRO_BASE_URL + 'orders', data=json.dumps(post_obj), auth=auth)
