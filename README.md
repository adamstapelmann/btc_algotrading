# Bitcoin Algotrading
Algotrading project for Bitcoin. This project seeks to analyze bitcoin metrics and make buy/sell trades in order to make profit off of the long term. Currently, we look for a switch in trend between the current price of bitcoin and the 5 day moving average.

## Set up
There is a lot of setup up for this, so bear with me. By the end of this, however, you should have all the necessary tools to mimic this stragey, and it shouldn't be too difficult to tweak the algorithm to have a different trading strategy.

### Get historical data
To get historical data, we need to scrape CoinMarketCap's website. They have an API to get it, but it costs money.

1. Go to this url: https://coinmarketcap.com/currencies/bitcoin/historical-data/?start=20130428&end=20200405
2. Adjust the dates to be current, then right click > view page source to see the html for the file.
3. Copy the HTML and paste it in a file in your project called "coinmarketcap_historical_html.txt"
4. Execute the preprocess.py python file. This should covert the html into a pandas dataframe and write this to a csv called "pandas_historical_data.csv"

### Get Coinbase Pro set up
We will need a portfolio on Coinbase Pro and an API key to be able to make trades.

1. Go to pro.coinbase.com and make an account.
2. Transfer as much money as you are comfortable to this account.
3. On the dropdown from your profile, select API. For you portfolio, add an API key and make sure to give it the View and Trade permissions. Keep track of the Passphrase, Secret, and Key.
4. In algotrade.py, add your Passphrase, Secret, and Key to the constants. Also adjust the FILE_NAME constant to have the full file path to your historical data csv file.

### Add a scheduled task
We will want to execute our trading code daily. To do this, we will set up a scheduled task (Windows computers only).

1. Edit the .BAT file to have your file path rather than mine.
2. Start on step 4 of the guide on this website: https://datatofish.com/python-script-windows-scheduler/
3. Change the details as you see fit. I would at least check the box that allows the scheduler to wake up your computer to execute the task.
4. I set my script to execute at 7 pm.

### Backtest
If you are interested in changing the trading strategy, I've included my backtesting code at the bottom of preprocess.py. It just iterates over all our historical data and simulates trades using the same criteria as the actual algorithm. Then it prints out some relevant data to see how well we did.
