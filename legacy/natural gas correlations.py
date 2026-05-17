"""Generated from Jupyter notebook: natural gas correlations

Magics and shell lines are commented out. Run with a normal Python interpreter."""

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


def analyze_correlations(df, split_date="2020-01-01"):
    before_2020 = df[df.index < split_date].corr()
    after_2020 = df[df.index >= split_date].corr()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    sns.heatmap(before_2020, annot=True, cmap="coolwarm", ax=ax1)
    ax1.set_title("Correlations Before 2020")
    sns.heatmap(after_2020, annot=True, cmap="coolwarm", ax=ax2)
    ax2.set_title("Correlations After 2020")
    plt.tight_layout()
    plt.show()
    return (before_2020, after_2020)


def calculate_garch_volatility(returns):
    """Calculate volatility using GARCH(1,1) model"""
    model = arch_model(returns, vol="Garch", p=1, q=1)
    results = model.fit(disp="off")
    return np.sqrt(results.conditional_volatility)


def create_animation(combined_df):
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.set_xlim(combined_df.index.min(), combined_df.index.max())
    ax.set_ylim(0, combined_df.max().max() * 1.1)
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    lines = {}
    for i, region in enumerate(combined_df.columns):
        (line,) = ax.plot([], [], label=region, color=colors[i], linewidth=2)
        lines[region] = line
    ax.set_title("Natural Gas Prices Over Time", fontsize=12, pad=20)
    ax.set_xlabel("Date", fontsize=10)
    ax.set_ylabel("Price (USD)", fontsize=10)
    ax.grid(True, alpha=0.3)
    leg = ax.legend(loc="upper left", frameon=True, framealpha=0.9)
    leg.set_zorder(100)

    def animate(frame):
        for region in combined_df.columns:
            lines[region].set_data(
                combined_df.index[:frame], combined_df[region].iloc[:frame]
            )
        return lines.values()

    anim = animation.FuncAnimation(
        fig, animate, frames=len(combined_df), interval=50, blit=True, repeat=False
    )
    plt.tight_layout()
    anim.save("gas_prices.gif", writer="pillow", dpi=150)
    plt.close()


def create_features(df, leakage=False):
    """Create features with or without data leakage"""
    df = df.copy()
    if leakage:
        df["rolling_mean"] = df["value"].rolling(window=7, center=True).mean()
        df["volatility"] = df["value"].rolling(window=10, center=True).std()
    else:
        df["rolling_mean"] = df["value"].rolling(window=7).mean().shift(1)
        df["volatility"] = df["value"].rolling(window=10).std().shift(1)
    df["price_lag"] = df["value"].shift(1)
    df["monthly_return"] = df["value"].pct_change(periods=30)
    return df


def create_features_proper(df):
    df["next_day_price"] = df["value"].shift(-1)
    df["past_5day_ma"] = df["value"].rolling(window=5).mean()
    df["past_volatility"] = df["value"].rolling(window=10).std()
    return df


def create_features_with_lookahead(df):
    df["next_day_price"] = df["value"].shift(-1)
    df["future_5day_ma"] = df["value"].rolling(window=5, center=True).mean()
    df["future_volatility"] = df["value"].rolling(window=10, center=True).std()
    return df


def create_volatility_animation(volatility_df):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    rolling_cols = [col for col in volatility_df.columns if "Rolling" in col]
    rolling_min = volatility_df[rolling_cols].min().min()
    rolling_max = volatility_df[rolling_cols].max().max()
    garch_cols = [col for col in volatility_df.columns if "GARCH" in col]
    garch_min = volatility_df[garch_cols].min().min()
    garch_max = volatility_df[garch_cols].max().max()
    ax1.set_xlim(volatility_df.index.min(), volatility_df.index.max())
    ax2.set_xlim(volatility_df.index.min(), volatility_df.index.max())
    ax1.set_ylim(rolling_min * 0.9, rolling_max * 1.1)
    ax2.set_ylim(garch_min * 0.9, garch_max * 1.1)
    for ax in [ax1, ax2]:
        ax.grid(True, alpha=0.3)
    rolling_lines = {}
    garch_lines = {}
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    for i, region in enumerate(["Japan", "Europe", "US"]):
        (roll_line,) = ax1.plot(
            [], [], label=f"{region} Rolling", color=colors[i], linewidth=2
        )
        rolling_lines[region] = roll_line
        (garch_line,) = ax2.plot(
            [], [], label=f"{region} GARCH", color=colors[i], linewidth=2
        )
        garch_lines[region] = garch_line
    ax1.set_title("Rolling Volatility (20-day window)", fontsize=12)
    ax2.set_title("GARCH(1,1) Volatility", fontsize=12)
    ax2.set_xlabel("Date", fontsize=10)
    for ax in [ax1, ax2]:
        ax.set_ylabel("Annualized Volatility", fontsize=10)
        leg = ax.legend(loc="upper left", frameon=True, framealpha=0.9)
        leg.set_zorder(100)

    def animate(frame):
        for region in ["Japan", "Europe", "US"]:
            rolling_lines[region].set_data(
                volatility_df.index[:frame],
                volatility_df[f"{region}_Rolling"].iloc[:frame],
            )
            garch_lines[region].set_data(
                volatility_df.index[:frame],
                volatility_df[f"{region}_GARCH"].iloc[:frame],
            )
        return list(rolling_lines.values()) + list(garch_lines.values())

    anim = animation.FuncAnimation(
        fig, animate, frames=len(volatility_df), interval=50, blit=True, repeat=False
    )
    plt.tight_layout()
    anim.save("gas_volatility.gif", writer="pillow", dpi=150)
    plt.close()
    print("\nScale Ranges:")
    print(f"Rolling Volatility: {rolling_min:.4f} to {rolling_max:.4f}")
    print(f"GARCH Volatility: {garch_min:.4f} to {garch_max:.4f}")


