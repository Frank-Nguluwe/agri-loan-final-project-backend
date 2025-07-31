import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
from app.encoders.frequency_encoder import FrequencyEncoder

# Load data
data = pd.read_excel("Data_cumo_trial1.xlsx")

# Columns
num_features = ['loan_farm_size', 'past_yield_kgs', 'past_yield_mk', 'expected_yield_kgs', 'expected_yield_mk']
cat_features = ['loan_crop']

# Preprocessors
preprocessor = ColumnTransformer(transformers=[
    ('num', StandardScaler(), num_features),
    ('freq', FrequencyEncoder('loan_crop'), ['loan_crop'])
])

# Pipeline
pipeline = Pipeline(steps=[
    ('preprocessing', preprocessor),
    ('model', GradientBoostingRegressor(n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42))
])

# Prepare data
X = data.drop(['loan_amount'], axis=1)
y = data['loan_amount']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Fit pipeline
pipeline.fit(X_train, y_train)

# Save the full pipeline
joblib.dump(pipeline, 'app/ml_model/loan_predictor1.pkl')
print("✅ Pipeline saved as 'app/ml_model/loan_predictor1.pkl'")
