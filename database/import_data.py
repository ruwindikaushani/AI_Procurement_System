import pandas as pd
import mysql.connector

# Read the CSV file
df = pd.read_csv("vendor_dataset.csv")
# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="procurement_ai"
)

cursor = conn.cursor()

# Insert data
for index, row in df.iterrows():
    sql = """
    INSERT INTO vendors
    (VendorID, VendorName, Category, PriceScore, QualityScore,
    DeliveryScore, VendorScore, ComplaintCount, ReliabilityScore,
    OnTimeDeliveryRate, ContractValue, RiskLevel)

    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    values = (
        row["VendorID"],
        row["VendorName"],
        row["Category"],
        row["PriceScore"],
        row["QualityScore"],
        row["DeliveryScore"],
        row["VendorScore"],
        row["ComplaintCount"],
        row["ReliabilityScore"],
        row["OnTimeDeliveryRate"],
        row["ContractValue"],
        row["RiskLevel"]
    )

    cursor.execute(sql, values)

conn.commit()

print("Data Imported Successfully!")
print("Total Records:", len(df))

cursor.close()
conn.close()