def demonstrate_leakage(data):
    data = data.dropna()
    train_size = int(len(data) * 0.8)
    train_data = data[:train_size]
    test_data = data[train_size:]
    X_train = train_data[["price_lag1", "rolling_mean_with_leakage", "monthly_return"]]
    y_train = train_data["price"]
    X_test = test_data[["price_lag1", "rolling_mean_with_leakage", "monthly_return"]]
    y_test = test_data["price"]
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    return (test_data.index, y_test, y_pred)


def demonstrate_proper_handling(data):
    data = data.dropna()
    train_size = int(len(data) * 0.8)
    train_data = data[:train_size]
    test_data = data[train_size:]
    X_train = train_data[["price_lag1", "proper_rolling_mean", "monthly_return"]]
    y_train = train_data["price"]
    X_test = test_data[["price_lag1", "proper_rolling_mean", "monthly_return"]]
    y_test = test_data["price"]
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    return (test_data.index, y_test, y_pred)


def evaluate_model(data, features):
    data = data.dropna()
    train_size = int(len(data) * 0.8)
    train_data = data[:train_size]
    test_data = data[train_size:]
    X_train = train_data[features]
    y_train = train_data["next_day_price"]
    X_test = test_data[features]
    y_test = test_data["next_day_price"]
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    return (test_data.index, y_test, y_pred)


def fetch_fred_data(series_id, api_key, start_date="2000-01-01"):
    """Fetch data from FRED API"""
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series_id,
        "api_key": api_key,
        "file_type": "json",
        "observation_start": start_date,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data["observations"])
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        return df


def granger_causality(data, max_lag=12):
    results = {}
    for col1 in data.columns:
        for col2 in data.columns:
            if col1 != col2:
                test_result = grangercausalitytests(
                    data[[col1, col2]], maxlag=max_lag, verbose=False
                )
                min_p_value = min(
                    [test_result[i + 1][0]["ssr_ftest"][1] for i in range(max_lag)]
                )
                results[f"{col1} -> {col2}"] = min_p_value
    return results




def mape(y_true, y_pred):
    """Calculate Mean Absolute Percentage Error"""
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100


def plot_correlations_and_scatter(data):
    corr = data.corr()
    fig = plt.figure(figsize=(15, 10))
    ax1 = plt.subplot2grid((2, 3), (0, 0), colspan=2)
    sns.heatmap(corr, annot=True, cmap="coolwarm", center=0, ax=ax1)
    ax1.set_title("Correlation Heatmap")
    ax2 = plt.subplot2grid((2, 3), (1, 0))
    ax2.scatter(data["Japan Gas"], data["EU Gas"])
    ax2.set_xlabel("Japan Gas")
    ax2.set_ylabel("EU Gas")
    ax2.set_title("Japan Gas vs EU Gas")
    ax3 = plt.subplot2grid((2, 3), (1, 1))
    ax3.scatter(data["Japan Gas"], data["US Loan Rate"])
    ax3.set_xlabel("Japan Gas")
    ax3.set_ylabel("US Loan Rate")
    ax3.set_title("Japan Gas vs US Loan Rate")
    ax4 = plt.subplot2grid((2, 3), (1, 2))
    ax4.scatter(data["EU Gas"], data["US Loan Rate"])
    ax4.set_xlabel("EU Gas")
    ax4.set_ylabel("US Loan Rate")
    ax4.set_title("EU Gas vs US Loan Rate")
    plt.tight_layout()
    plt.show()


