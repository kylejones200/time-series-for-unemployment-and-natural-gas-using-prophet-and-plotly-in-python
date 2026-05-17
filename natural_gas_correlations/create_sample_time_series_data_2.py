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

def create_sample_time_series_data_2() -> None:
    warnings.filterwarnings("ignore")

    np.random.seed(42)

    dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")

    data = pd.DataFrame(
        {
            "date": dates,
            "target": np.random.normal(100, 10, len(dates)),
            "feature1": np.random.normal(50, 5, len(dates)),
        }
    )

    data["rolling_mean_with_leakage"] = (
        data["target"].rolling(window=7, center=True).mean()
    )

    data["proper_rolling_mean"] = (
        data["target"].rolling(window=7, min_periods=1).mean().shift(1)
    )

    X_test_leak, y_test_leak, y_pred_leak = demonstrate_leakage()

    X_test_proper, y_test_proper, y_pred_proper = demonstrate_proper_handling()

    mse_leak = mean_squared_error(y_test_leak, y_pred_leak)

    mse_proper = mean_squared_error(y_test_proper, y_pred_proper)

    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 15))

    ax1.plot(data.index, data["target"], label="Target", alpha=0.5)

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

    ax1.set_title("Time Series Data with Different Rolling Means")

    ax1.legend()

    ax1.set_xlabel("Date")

    ax1.set_ylabel("Value")

    ax2.scatter(y_test_leak, y_pred_leak, alpha=0.5)

    ax2.plot(
        [y_test_leak.min(), y_test_leak.max()],
        [y_test_leak.min(), y_test_leak.max()],
        "r--",
        label="Perfect Prediction",
    )

    ax2.set_title(f"Predictions with Data Leakage\nMSE: {mse_leak:.2f}")

    ax2.set_xlabel("Actual Values")

    ax2.set_ylabel("Predicted Values")

    ax2.legend()

    ax3.scatter(y_test_proper, y_pred_proper, alpha=0.5)

    ax3.plot(
        [y_test_proper.min(), y_test_proper.max()],
        [y_test_proper.min(), y_test_proper.max()],
        "r--",
        label="Perfect Prediction",
    )

    ax3.set_title(
        f"Predictions with Proper Time Series Handling\nMSE: {mse_proper:.2f}"
    )

    ax3.set_xlabel("Actual Values")

    ax3.set_ylabel("Predicted Values")

    ax3.legend()

    plt.tight_layout()

    plt.savefig("time_series_analysis.png")

    plt.show()

    print(f"MSE with data leakage: {mse_leak:.2f}")

    print(f"MSE with proper handling: {mse_proper:.2f}")

    print(f"Difference in MSE: {mse_proper - mse_leak:.2f}")

