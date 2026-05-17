"""Auto-split from legacy monolithic script."""

import warnings
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns
from arch import arch_model
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from statsmodels.tsa.stattools import grangercausalitytests

def fetch_japan_natural_gas_price_data() -> None:
    warnings.filterwarnings("ignore")

    api_key = "8f058d10ec8c788296c040ea09e634d5"

    japan_gas = fetch_fred_data("PNGASJPUSDM", api_key)

    data = pd.DataFrame(
        {"date": japan_gas["date"], "price": japan_gas["value"]}
    ).set_index("date")

    data["rolling_mean_with_leakage"] = (
        data["price"].rolling(window=7, center=True).mean()
    )

    data["proper_rolling_mean"] = (
        data["price"].rolling(window=7, min_periods=1).mean().shift(1)
    )

    data["price_lag1"] = data["price"].shift(1)

    data["monthly_return"] = data["price"].pct_change(periods=30)

    test_dates_leak, y_test_leak, y_pred_leak = demonstrate_leakage(data)

    test_dates_proper, y_test_proper, y_pred_proper = demonstrate_proper_handling(data)

    mape_leak = mape(y_test_leak, y_pred_leak)

    mape_proper = mape(y_test_proper, y_pred_proper)

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15))

    ax1.plot(data.index, data["price"], label="Japan Gas Price", alpha=0.5)

    ax1.plot(
        data.index,
        data["rolling_mean_with_leakage"],
        label="Rolling Mean (with leakage)",
        linewidth=2,
    )

    ax1.plot(
        data.index,
        data["proper_rolling_mean"],
        label="Proper Rolling Mean (shifted)",
        linewidth=2,
    )

    ax1.set_title("Japan Natural Gas Prices with Different Rolling Means")

    ax1.legend()

    ax1.set_xlabel("Date")

    ax1.set_ylabel("Price")

    ax2.scatter(y_test_leak, y_pred_leak, alpha=0.5)

    ax2.plot(
        [y_test_leak.min(), y_test_leak.max()],
        [y_test_leak.min(), y_test_leak.max()],
        "r--",
        label="Perfect Prediction",
    )

    ax2.set_title(f"Predictions with Data Leakage\nMAPE: {mape_leak:.2f}%")

    ax2.set_xlabel("Actual Price")

    ax2.set_ylabel("Predicted Price")

    ax2.legend()

    ax3.scatter(y_test_proper, y_pred_proper, alpha=0.5)

    ax3.plot(
        [y_test_proper.min(), y_test_proper.max()],
        [y_test_proper.min(), y_test_proper.max()],
        "r--",
        label="Perfect Prediction",
    )

    ax3.set_title(
        f"Predictions with Proper Time Series Handling\nMAPE: {mape_proper:.2f}%"
    )

    ax3.set_xlabel("Actual Price")

    ax3.set_ylabel("Predicted Price")

    ax3.legend()

    plt.tight_layout()

    plt.show()

    print(f"MAPE with data leakage: {mape_leak:.2f}%")

    print(f"MAPE without data leakage: {mape_proper:.2f}%")

    print(f"Difference in MAPE: {mape_proper - mape_leak:.2f}%")

    plt.figure(figsize=(12, 6))

    plt.plot(test_dates_leak, y_test_leak, label="Actual Price", alpha=0.7)

    plt.plot(test_dates_leak, y_pred_leak, "--", label="Predicted (with leakage)")

    plt.plot(test_dates_proper, y_pred_proper, "--", label="Predicted (proper)")

    plt.title("Japan Natural Gas Price: Actual vs Predicted")

    plt.xlabel("Date")

    plt.ylabel("Price")

    plt.legend()

    plt.tight_layout()

    plt.show()

