# Description: Short example for Time series for unemployment and natural gas using Prophet and Plotly in Python.



import plotly.graph_objs as go

df.plot()

df.reset_index(inplace=True)

df.columns = ["ds", "y"]
df.dropna(inplace= True)
model = Prophet()
model.fit(df)

future = model.make_future_dataframe(periods=12)

forecast = model.predict(future)
forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()


def timeseries(df, x, yhat, lower, upper, actual, save = False):

    fig = go.Figure([
        go.Scatter(
            name='Measurement',
            x=df[x],
            y=df['yhat'],
            mode='lines',
            line=dict(color='rgb(31, 119, 180)'),
            showlegend=False
        ),
        go.Scatter(
            name='Upper Bound',
            x=df[x],
            y=df[upper],
            mode='lines',
            marker=dict(color="#444"),
            line=dict(width=0),
            showlegend=False
        ),
        go.Scatter(
            name='Lower Bound',
            x=df[x],
            y=df[lower],
            marker=dict(color="#444"),
            line=dict(width=0),
            mode='lines',
            fillcolor='rgba(68, 68, 68, 0.3)',
            fill='tonexty',
            showlegend=False
        )
    ])
    fig.update_layout(
        yaxis_title='Unemployment Rate',
        title='Unemployment rate estimate using Prophet Forecast',
        hovermode="x"
    )
    fig.add_trace(go.Scatter(x=actual['ds'], y=actual["y"],
                    mode='lines+markers',
                    name='Actual values',
                    showlegend=False))
    fig.show()
    
    if save: 
        fig.write_html("unemployment rate.html")

forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]

df1 = web.DataReader('DHHNGSP', 'fred', start, end)
df1.plot()

df1.reset_index(inplace=True)
df1.columns = ["ds", "y"]
m = Prophet()
m.fit(df1)
future = m.make_future_dataframe(periods=12, freq='MS')
fcst = m.predict(future)
fig = m.plot(fcst)

df1.set_index("ds", inplace=True)

def timeseries_trad(df,  y, periods = 10, save = False):
    shift = df.shift(periods=periods, freq="M")
    fig = go.Figure([
        go.Scatter(
            name='Actual values',
            x=df.index, 
            y=df[y],
            mode='lines+markers',
            showlegend=False
        ),
        go.Scatter(
            name='Naive Forecast',
            x=shift.index,
            y=shift[y],
            mode='lines',
            marker=dict(color="#444"),
            line=dict(width=1),
            showlegend=False
        ),
    ])
    fig.update_layout(
        yaxis_title='price',
        title='Henry Hub Natural Gas Spot Price using Prophet Forecast with shift of {}'.format(periods),
        hovermode="x"
    )
    
    fig.show()
    
    if save: 
        fig.write_html("timeseries_trad.html")

timeseries_trad(df1,  "y", periods = 10, save = False)
