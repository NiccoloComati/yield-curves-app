from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from config import MATURITY_MAPPING


def plot_yield_curves(df: pd.DataFrame) -> go.Figure:
    df = df.copy()
    for col in MATURITY_MAPPING.keys():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = pd.NA

    fig = go.Figure()
    for curve_date, group in df.groupby("Date"):
        if group.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=list(MATURITY_MAPPING.values()),
                y=group[list(MATURITY_MAPPING.keys())].values[0],
                mode="lines+markers",
                name=curve_date.strftime("%Y-%m-%d"),
                hovertemplate="Maturity: %{text}<br>Yield: %{y:.2f}%<extra></extra>",
                text=list(MATURITY_MAPPING.keys()),
            )
        )

    steps = []
    for i, trace in enumerate(fig.data):
        step = dict(method="update", args=[{"visible": [False] * len(fig.data)}], label=trace.name)
        step["args"][0]["visible"][i] = True
        steps.append(step)

    sliders = [
        dict(
            active=0,
            currentvalue={"prefix": "Date: "},
            pad={"t": 50},
            steps=steps,
        )
    ]

    max_yield = df[list(MATURITY_MAPPING.keys())].max().max()
    max_yield = max_yield if pd.notna(max_yield) else 1.0

    fig.update_layout(
        title="Evolution of the U.S. Treasury Yield Curve",
        xaxis=dict(
            title="Adjusted Maturities",
            tickmode="array",
            tickvals=list(MATURITY_MAPPING.values()),
            ticktext=list(MATURITY_MAPPING.keys()),
            showgrid=True,
        ),
        yaxis=dict(
            title="Yield (%)",
            range=[0, max_yield * 1.1],
            showgrid=True,
        ),
        sliders=sliders if fig.data else [],
        template="plotly_white",
        hovermode="x unified",
        height=600,
    )
    return fig
