#######################################################################################################################
# We'll get historical data from coinmarketcap.com.                                                                   #
# Their API doesn't actually let us query for this information without paying, so we'll scrape it from their website. #
#                                                                                                                     #
# Here is the URL I'm using to get the All Time historical data, you'll need to change the end parameter:             #
# https://coinmarketcap.com/currencies/bitcoin/historical-data/?start=20130428&end=20200405                           #
#                                                                                                                     #
# I then inspected the webpage and posted the html into the txt file coinmarketcap_historical_html.txt                #
#######################################################################################################################

###########
# IMPORTS #
###########

import pandas
from bs4 import BeautifulSoup

#############
# FUNCTIONS #
#############


# parses text out of a row (1D array) of html tags
def get_parsed_row(row):
    for item in range(len(row)):
        row[item] = row[item].get_text().replace(',', '').replace('-', 'NaN')
    return row

###########################
# BEAUTIFULSOUP DATA PREP #
###########################


# open coinmarketcap html file with historical data
with open('coinmarketcap_historical_html.txt', encoding='utf-8') as fp:
    soup = BeautifulSoup(fp, "lxml")

# Get html table of historical data
table_div = soup.find(("div", {"class": "cmc-table__table-wrapper-outer"}))
table = table_div.find('table')

# pull out headers and rows
headers = table.thead.tr.find_all('th')
rows = table_div.find('tbody').find_all('tr')

# initialize 2d array for data
data = []

# get headers
headers = get_parsed_row(headers)

# get rows
for row in rows:
    tds = row.find_all('td')
    tds = get_parsed_row(tds)
    data.append(tds)

# convert to pandas dataframe
pd = pandas.DataFrame(data=data, columns=headers)
pd.set_index("Date", inplace=True)
pd.index = pandas.to_datetime(pd.index, errors="ignore")
pd = pd.astype(float)

###################################
# Add 5 day moving average column #
###################################

pd = pd.iloc[::-1]

MA_WINDOW = 5
pd['MA5'] = pd.iloc[:, 0].rolling(window=MA_WINDOW).mean()

pd = pd.iloc[::-1]

##############
# EXPORT CSV #
##############

pd.to_csv('pandas_historical_data.csv')

############
# BACKTEST #
############

# Reverse list
pd = pd.iloc[::-1]

# Start amounts of USD and BTC
STARTING_MONEY = 100
STARTING_BTC = 0

# Set starting amounts
money = STARTING_MONEY
btc = STARTING_BTC

# Initial price of BTC
first = pd['Open*'][0]

# Number of times we make buy and sell trades
num_buys = 0
num_sells = 0

# Columns we'll use for our small and big moving averages
maSmallStr = 'Open*'
maBigStr = 'MA5'

# Iterate over historical data and simulate trades
for i in range(7, pd['Open*'].size, 1):
    # Relevant data points for today
    maSmall = pd[maSmallStr][i]
    maBig = pd[maBigStr][i]
    curr = pd['Open*'][i]

    # Relevant data points for yesterday
    maSmallPrev = pd[maSmallStr][i - 1]
    maBigPrev = pd[maBigStr][i - 1]

    # Determine trend for yesterday and today
    trendPrev = maSmallPrev > maBigPrev
    trend = maSmall > maBig

    # If the trend has reversed, make a trade
    if maBig < maSmall and trend != trendPrev:  # BUY (Gonna go up)
        # Determine the amount of BTC we can afford
        size = btc + ((money / 1.005) / curr)

        # Adjust USD and BTC amounts as though we had made the trade
        money = 0
        btc = btc + size

        # Reflect that we have made a purchase of BTC
        num_buys = num_buys + 1
    if maSmall < maBig and trend != trendPrev:  # SELL (Gonna go down)
        # Determine the amount of USD we'll get from selling all BTC
        money = money + .995 * (curr * btc)
        btc = 0

        # Reflect that we have made a sale of BTC
        num_sells = num_sells + 1

# Print out data
print("Buys: " + str(num_buys))
print("Sells: " + str(num_sells))
print("End USD:" + money)
print("End BTC:" + btc)

# Difference between inital money/btc and current money/btc
usd_gain = (money - STARTING_MONEY + curr * (btc - STARTING_BTC))
print("$ Gain: " + str(usd_gain))

# % Gain between initial value and current value
print("% Gain:" + str(100 * (usd_gain / STARTING_MONEY) - 100))

# $ Gain if we had bought and held the entire time
print("Hold $ Gains:" + str(((STARTING_MONEY / first) * curr) - STARTING_MONEY))
