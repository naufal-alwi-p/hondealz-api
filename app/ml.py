import tensorflow as tf
import numpy as np
import joblib
from typing import Dict, Union
import pandas as pd
from datetime import datetime, timezone
from sklearn.base import BaseEstimator, TransformerMixin

class MotorImagePredictor:
    def __init__(self, model_path):
        self.model = tf.keras.models.load_model(model_path)

        self.class_names = [
            'All New Honda Vario 125 & 150',
            'All New Honda Vario 125 & 150 Keyless',
            'Vario 110',
            'Vario 110 ESP',
            'Vario 160',
            'Vario Techno 110',
            'Vario Techno 125 FI'
        ]
        self.img_size = (224, 224)

    def preprocess_image(self, img):
        img = img.resize(self.img_size)
        img_array = tf.keras.preprocessing.image.img_to_array(img)
        img_array = tf.expand_dims(img_array, 0)
        img_array = tf.keras.applications.efficientnet.preprocess_input(img_array)
        return img_array

    def predict_image(self, img):  # Changed method name from predict to predict_image
        processed_image = self.preprocess_image(img)

        # Get raw predictions
        raw_predictions = self.model.predict(processed_image, verbose=1)

        # Get top 3 predictions
        top_3_idx = np.argsort(raw_predictions[0])[-3:][::-1]
        top_3_predictions = [
            (self.class_names[idx], float(raw_predictions[0][idx]) * 100)
            for idx in top_3_idx
        ]

        return top_3_predictions

