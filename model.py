import json
import requests
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from datetime import datetime as dt
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.svm import SVR
from datetime import date, timedelta

def make_api_request(url):
    try:
        response = requests.get(url)
        response.raise_for_status()

        # Check for empty content
        if not response.text:
            print("Empty response received.")
            return None

        # Try to parse the response as JSON
        try:
            data = response.json()
        except json.JSONDecodeError as e:
            print("Error decoding JSON:", e)
            print("Response text:", response.text)
            return None

        return data

    except requests.exceptions.HTTPError as errh:
        print("HTTP Error:", errh)
        return None
    except requests.exceptions.RequestException as err:
        print("Request Error:", err)
        return None

def prediction(stock, n_days):
    df = yf.download(stock, period='60d')
    df.reset_index(inplace=True)
    df['Day'] = df.index

    days = list()
    for i in range(len(df.Day)):
        days.append([i])

    X = days
    Y = df[['Close']]

    x_train, x_test, y_train, y_test = train_test_split(X, Y, test_size=0.1, shuffle=False)

    gsc = GridSearchCV(
        estimator=SVR(kernel='rbf'),
        param_grid={
            'C': [0.001, 0.01, 0.1, 1, 100, 1000],
            'epsilon': [0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5, 10, 50, 100, 150, 1000],
            'gamma': [0.0001, 0.001, 0.005, 0.1, 1, 3, 5, 8, 40, 100, 1000]
        },
        cv=5,
        scoring='neg_mean_absolute_error',
        verbose=0,
        n_jobs=-1
    )

    y_train = y_train.values.ravel()
    grid_result = gsc.fit(x_train, y_train)
    best_params = grid_result.best_params_
    best_svr = SVR(kernel='rbf', C=best_params["C"], epsilon=best_params["epsilon"], gamma=best_params["gamma"], max_iter=-1)

    rbf_svr = best_svr
    rbf_svr.fit(x_train, y_train)

    output_days = list()
    for i in range(1, n_days):
        output_days.append([i + x_test[-1][0]])

    dates = []
    current = date.today()
    for i in range(n_days):
        current += timedelta(days=1)
        dates.append(current)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=rbf_svr.predict(output_days), mode='lines+markers', name='data'))
    fig.update_layout(title="Predicted Close Price of next " + str(n_days - 1) + " days",
                      xaxis_title="Date",
                      yaxis_title="Closed Price")

    return fig


