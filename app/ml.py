import tensorflow as tf
import numpy as np
import joblib
from typing import Dict, Union
import pandas as pd
from datetime import datetime, timezone

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

class MotorPricePredictorWithRange:
    def __init__(self, model_path: str = 'optimized_price_model.joblib'):
        self.model_artifacts = joblib.load(model_path)

    def map_model_to_training(self, selected_model):
        mapping = {
            'All New Honda Vario 125 & 150 (2015-2018)':
                {'model': 'VARIO 125', 'year_range': [2015, 2018]},
            'All New Honda Vario 125 & 150 Keyless (2018-2022)':
                {'model': 'VARIO 125', 'year_range': [2018, 2022]},
            'Vario 110': {'model': 'VARIO 110', 'year_range': None},
            'Vario 110 ESP': {'model': 'VARIO 110 ESP', 'year_range': None},
            'Vario 160': {'model': 'VARIO 160', 'year_range': None},
            'Vario Techno 110': {'model': 'VARIO TECHNO 110', 'year_range': None},
            'Vario Techno 125 FI': {'model': 'VARIO 125', 'year_range': None}
        }
        return mapping.get(selected_model)

    def predict(self, data):
        """
        Test the price prediction model with given parameters

        Args:
            model_path (str): Path to the saved model
            test_data (dict): Dictionary containing test parameters
        """
        try:
            # Create DataFrame from test data
            df = pd.DataFrame([data])

            # Feature engineering
            current_year = datetime.now(timezone.utc).year
            df['age'] = current_year - df['year']
            df['age_squared'] = df['age'] ** 2
            df['mileage_squared'] = df['mileage'] ** 2
            df['price_per_cc'] = 0  # Placeholder
            df['mileage_per_age'] = df['mileage'] / (df['age'] + 1)
            df['normalized_mileage'] = df['mileage'] / (df['age'] + 1)
            df['engine_age_interaction'] = df['engine_size'] * np.exp(-df['age']/3)
            df['depreciation_factor'] = np.exp(-df['age']/5)

            # Categorical features
            df['age_category'] = pd.cut(df['age'],
                                    bins=[-np.inf, 2, 4, 6, np.inf],
                                    labels=['new', 'medium_new', 'medium_old', 'old'])

            df['mileage_segment'] = pd.cut(df['mileage'],
                                        bins=[0, 5000, 10000, 20000, 30000, float('inf')],
                                        labels=['very_low', 'low', 'medium', 'high', 'very_high'])

            # Price segments
            df['price_segment'] = 'medium'  # Default value
            price_segment_dummies = pd.get_dummies(df['price_segment'], prefix='price_segment')

            # Model features
            df['is_abs'] = df['model'].str.contains('ABS', case=False).astype(int)
            df['is_cbs'] = df['model'].str.contains('CBS|ISS', case=False).astype(int)
            df['is_premium'] = ((df['engine_size'] >= 150) |
                            df['model'].str.contains('ABS|CBS', case=False)).astype(int)

            # Condition score
            df['condition_score'] = (100 - (df['age'] * 5 + df['mileage']/1000)) / 100
            df['condition_score'] = df['condition_score'].clip(0, 1)

            # Location price ratio
            df['location_price_ratio'] = 1.0

            # Create all necessary dummies
            age_dummies = pd.get_dummies(df['age_category'], prefix='age_category')
            mileage_dummies = pd.get_dummies(df['mileage_segment'], prefix='mileage_segment')
            province_dummies = pd.get_dummies(df['province'], prefix='province')

            # Ensure all price segment categories exist
            for segment in ['very_low', 'low', 'medium', 'high', 'very_high']:
                col_name = f'price_segment_{segment}'
                if col_name not in price_segment_dummies.columns:
                    price_segment_dummies[col_name] = 0

            # Numerical features
            numerical_features = [
                'engine_size', 'year', 'mileage', 'age', 'mileage_per_age',
                'engine_age_interaction', 'location_price_ratio', 'condition_score',
                'is_abs', 'is_cbs', 'is_premium', 'age_squared', 'mileage_squared',
                'price_per_cc', 'normalized_mileage', 'depreciation_factor'
            ]

            # Combine features and ensure they match the training data
            feature_cols = self.model_artifacts['feature_columns']
            final_features = pd.DataFrame(index=df.index)

            # Add numerical features
            for col in numerical_features:
                if col in feature_cols:
                    final_features[col] = df[col]

            # Add dummy variables
            all_dummies = pd.concat([
                price_segment_dummies,
                age_dummies,
                mileage_dummies,
                province_dummies
            ], axis=1)

            # Ensure all required columns are present
            for col in feature_cols:
                if col not in final_features.columns:
                    if col in all_dummies.columns:
                        final_features[col] = all_dummies[col]
                    else:
                        final_features[col] = 0

            # Reorder columns to match training data
            final_features = final_features[feature_cols]

            # Make predictions
            rf_pred = self.model_artifacts['models']['rf'].predict(final_features)
            xgb_pred = self.model_artifacts['models']['xgb'].predict(final_features)
            gbm_pred = self.model_artifacts['models']['gbm'].predict(final_features)

            # Calculate ensemble prediction
            weights = self.model_artifacts['weights']
            base_prediction = (
                weights['rf'] * rf_pred[0] +
                weights['xgb'] * xgb_pred[0] +
                weights['gbm'] * gbm_pred[0]
            )

            return {
                "status": "success",
                "predicted_price": base_prediction
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error during prediction: {str(e)}"
            }

    def predict_with_range(self, data: Dict[str, Union[str, int, float]],
                          confidence_interval: float = 0.1) -> Dict[str, Union[float, str]]:
        try:
            mapped_model = self.map_model_to_training(data['model'])
            if mapped_model is None:
                return {
                    'status': 'error',
                    'message': 'Invalid model selected'
                }

            data['model'] = mapped_model['model']

            if mapped_model['year_range'] is not None:
                if not (mapped_model['year_range'][0] <= data['year'] <= mapped_model['year_range'][1]):
                    return {
                        'status': 'error',
                        'message': f"Year must be between {mapped_model['year_range'][0]} and {mapped_model['year_range'][1]} for this model"
                    }

            result = self.predict(data)

            if result['status'] == 'success':
                base_price = result['predicted_price']
                price_range = base_price * confidence_interval
                lower_bound = round(base_price - price_range)
                upper_bound = round(base_price + price_range)

                return {
                    'predicted_price': round(base_price),
                    'price_range': {
                        'lower': lower_bound,
                        'upper': upper_bound
                    },
                    'status': 'success'
                }
            return result

        except Exception as e:
            return {
                'predicted_price': None,
                'price_range': None,
                'status': 'error',
                'message': str(e)
            }
