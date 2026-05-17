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

def fetch_japan_natural_gas_price_data_3() -> None:
    warnings.filterwarnings("ignore")

    api_key = "8f058d10ec8c788296c040ea09e634d5"

    japan_gas = fetch_fred_data("PNGASJPUSDM", api_key)

    data = japan_gas.copy()

    data_with_lookahead = data.copy()

    data_with_lookahead["next_day_price"] = data_with_lookahead["value"].shift(-1)

    data_with_lookahead["future_5day_ma"] = (
        data_with_lookahead["value"].rolling(window=5, center=True).mean()
    )

    data_with_lookahead["future_volatility"] = (
        data_with_lookahead["value"].rolling(window=10, center=True).std()
    )

    data_proper = data.copy()

    data_proper["next_day_price"] = data_proper["value"].shift(-1)

    data_proper["past_5day_ma"] = data_proper["value"].rolling(window=5).mean()

    data_proper["past_volatility"] = data_proper["value"].rolling(window=10).std()

    test_dates_leak, y_test_leak, y_pred_leak = evaluate_model(
        data_with_lookahead, ["future_5day_ma", "future_volatility"]
    )

    test_dates_proper, y_test_proper, y_pred_proper = evaluate_model(
        data_proper, ["past_5day_ma", "past_volatility"]
    )

    mape_leak = mape(y_test_leak, y_pred_leak)

    mape_proper = mape(y_test_proper, y_pred_proper)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    ax1.plot(data["date"], data["value"], label="Original Price", alpha=0.5)

    ax1.plot(
        data_with_lookahead["date"],
        data_with_lookahead["future_5day_ma"],
        label="MA with Lookahead",
        linewidth=2,
    )

    ax1.plot(
        data_proper["date"],
        data_proper["past_5day_ma"],
        label="MA without Lookahead",
        linewidth=2,
    )

    ax1.set_title("Moving Averages Comparison")

    ax1.legend(loc="upper left")

    ax1.grid(False)

    ax2.plot(
        data_with_lookahead["date"],
        data_with_lookahead["future_volatility"],
        label="Volatility with Lookahead",
        linewidth=2,
    )

    ax2.plot(
        data_proper["date"],
        data_proper["past_volatility"],
        label="Volatility without Lookahead",
        linewidth=2,
    )

    ax2.set_title("Volatility Comparison")

    ax2.legend(loc="upper left")

    ax2.grid(False)

    plt.tight_layout()

    plt.savefig("japan_gas_features.png", dpi=300, bbox_inches="tight")

    plt.show()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    ax1.scatter(y_test_leak, y_pred_leak, alpha=0.5)

    ax1.plot(
        [y_test_leak.min(), y_test_leak.max()],
        [y_test_leak.min(), y_test_leak.max()],
        "r--",
        label="Perfect Prediction",
    )

    ax1.set_title(f"With Lookahead Bias\nMAPE: {mape_leak:.2f}%")

    ax1.set_xlabel("Actual Price")

    ax1.set_ylabel("Predicted Price")

    ax1.legend(loc="upper left")

    ax1.grid(False)

    ax2.scatter(y_test_proper, y_pred_proper, alpha=0.5)

    ax2.plot(
        [y_test_proper.min(), y_test_proper.max()],
        [y_test_proper.min(), y_test_proper.max()],
        "r--",
        label="Perfect Prediction",
    )

    ax2.set_title(f"Without Lookahead Bias\nMAPE: {mape_proper:.2f}%")

    ax2.set_xlabel("Actual Price")

    ax2.set_ylabel("Predicted Price")

    ax2.legend(loc="upper left")

    ax2.grid(False)

    plt.tight_layout()

    plt.savefig("japan_gas_predictions.png", dpi=300, bbox_inches="tight")

    plt.show()

    plt.figure(figsize=(12, 6))

    plt.plot(test_dates_leak, y_test_leak, label="Actual Price", alpha=0.7)

    plt.plot(
        test_dates_leak,
        y_pred_leak,
        "--",
        label=f"With Lookahead (MAPE: {mape_leak:.2f}%)",
    )

    plt.plot(
        test_dates_proper,
        y_pred_proper,
        "--",
        label=f"Without Lookahead (MAPE: {mape_proper:.2f}%)",
    )

    plt.title("Japan Natural Gas Price: Actual vs Predicted")

    plt.xlabel("Date")

    plt.ylabel("Price")

    plt.legend(loc="upper left")

    plt.grid(False)

    plt.tight_layout()

    plt.savefig("japan_gas_time_series.png", dpi=300, bbox_inches="tight")

    plt.show()

    print("\nPerformance Metrics:")

    print("-" * 50)

    print(f"MAPE with lookahead bias: {mape_leak:.2f}%")

    print(f"MAPE without lookahead bias: {mape_proper:.2f}%")

    print(f"Difference in MAPE: {mape_proper - mape_leak:.2f}%")

