"""Auto-split from legacy monolithic script."""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


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
