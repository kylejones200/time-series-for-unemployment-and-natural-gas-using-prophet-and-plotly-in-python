"""Auto-split from legacy monolithic script."""

import warnings

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from arch import arch_model
from sklearn.linear_model import LinearRegression
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


def fetch_fred_data(series_id, start_date="2000-01-01", end_date=None):
    """Fetch data from FRED via pandas_datareader."""
    from datetime import datetime

    import pandas_datareader.data as web

    if end_date is None:
        end_date = datetime.now()
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    raw = web.DataReader(series_id, "fred", start, end)
    df = raw.reset_index()
    date_col = "DATE" if "DATE" in df.columns else df.columns[0]
    value_col = series_id if series_id in df.columns else df.columns[-1]
    out = df.rename(columns={date_col: "date", value_col: "value"})
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.dropna(subset=["value"])


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
    plt.figure(figsize=(15, 10))
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


def main() -> None:
    notebook_step_006()
    create_sample_time_series_data()
    create_sample_time_series_data_2()
    create_synthetic_stock_data()
    fetch_japan_natural_gas_price_data()
    fetch_japan_natural_gas_price_data_2()
    fetch_japan_natural_gas_price_data_3()
