import pickle
import pandas as pd

# Load trained model
with open("model/risk_model.pkl", "rb") as file:
    model = pickle.load(file)

# Sample vendor data
sample_vendor = pd.DataFrame([{
  
    "PriceScore": 45,
    "QualityScore": 50,
    "DeliveryScore": 45,
    "ComplaintCount": 15,
    "ReliabilityScore": 40,
    "OnTimeDeliveryRate": 50,
    "ContractValue": 500000,
    "VendorScore": 48
}])


# Predict
prediction = model.predict(sample_vendor)

print("Predicted Risk Level:", prediction[0])