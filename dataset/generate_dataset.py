import pandas as pd
import random

vendors = [
    "TechGlobal Solutions",
    "SmartTech Distributors",
    "Digital Edge Suppliers",
    "Alpha IT Systems",
    "FutureNet Technologies",
    "Elite Office Solutions",
    "Prime Stationery Traders",
    "OfficeMart Lanka",
    "Lanka Industrial Suppliers",
    "ABC Raw Materials"
]

categories = [
    "IT Equipment",
    "Office Supplies",
    "Raw Materials",
    "Electrical Items",
    "Mechanical Parts",
    "Safety Equipment",
    "Furniture",
    "Logistics Services"
]

data = []

for i in range(1500):

    vendor_id = f"V{i+1:04d}"

    vendor_name = random.choice(vendors)

    category = random.choice(categories)

    price_score = random.randint(40, 100)
    quality_score = random.randint(40, 100)
    delivery_score = random.randint(40, 100)

    complaint_count = random.randint(0, 20)

    reliability_score = random.randint(40, 100)

    on_time_delivery_rate = random.randint(40, 100)

    contract_value = random.randint(50000, 5000000)

    complaint_score = max(0, 100 - (complaint_count * 5))

    vendor_score = round(
        (price_score * 0.25)
        + (quality_score * 0.25)
        + (delivery_score * 0.20)
        + (reliability_score * 0.20)
        + (complaint_score * 0.10),
        2
    )

    if vendor_score >= 80:
        risk_level = "Low"
    elif vendor_score >= 60:
        risk_level = "Medium"
    else:
        risk_level = "High"

    data.append([
        vendor_id,
        vendor_name,
        category,
        price_score,
        quality_score,
        delivery_score,
        complaint_count,
        reliability_score,
        on_time_delivery_rate,
        contract_value,
        vendor_score,
        risk_level
    ])

df = pd.DataFrame(data, columns=[
    "VendorID",
    "VendorName",
    "Category",
    "PriceScore",
    "QualityScore",
    "DeliveryScore",
    "ComplaintCount",
    "ReliabilityScore",
    "OnTimeDeliveryRate",
    "ContractValue",
    "VendorScore",
    "RiskLevel"
])

df.to_csv("vendor_dataset.csv", index=False)

print("Dataset created successfully!")
print("Total Records:", len(df))