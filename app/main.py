from fastapi import FastAPI

app = FastAPI(
    title="HonDealz API Documentation",
    description="Second-Hand Honda Motorcycle Price Prediction Application",
    version="1.0.0"
)

@app.post("/ai-models/motor-image-recognition")
def motor_image_recognition():
    return { "message": "API for Motocycle Image Recognition Model" }

@app.post("/ai-models/motor-price-estimator")
def motor_price_estimator():
    return { "message": "API for Second-Hand Motor Price Estimator Model" }
