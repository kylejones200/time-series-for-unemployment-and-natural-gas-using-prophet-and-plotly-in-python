# Time series for unemployment and natural gas using Prophet and Plotly in Python

This simple project uses Bayesian time series to predict unemployment in
the US. We visualize the data using Plotly. Then we repeat the...

### Time series for unemployment and natural gas using Prophet and Plotly in Python
This simple project uses Bayesian time series to predict unemployment in
the US. We visualize the data using Plotly. Then we repeat the process
using a different dataset --- the price of natural gas in the US. I made
this project to show how easily we can make powerful time series
forecasts without having to get into complicated math.

We begin by importing the python modules we will use. For this project,
I use \`pandas_datareader\` to fetch data from the [Federal Reserve
Economic Data \| FRED](https://fred.stlouisfed.org/).

I like using FRED data because it is free and easily accessible via API.


Now we import the data and take a look at the top 5 rows.


Since the data is univariate and indexed on time, we can use the pandas
plot function to make a simple graph. For data that has more features
(aka columns), this is not the best approach.



<figcaption>Unemployment rate in US from Jan 1, 2010 to Oct
20, 2024</figcaption>


We see a huge spike from 2020--2021. That is unemployment associated
with COVID-19.

Now that we have the data, we can build a model to predict unemployment.
I use the [Prophet](https://facebook.github.io/prophet/) model from Facebook that creates a
Bayesian structural time series. The graph shows the actual values
(dots), predictive values (blue solid line), and predicted range (light
blue field).

Note that we have to create columns with specific names "ds" and "y".
Prophet is a picky module and only works with columns that have these
names.



<figcaption>Unemployment rate values are dots. Dark blue line is Prophet
forecast and shaded area is area of uncertainty.</figcaption>


You can see the forecasted unemployment for the next 12 months.

#### Graphing the forecast with Plotly
Plotly is a declarative framework to build interactive graphs.



This shows the same data using a plot from Plotly. If you run this, it
will create an interactive graph that lets you hover over values.

### Forecasting the Henry Hub Natural Gas Spot Price
Now that we have a pattern we used for looking at unemployment, we can
easily look at other data. I use the Henry Hub Natural Gas Spot Price
which is the index price for natural gas in the US.



There is a huge spike in 2020--2021 that looks a lot like the
unemployment spike. This dramatic increase is also associated with
COVID-19.


Let's take a look at the forecasted data.


<figcaption>Henry Hub price actuals are dots. Dark blue line is Prophet
forecast and shaded area is area of uncertainty.</figcaption>


#### Time shifting
Another approach to time series forecasting is to shift the data.
Basically we assume the price next month will be the price today. This
graph shows the shifted value in black. As you can see, the forecast
from Prophet is better than the Naive forecast.