def plot_features(data, leakage_data, proper_data, title, filename):
    """Plot feature comparison for leakage and proper handling"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    ax1.plot(data.index, data["value"], label="Original Price", alpha=0.5)
    ax1.plot(
        leakage_data.index,
        leakage_data["rolling_mean"],
        label="Rolling Mean (with leakage)",
        linewidth=2,
    )
    ax1.plot(
        proper_data.index,
        proper_data["rolling_mean"],
        label="Rolling Mean (proper)",
        linewidth=2,
    )
    ax1.set_title(f"{title} - Rolling Means")
    ax1.legend(loc="upper left")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Price")
    ax2.plot(
        leakage_data.index,
        leakage_data["volatility"],
        label="Volatility (with leakage)",
        linewidth=2,
    )
    ax2.plot(
        proper_data.index,
        proper_data["volatility"],
        label="Volatility (proper)",
        linewidth=2,
    )
    ax2.set_title(f"{title} - Volatility")
    ax2.legend(loc="upper left")
    ax2.set_xlabel("Date")
    ax2.set_ylabel("Volatility")
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.show()


def plot_predictions(leakage_results, proper_results, title, filename):
    """Plot prediction results"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    dates_leak, y_test_leak, y_pred_leak = leakage_results
    dates_proper, y_test_proper, y_pred_proper = proper_results
    mape_leak = mape(y_test_leak, y_pred_leak)
    mape_proper = mape(y_test_proper, y_pred_proper)
    ax1.plot(dates_leak, y_test_leak, label="Actual", alpha=0.7)
    ax1.plot(
        dates_leak, y_pred_leak, "--", label=f"With Leakage (MAPE: {mape_leak:.2f}%)"
    )
    ax1.plot(
        dates_proper, y_pred_proper, "--", label=f"Proper (MAPE: {mape_proper:.2f}%)"
    )
    ax1.set_title(f"{title} - Predictions Over Time")
    ax1.legend(loc="upper left")
    ax1.set_xlabel("Date")
    ax1.set_ylabel("Price")
    ax2.scatter(y_test_leak, y_pred_leak, alpha=0.5, label="With Leakage")
    ax2.scatter(y_test_proper, y_pred_proper, alpha=0.5, label="Proper")
    ax2.plot(
        [
            min(y_test_leak.min(), y_test_proper.min()),
            max(y_test_leak.max(), y_test_proper.max()),
        ],
        [
            min(y_test_leak.min(), y_test_proper.min()),
            max(y_test_leak.max(), y_test_proper.max()),
        ],
        "r--",
        label="Perfect Prediction",
    )
    ax2.set_title("Actual vs Predicted Prices")
    ax2.legend(loc="upper left")
    ax2.set_xlabel("Actual Price")
    ax2.set_ylabel("Predicted Price")
    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.show()


def plot_time_series(data):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))
    ax1.plot(data.index, data["Japan Gas"], label="Japan Gas")
    ax1.plot(data.index, data["EU Gas"], label="EU Gas")
    ax1.set_title("Natural Gas Prices Over Time")
    ax1.legend()
    ax1.grid(True)
    ax2.plot(data.index, data["US Loan Rate"], label="US Loan Rate", color="green")
    ax2.set_title("US Loan Rate Over Time")
    ax2.legend()
    ax2.grid(True)
    plt.tight_layout()
    plt.show()


def prepare_volatility_data(combined_df):
    """Calculate returns and volatility for each series"""
    volatility_df = pd.DataFrame(index=combined_df.index)
    for region in combined_df.columns:
        returns = np.log(combined_df[region]).diff()
        rolling_vol = returns.rolling(window=20).std() * np.sqrt(252)
        garch_vol = calculate_garch_volatility(returns.dropna())
        volatility_df[f"{region}_Rolling"] = rolling_vol
        volatility_df[f"{region}_GARCH"] = garch_vol
    return volatility_df


def train_model(data, features, target="value"):
    """Train and evaluate model"""
    data = data.dropna()
    train_size = int(len(data) * 0.8)
    train_data = data[:train_size]
    test_data = data[train_size:]
    X_train = train_data[features]
    y_train = train_data[target]
    X_test = test_data[features]
    y_test = test_data[target]
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    return (test_data.index, y_test, y_pred)










def notebook_step_006() -> None:
    create_volatility_animation(volatility_df)


def create_sample_time_series_data() -> None:
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

    data["rolling_mean"] = data["target"].rolling(window=7, center=True).mean()

    leakage_mse = demonstrate_leakage()

    proper_mse = demonstrate_proper_handling()

    print(f"MSE with data leakage: {leakage_mse:.2f}")

    print(f"MSE with proper handling: {proper_mse:.2f}")

    print(f"Difference in MSE: {proper_mse - leakage_mse:.2f}")


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