class MotorPricePredictorWithRange(BaseEstimator, TransformerMixin):
    def __init__(self, model_path: str = 'optimized_price_model.joblib'):
        """Initialize preprocessor with model artifacts."""
        self.current_year = datetime.now(timezone.utc).year
        try:
            model_artifacts = joblib.load(model_path)
            self.models = model_artifacts['models']
            self.weights = model_artifacts['weights']
            self.feature_columns = model_artifacts['feature_columns']
            self.numerical_features = model_artifacts['numerical_features']
            self.categorical_features = model_artifacts['categorical_features']
            self.scaler = model_artifacts['scaler']
        except Exception as e:
            raise Exception(f"Error loading model artifacts: {str(e)}")

        # Required input features
        self.required_features = ['model', 'year', 'mileage', 'location', 'tax']
        
        # Model mapping
        self.model_mapping = {
            'All New Honda Vario 125 & 150': 'VARIO 125',
            'All New Honda Vario 125 & 150 Keyless': 'VARIO 125', 
            'Vario 110': 'VARIO 110',
            'Vario 110 ESP': 'VARIO 110 ESP',
            'Vario 160': 'VARIO 160',
            'Vario Techno 110': 'VARIO TECHNO 110',
            'Vario Techno 125 FI': 'VARIO 125'
        }
        
        # Province mapping
        self.province_mapping = {
            'Jakarta': ['Jakarta', 'Jakarta Timur', 'Jakarta Barat', 'Jakarta Selatan', 
                       'Jakarta Utara', 'Jakarta Pusat'],
            'Jawa Barat': ['Bandung', 'Depok', 'Bekasi', 'Bogor', 'Cimahi', 'Cianjur', 
                          'Ciamis', 'Garut', 'Sukabumi', 'Karawang'],
            'Banten': ['Tangerang', 'Tangerang Selatan', 'Serang', 'Cilegon'],
            'Jawa Tengah': ['Semarang', 'Magelang', 'Klaten', 'Pemalang'],
            'Yogyakarta': ['Yogyakarta', 'Sleman', 'Bantul'],
            'Jawa Timur': ['Surabaya', 'Malang', 'Sidoarjo', 'Gresik', 'Kediri'],
            'Bali': ['Denpasar', 'Badung', 'Buleleng']
        }

    def _clean_mileage(self, mileage: Union[str, float, int]) -> float:
        """Clean and standardize mileage format."""
        if isinstance(mileage, (int, float)):
            return float(mileage)
            
        try:
            mileage = str(mileage).lower()
            if '-' in mileage:
                start, end = mileage.split('-')
                start = float(start.replace('km', '').replace(',', '').replace('.', '').strip())
                end = float(end.replace('km', '').replace(',', '').replace('.', '').strip())
                return (start + end) / 2
            return float(mileage.replace('km', '').replace(',', '').replace('.', '').strip())
        except:
            raise ValueError(f"Invalid mileage format: {mileage}")

    def _extract_engine_size(self, model: str) -> int:
        """Extract engine size from model name."""
        model = str(model).upper()
        if '160' in model:
            return 160
        elif '150' in model:
            return 150
        elif '125' in model:
            return 125
        return 110

    def _map_location_to_province(self, location: str) -> str:
        """Map location to province."""
        location = str(location).lower()
        for province, cities in self.province_mapping.items():
            if any(city.lower() in location for city in cities):
                return province
        return 'Others'

    def _validate_input(self, df: pd.DataFrame) -> None:
        """Validate input data."""
        missing_features = [f for f in self.required_features if f not in df.columns]
        if missing_features:
            raise ValueError(f"Missing required features: {missing_features}")
            
        if df['year'].max() > self.current_year:
            raise ValueError(f"Year cannot be greater than {self.current_year}")
            
        if df['mileage'].min() < 0:
            raise ValueError("Mileage cannot be negative")

    def transform(self, data: Dict[str, Union[str, float, int]]) -> pd.DataFrame:
        """Transform input data untuk prediksi."""
        # Convert to DataFrame if needed
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = pd.DataFrame(data)

        # Validate input
        self._validate_input(df)
        
        # Basic cleaning
        df['mileage'] = df['mileage'].apply(self._clean_mileage)
        
        # Create basic features
        df['age'] = self.current_year - df['year']
        df['engine_size'] = df['model'].apply(self._extract_engine_size)
        df['province'] = df['location'].apply(self._map_location_to_province)
        
        # Create age categories with handling for single value
        try:
            df['age_category'] = pd.qcut(df['age'], 4,
                                       labels=['new', 'medium_new', 'medium_old', 'old'])
        except ValueError:
            # If all values are the same, assign 'new' for low values
            if df['age'].iloc[0] <= 2:
                df['age_category'] = 'new'
            else:
                df['age_category'] = 'old'
        
        # Create numerical features
        df['age_squared'] = df['age'] ** 2
        df['mileage_squared'] = df['mileage'] ** 2
        df['price_per_cc'] = df['engine_size']
        df['mileage_per_age'] = df['mileage'] / (df['age'] + 1)
        df['engine_age_interaction'] = df['engine_size'] * np.exp(-df['age']/3)
        df['normalized_mileage'] = df['mileage'] / (df['age'] + 1)
        df['depreciation_factor'] = np.exp(-df['age']/5)
        
        # Create mileage segments with handling for single value
        try:
            df['mileage_segment'] = pd.cut(df['mileage'],
                                         bins=[0, 5000, 10000, 20000, 30000, float('inf')],
                                         labels=['very_low', 'low', 'medium', 'high', 'very_high'])
        except ValueError:
            # Assign segment based on value
            mileage = df['mileage'].iloc[0]
            if mileage <= 5000:
                df['mileage_segment'] = 'very_low'
            elif mileage <= 10000:
                df['mileage_segment'] = 'low'
            elif mileage <= 20000:
                df['mileage_segment'] = 'medium'
            elif mileage <= 30000:
                df['mileage_segment'] = 'high'
            else:
                df['mileage_segment'] = 'very_high'
                
        # Price segment for single prediction always set to medium
        df['price_segment'] = 'medium'
        
        # Market features
        df['is_abs'] = df['model'].str.contains('ABS', case=False, na=False).astype(int)
        df['is_cbs'] = df['model'].str.contains('CBS|ISS', case=False, na=False).astype(int)
        df['is_premium'] = ((df['engine_size'] >= 150) |
                          (df['model'].str.contains('ABS|CBS', case=False, na=False))).astype(int)
        
        # Create dummies
        categorical_columns = ['province', 'age_category', 'price_segment', 'mileage_segment']
        df_encoded = pd.get_dummies(df, columns=categorical_columns)
        
        # Ensure all training features exist
        for col in self.feature_columns:
            if col not in df_encoded.columns:
                df_encoded[col] = 0
        
        # Select and order columns
        X = df_encoded[self.feature_columns]
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=self.feature_columns)
        
        return X_scaled

    def predict(self, data: Dict[str, Union[str, float, int]]) -> Dict[str, Union[float, str]]:
        """Make price prediction."""
        try:
            # Transform features
            X = self.transform(data)
            
            # Make predictions with each model
            predictions = {}
            for name, model in self.models.items():
                pred = model.predict(X)[0]
                predictions[name] = pred
            
            # Calculate ensemble prediction
            final_prediction = sum(self.weights[name] * predictions[name] 
                                 for name in self.models.keys())
            
            # Calculate prediction range
            confidence_interval = 0.1  # 10% margin
            price_range = {
                'lower': round(final_prediction * (1 - confidence_interval)),
                'upper': round(final_prediction * (1 + confidence_interval))
            }
            
            return {
                'status': 'success',
                'predictions': {
                    'rf': predictions['rf'],
                    'xgb': predictions['xgb'],
                    'gbm': predictions['gbm'],
                    'final': round(final_prediction),
                    'price_range': price_range
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }

    def batch_predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """Make predictions for multiple entries."""
        results = []
        for _, row in df.iterrows():
            prediction = self.predict(row.to_dict())
            if prediction['status'] == 'success':
                results.append({
                    'input': row.to_dict(),
                    'predicted_price': prediction['predictions']['final'],
                    'price_range_low': prediction['predictions']['price_range']['lower'],
                    'price_range_high': prediction['predictions']['price_range']['upper']
                })
            else:
                results.append({
                    'input': row.to_dict(),
                    'error': prediction['message']
                })
        
        return pd.DataFrame(results)
