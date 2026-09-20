import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
import pandas as pd

SHIPMENT_NUMERICAL_FEATURES = [
    "total_weight_kg",
    "total_volume_m3",
    "distance_km",
]

SHIPMENT_CATEGORICAL_FEATURES = [
    "transport_mode",
    "service_level",
    "carrier_id"
]

SHIPMENT_TARGET = "freight_cost_sek"

def train_transport_cost_model(rows):
    df = pd.DataFrame(rows)

    # Remove rows with missing information
    required_columns = (SHIPMENT_NUMERICAL_FEATURES + SHIPMENT_CATEGORICAL_FEATURES + [SHIPMENT_TARGET])

    df = df.dropna(subset=required_columns)

    # Convert numerical columns
    for col in SHIPMENT_NUMERICAL_FEATURES + [SHIPMENT_TARGET]:
        df[col] = pd.to_numeric(df[col])

    # Convert UUIDs, enums and text values before encoding
    for col in SHIPMENT_CATEGORICAL_FEATURES:
        df[col] = df[col].astype(str)

    X = df[SHIPMENT_NUMERICAL_FEATURES + SHIPMENT_CATEGORICAL_FEATURES]
    y = df[SHIPMENT_TARGET]

    # Separate training and test data

    X_train, X_test, Y_train, Y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # One-hot encoding of categorical variables
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(
                    drop="first",
                    handle_unknown="ignore",     
                ),
                SHIPMENT_CATEGORICAL_FEATURES,
            ),
            (
                "numerical",
                "passthrough",
                SHIPMENT_NUMERICAL_FEATURES,
            )          
        ]
    )

    # ML pipeline
    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regression", LinearRegression())
        ]
    )

    # Train model
    model.fit(X_train, Y_train)

    # Predict costs for test shipments
    y_pred = np.asarray(model.predict(X_test), dtype=float)

    # Evaluate model
    mae = mean_absolute_error(Y_test, y_pred)
    mse = mean_squared_error(Y_test, y_pred)
    r2 = r2_score(Y_test, y_pred)
    rmse = np.sqrt(mse)

    wape = (
        np.sum(np.abs(Y_test - y_pred)) / np.sum(np.abs(Y_test))
    )

    # Checking individual aspects of the model

    results_df = X_test.copy()
    results_df["actual"] = Y_test
    results_df["predicted"] = y_pred
    results_df["absolute_error"] = np.abs(results_df["actual"] - results_df["predicted"])

    air_results = results_df[
        results_df["transport_mode"] == "AIR"
    ]

    air_mae = air_results["absolute_error"].mean()

    

    return {
        "model": model,
        "metrics": {
            "rows_used": len(df),
            "mae": mae,
            "mse": mse,
            "r2": r2,
            "rmse" : rmse,
            "wape": float(wape),
            "actual": Y_test.tolist()[:20],
            "predicted": y_pred.tolist()[:20],
        }
    }


def random_test_model():
    np.random.seed(42)
    """Method for generating random data to test the model on"""
    X = np.random.rand(50, 1) * 100
    Y = X + 3.5 * np.random.randn(50, 1) * 20

    model = LinearRegression()
    model.fit(X, Y)

    Y_pred = model.predict(X)

    plt.figure(figsize=(8,6))
    plt.scatter(X, Y, color="blue", label="Data Points")
    plt.plot(X, Y_pred, color="red", linewidth=2, label="Regression Line")
    plt.title("Linear regression on random dataset")
    plt.xlabel('X')
    plt.ylabel('Y')
    plt.legend()
    plt.grid(True)
    plt.show()

    slope = np.asarray(model.coef_).reshape(-1)[0]
    intercept = np.asarray(model.intercept_).item()

    print(f"Slope Coefficient: {slope}")
    print(f"Intercept: {intercept}")