def create_synthetic_stock_data() -> None:
    np.random.seed(42)

    dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")

    stock_data = pd.DataFrame(
        {
            "date": dates,
            "price": 100 * (1 + np.random.normal(0, 0.02, len(dates)).cumsum()),
        }
    )

    data_with_lookahead = create_features_with_lookahead(stock_data.copy())

    data_proper = create_features_proper(stock_data.copy())

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    mse_lookahead = evaluate_model(
        data_with_lookahead,
        ["future_5day_ma", "future_volatility"],
        "Model with Lookahead Bias",
        ax1,
    )

    mse_proper = evaluate_model(
        data_proper,
        ["past_5day_ma", "past_volatility"],
        "Model without Lookahead Bias",
        ax2,
    )

    plt.tight_layout()

    plt.show()

    print(f"MSE with lookahead bias: {mse_lookahead:.6f}")

    print(f"MSE without lookahead bias: {mse_proper:.6f}")

    print(
        f"Performance difference (proper - lookahead): {mse_proper - mse_lookahead:.6f}"
    )

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

    ax1.plot(stock_data["date"], stock_data["price"], label="Price", alpha=0.5)

    ax1.plot(
        data_with_lookahead["date"],
        data_with_lookahead["future_5day_ma"],
        label="5-day MA (with lookahead)",
        linewidth=2,
    )

    ax1.plot(
        data_proper["date"],
        data_proper["past_5day_ma"],
        label="5-day MA (proper)",
        linewidth=2,
    )

    ax1.set_title("Price and Moving Averages")

    ax1.legend()

    ax2.plot(
        data_with_lookahead["date"],
        data_with_lookahead["future_volatility"],
        label="Volatility (with lookahead)",
        linewidth=2,
    )

    ax2.plot(
        data_proper["date"],
        data_proper["past_volatility"],
        label="Volatility (proper)",
        linewidth=2,
    )

    ax2.set_title("Volatility Measures")

    ax2.legend()

    plt.tight_layout()

    plt.show()








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


def fetch_japan_natural_gas_price_data_2() -> None:
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

    ax1.legend(loc="upper left")

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

    ax2.legend(loc="upper left")

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

    ax3.legend(loc="upper left")

    plt.tight_layout()

    plt.savefig("japan_gas_analysis_combined.png", dpi=300, bbox_inches="tight")

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

    plt.legend(loc="upper left")

    plt.tight_layout()

    plt.savefig("japan_gas_predictions_comparison.png", dpi=300, bbox_inches="tight")

    plt.show()

    plt.figure(figsize=(12, 6))

    plt.plot(data.index, data["price"], label="Japan Gas Price", alpha=0.5)

    plt.plot(
        data.index,
        data["rolling_mean_with_leakage"],
        label="Rolling Mean (with leakage)",
        linewidth=2,
    )

    plt.plot(
        data.index,
        data["proper_rolling_mean"],
        label="Proper Rolling Mean (shifted)",
        linewidth=2,
    )

    plt.title("Japan Natural Gas Prices with Different Rolling Means")

    plt.xlabel("Date")

    plt.ylabel("Price")

    plt.legend(loc="upper left")

    plt.tight_layout()

    plt.savefig("japan_gas_rolling_means.png", dpi=300, bbox_inches="tight")

    plt.show()

    plt.figure(figsize=(12, 6))

    plt.scatter(y_test_leak, y_pred_leak, alpha=0.5)

    plt.plot(
        [y_test_leak.min(), y_test_leak.max()],
        [y_test_leak.min(), y_test_leak.max()],
        "r--",
        label="Perfect Prediction",
    )

    plt.title(f"Predictions with Data Leakage\nMAPE: {mape_leak:.2f}%")

    plt.xlabel("Actual Price")

    plt.ylabel("Predicted Price")

    plt.legend(loc="upper left")

    plt.tight_layout()

    plt.savefig("japan_gas_leakage_predictions.png", dpi=300, bbox_inches="tight")

    plt.show()

    plt.figure(figsize=(12, 6))

    plt.scatter(y_test_proper, y_pred_proper, alpha=0.5)

    plt.plot(
        [y_test_proper.min(), y_test_proper.max()],
        [y_test_proper.min(), y_test_proper.max()],
        "r--",
        label="Perfect Prediction",
    )

    plt.title(f"Predictions with Proper Time Series Handling\nMAPE: {mape_proper:.2f}%")

    plt.xlabel("Actual Price")

    plt.ylabel("Predicted Price")

    plt.legend(loc="upper left")

    plt.tight_layout()

    plt.savefig("japan_gas_proper_predictions.png", dpi=300, bbox_inches="tight")

    plt.show()


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


def main() -> None:
    notebook_step_006()
    create_sample_time_series_data()
    create_sample_time_series_data_2()
    create_synthetic_stock_data()
    fetch_japan_natural_gas_price_data()
    fetch_japan_natural_gas_price_data_2()
    fetch_japan_natural_gas_price_data_3()


if __name__ == "__main__":
    main()
