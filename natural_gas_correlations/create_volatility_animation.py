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

