from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import pickle
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = "procurement_ai_secret_key"

# ============================================================
# LOGIN / LOGOUT
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Check username and password from MySQL
        cursor.execute("""
            SELECT UserID, Username, Password, Role
            FROM users
            WHERE Username = %s
            LIMIT 1
        """, (username,))

        user = cursor.fetchone()

        # Validate login credentials
        if user and password == user["Password"]:

            session["logged_in"] = True
            session["user_id"] = user["UserID"]
            session["username"] = user["Username"]
            session["role"] = user["Role"]

            return redirect(url_for("dashboard"))

        # Invalid login
        return render_template(
            "login.html",
            error="Invalid username or password."
        )

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


@app.before_request
def require_login():

    public_endpoints = {"login", "static"}

    if request.endpoint in public_endpoints:
        return

    if not session.get("logged_in"):
        return redirect(url_for("login"))


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(
    BASE_DIR,
    "model",
    "risk_model.pkl"
)

CSV_PATH = os.path.join(
    BASE_DIR,
    "vendor_dataset.csv"
)


# ============================================================
# MYSQL CONNECTION
# ============================================================

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="procurement_ai"
)

cursor = conn.cursor(dictionary=True)


# ============================================================
# LOAD AI MODEL
# ============================================================

with open(MODEL_PATH, "rb") as file:
    model = pickle.load(file)


# ============================================================
# DATABASE SETUP
# ============================================================

def setup_database():

    # --------------------------------------------------------
    # Check ItemMaterial
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'procurement_ai'
        AND TABLE_NAME = 'vendors'
        AND COLUMN_NAME = 'ItemMaterial'
    """)

    result = cursor.fetchone()

    if result["count"] == 0:

        print("Adding ItemMaterial column...")

        cursor.execute("""
            ALTER TABLE vendors
            ADD COLUMN ItemMaterial VARCHAR(255)
            AFTER Category
        """)

        conn.commit()

        print("ItemMaterial column added successfully.")


    # --------------------------------------------------------
    # Check UnitPrice
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'procurement_ai'
        AND TABLE_NAME = 'vendors'
        AND COLUMN_NAME = 'UnitPrice'
    """)

    result = cursor.fetchone()

    if result["count"] == 0:

        print("Adding UnitPrice column...")

        cursor.execute("""
            ALTER TABLE vendors
            ADD COLUMN UnitPrice DECIMAL(12,2)
            AFTER ItemMaterial
        """)

        conn.commit()

        print("UnitPrice column added successfully.")



    # --------------------------------------------------------
    # Procurement Transactions table
    # --------------------------------------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS procurement_transactions (
            TransactionID VARCHAR(20) PRIMARY KEY,
            VendorID VARCHAR(20) NOT NULL,
            ItemMaterial VARCHAR(255) NOT NULL,
            Category VARCHAR(100) NOT NULL,
            Quantity INT NOT NULL,
            UnitPrice DECIMAL(12,2) NOT NULL,
            TotalValue DECIMAL(14,2) NOT NULL,
            TransactionDate DATE NOT NULL,
            DeliveryStatus VARCHAR(50) NOT NULL,
            PaymentStatus VARCHAR(50) NOT NULL
        )
    """)
    conn.commit()

# Run database setup
setup_database()


# ============================================================
# SYNCHRONIZE CSV DATA
# ============================================================

def sync_csv_data():

    if not os.path.exists(CSV_PATH):

        print(
            "CSV file not found:",
            CSV_PATH
        )

        return


    try:

        df = pd.read_csv(CSV_PATH)

        required_columns = [
            "VendorID",
            "ItemMaterial",
            "UnitPrice"
        ]

        for column in required_columns:

            if column not in df.columns:

                print(
                    f"{column} column missing from CSV."
                )

                return


        updated = 0


        for _, row in df.iterrows():

            vendor_id = str(
                row["VendorID"]
            ).strip()


            item_material = str(
                row["ItemMaterial"]
            ).strip()


            if not item_material or item_material.lower() == "nan":

                item_material = "Not specified"


            unit_price = row["UnitPrice"]


            if pd.isna(unit_price):

                unit_price = None


            cursor.execute("""
                UPDATE vendors
                SET
                    ItemMaterial = %s,
                    UnitPrice = %s
                WHERE VendorID = %s
            """, (
                item_material,
                unit_price,
                vendor_id
            ))


            if cursor.rowcount > 0:

                updated += cursor.rowcount


        conn.commit()


        print(
            "CSV synchronization completed."
        )

        print(
            "Updated rows:",
            updated
        )


    except Exception as e:

        print(
            "Error synchronizing CSV:",
            e
        )


# Synchronize CSV
sync_csv_data()


# ============================================================
# GENERATE VENDOR ID
# ============================================================

def generate_vendor_id():

    cursor.execute("""
        SELECT VendorID
        FROM vendors
        ORDER BY VendorID DESC
        LIMIT 1
    """)

    result = cursor.fetchone()


    if not result:

        return "V0001"


    last_id = result["VendorID"]


    try:

        number = int(
            last_id.replace("V", "")
        )

        number += 1

        return "V" + str(
            number
        ).zfill(4)


    except ValueError:

        return "V0001"


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/")
def dashboard():

    # --------------------------------------------------------
    # TOTAL VENDORS
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM vendors
    """)

    total = cursor.fetchone()["total"]

    # --------------------------------------------------------
    # LOW RISK VENDORS
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM vendors
        WHERE RiskLevel = 'Low'
    """)

    low = cursor.fetchone()["total"]

    # --------------------------------------------------------
    # MEDIUM RISK VENDORS
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM vendors
        WHERE RiskLevel = 'Medium'
    """)

    medium = cursor.fetchone()["total"]

    # --------------------------------------------------------
    # HIGH RISK VENDORS
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM vendors
        WHERE RiskLevel = 'High'
    """)

    high = cursor.fetchone()["total"]

    # --------------------------------------------------------
    # RISK PERCENTAGES
    # --------------------------------------------------------

    if total > 0:
        low_percent = round((low / total) * 100, 1)
        medium_percent = round((medium / total) * 100, 1)
        high_percent = round((high / total) * 100, 1)
    else:
        low_percent = 0
        medium_percent = 0
        high_percent = 0

    # --------------------------------------------------------
    # PROCUREMENT TRANSACTION SUMMARY
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            COUNT(*) AS total_transactions,
            COALESCE(SUM(TotalValue), 0) AS total_procurement_value
        FROM procurement_transactions
    """)

    transaction_summary = cursor.fetchone()

    total_transactions = transaction_summary["total_transactions"]

    total_procurement_value = float(
        transaction_summary["total_procurement_value"] or 0
    )

    # --------------------------------------------------------
    # SEND DATA TO DASHBOARD
    # --------------------------------------------------------

    return render_template(
        "dashboard.html",

        # Original variable names
        total=total,
        low=low,
        medium=medium,
        high=high,

        # Variable names used by the new dashboard
        total_vendors=total,
        low_risk=low,
        medium_risk=medium,
        high_risk=high,

        # Risk percentages
        low_percent=low_percent,
        medium_percent=medium_percent,
        high_percent=high_percent,

        # Procurement transaction information
        total_transactions=total_transactions,
        total_procurement_value=total_procurement_value
    )


# ============================================================
# ADD VENDOR
# ============================================================

@app.route(
    "/add_vendor",
    methods=["GET", "POST"]
)
def add_vendor():

    if request.method == "POST":

        vendor_name = request.form[
            "VendorName"
        ]

        category = request.form[
            "Category"
        ]


        item_material = request.form.get(
            "ItemMaterial",
            "Not specified"
        ).strip()


        # Actual unit price
        unit_price = float(
            request.form.get(
                "UnitPrice",
                0
            )
        )


        price = float(
            request.form[
                "PriceScore"
            ]
        )


        quality = float(
            request.form[
                "QualityScore"
            ]
        )


        delivery = float(
            request.form[
                "DeliveryScore"
            ]
        )


        complaints = int(
            request.form[
                "ComplaintCount"
            ]
        )


        reliability = float(
            request.form[
                "ReliabilityScore"
            ]
        )


        ontime = float(
            request.form[
                "OnTimeDeliveryRate"
            ]
        )


        contract = float(
            request.form[
                "ContractValue"
            ]
        )


        # ----------------------------------------------------
        # GENERATE ID
        # ----------------------------------------------------

        vendor_id = generate_vendor_id()


        # ----------------------------------------------------
        # VENDOR SCORE
        # ----------------------------------------------------

        vendor_score = round(
            (
                price
                + quality
                + delivery
                + reliability
                + ontime
                - (complaints * 2)
            ) / 5,
            2
        )


        # ----------------------------------------------------
        # AI PREDICTION
        # ----------------------------------------------------

        sample = pd.DataFrame([{

            "PriceScore": price,

            "QualityScore": quality,

            "DeliveryScore": delivery,

            "ComplaintCount": complaints,

            "ReliabilityScore": reliability,

            "OnTimeDeliveryRate": ontime,

            "ContractValue": contract,

            "VendorScore": vendor_score

        }])


        risk_level = str(
            model.predict(sample)[0]
        )


        # ----------------------------------------------------
        # INSERT
        # ----------------------------------------------------

        sql = """
            INSERT INTO vendors
            (
                VendorID,
                VendorName,
                Category,
                ItemMaterial,
                UnitPrice,
                PriceScore,
                QualityScore,
                DeliveryScore,
                VendorScore,
                ComplaintCount,
                ReliabilityScore,
                OnTimeDeliveryRate,
                ContractValue,
                RiskLevel
            )

            VALUES
            (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """


        values = (

            vendor_id,

            vendor_name,

            category,

            item_material,

            unit_price,

            price,

            quality,

            delivery,

            vendor_score,

            complaints,

            reliability,

            ontime,

            contract,

            risk_level

        )


        cursor.execute(
            sql,
            values
        )

        conn.commit()


        return redirect(
            "/vendors"
        )


    return render_template(
        "add_vendor.html"
    )


# ============================================================
# VENDOR MANAGEMENT
# ============================================================

@app.route("/vendors")
def vendors():

    search = request.args.get(
        "search",
        ""
    ).strip()


    risk = request.args.get(
        "risk",
        ""
    ).strip()


    category = request.args.get(
        "category",
        ""
    ).strip()


    query = """
        SELECT *
        FROM vendors
        WHERE 1 = 1
    """


    values = []


    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if search:

        query += """
            AND (
                VendorID LIKE %s
                OR VendorName LIKE %s
                OR ItemMaterial LIKE %s
            )
        """

        search_value = (
            "%" + search + "%"
        )


        values.extend([
            search_value,
            search_value,
            search_value
        ])


    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    if risk:

        query += """
            AND RiskLevel = %s
        """

        values.append(
            risk
        )


    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    if category:

        query += """
            AND Category = %s
        """

        values.append(
            category
        )


    query += """
        ORDER BY VendorID ASC
    """


    cursor.execute(
        query,
        tuple(values)
    )


    vendors_list = cursor.fetchall()


    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM vendors
    """)

    total = cursor.fetchone()["total"]


    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM vendors
        WHERE RiskLevel = 'Low'
    """)

    low = cursor.fetchone()["total"]


    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM vendors
        WHERE RiskLevel = 'Medium'
    """)

    medium = cursor.fetchone()["total"]


    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM vendors
        WHERE RiskLevel = 'High'
    """)

    high = cursor.fetchone()["total"]


    # --------------------------------------------------------
    # CATEGORIES
    # --------------------------------------------------------

    cursor.execute("""
        SELECT DISTINCT Category
        FROM vendors
        ORDER BY Category
    """)


    categories = cursor.fetchall()


    return render_template(

        "vendors.html",

        vendors=vendors_list,

        total=total,

        low=low,

        medium=medium,

        high=high,

        categories=categories,

        search=search,

        selected_risk=risk,

        selected_category=category

    )


# ============================================================
# VIEW VENDOR
# ============================================================

@app.route(
    "/view_vendor/<vendor_id>"
)
def view_vendor(vendor_id):

    cursor.execute("""
        SELECT *
        FROM vendors
        WHERE VendorID = %s
    """, (
        vendor_id,
    ))


    vendor = cursor.fetchone()


    if not vendor:

        return "Vendor not found", 404


    return render_template(
        "vendor_detail.html",
        vendor=vendor
    )


# ============================================================
# EDIT VENDOR
# ============================================================

@app.route(
    "/edit_vendor/<vendor_id>",
    methods=["GET", "POST"]
)
def edit_vendor(vendor_id):

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":

        cursor.execute("""
            SELECT *
            FROM vendors
            WHERE VendorID = %s
        """, (
            vendor_id,
        ))


        vendor = cursor.fetchone()


        if not vendor:

            return "Vendor not found", 404


        return render_template(
            "edit_vendor.html",
            vendor=vendor
        )


    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    vendor_name = request.form[
        "VendorName"
    ]


    category = request.form[
        "Category"
    ]


    item_material = request.form.get(
        "ItemMaterial",
        "Not specified"
    ).strip()


    unit_price = float(
        request.form.get(
            "UnitPrice",
            0
        )
    )


    price = float(
        request.form[
            "PriceScore"
        ]
    )


    quality = float(
        request.form[
            "QualityScore"
        ]
    )


    delivery = float(
        request.form[
            "DeliveryScore"
        ]
    )


    complaints = int(
        request.form[
            "ComplaintCount"
        ]
    )


    reliability = float(
        request.form[
            "ReliabilityScore"
        ]
    )


    ontime = float(
        request.form[
            "OnTimeDeliveryRate"
        ]
    )


    contract = float(
        request.form[
            "ContractValue"
        ]
    )


    # --------------------------------------------------------
    # VENDOR SCORE
    # --------------------------------------------------------

    vendor_score = round(
        (
            price
            + quality
            + delivery
            + reliability
            + ontime
            - (complaints * 2)
        ) / 5,
        2
    )


    # --------------------------------------------------------
    # AI RISK
    # --------------------------------------------------------

    sample = pd.DataFrame([{

        "PriceScore": price,

        "QualityScore": quality,

        "DeliveryScore": delivery,

        "ComplaintCount": complaints,

        "ReliabilityScore": reliability,

        "OnTimeDeliveryRate": ontime,

        "ContractValue": contract,

        "VendorScore": vendor_score

    }])


    risk_level = str(
        model.predict(sample)[0]
    )


    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    cursor.execute("""
        UPDATE vendors

        SET

            VendorName = %s,

            Category = %s,

            ItemMaterial = %s,

            UnitPrice = %s,

            PriceScore = %s,

            QualityScore = %s,

            DeliveryScore = %s,

            VendorScore = %s,

            ComplaintCount = %s,

            ReliabilityScore = %s,

            OnTimeDeliveryRate = %s,

            ContractValue = %s,

            RiskLevel = %s

        WHERE VendorID = %s
    """, (

        vendor_name,

        category,

        item_material,

        unit_price,

        price,

        quality,

        delivery,

        vendor_score,

        complaints,

        reliability,

        ontime,

        contract,

        risk_level,

        vendor_id

    ))


    conn.commit()


    return redirect(
        "/vendors"
    )


# ============================================================
# DELETE VENDOR
# ============================================================

@app.route(
    "/delete_vendor/<vendor_id>",
    methods=["POST"]
)
def delete_vendor(vendor_id):

    cursor.execute("""
        DELETE FROM vendors
        WHERE VendorID = %s
    """, (
        vendor_id,
    ))


    conn.commit()


    return {
        "success": True,
        "message": "Vendor deleted successfully."
    }


# ============================================================
# AI PREDICTION
# ============================================================

@app.route(
    "/ai_prediction",
    methods=["GET", "POST"]
)
def ai_prediction():

    prediction = None

    form_data = {}


    if request.method == "POST":

        form_data = request.form.to_dict()


        price = float(
            request.form[
                "PriceScore"
            ]
        )


        quality = float(
            request.form[
                "QualityScore"
            ]
        )


        delivery = float(
            request.form[
                "DeliveryScore"
            ]
        )


        complaints = int(
            request.form[
                "ComplaintCount"
            ]
        )


        reliability = float(
            request.form[
                "ReliabilityScore"
            ]
        )


        ontime = float(
            request.form[
                "OnTimeDeliveryRate"
            ]
        )


        contract = float(
            request.form[
                "ContractValue"
            ]
        )


        # ----------------------------------------------------
        # SCORE
        # ----------------------------------------------------

        vendor_score = round(
            (
                price
                + quality
                + delivery
                + reliability
                + ontime
                - (complaints * 2)
            ) / 5,
            2
        )


        # ----------------------------------------------------
        # MODEL INPUT
        # ----------------------------------------------------

        sample = pd.DataFrame([{

            "PriceScore": price,

            "QualityScore": quality,

            "DeliveryScore": delivery,

            "ComplaintCount": complaints,

            "ReliabilityScore": reliability,

            "OnTimeDeliveryRate": ontime,

            "ContractValue": contract,

            "VendorScore": vendor_score

        }])


        prediction = str(
            model.predict(sample)[0]
        )


    return render_template(

        "ai_prediction.html",

        prediction=prediction,

        form_data=form_data

    )



# ============================================================
# PROCUREMENT TRANSACTIONS
# ============================================================

def generate_transaction_id():
    cursor.execute("""
        SELECT TransactionID FROM procurement_transactions
        ORDER BY TransactionID DESC LIMIT 1
    """)
    result = cursor.fetchone()

    if not result:
        return "T0001"

    try:
        number = int(result["TransactionID"].replace("T", "")) + 1
        return "T" + str(number).zfill(4)
    except ValueError:
        return "T0001"


@app.route("/transactions", methods=["GET", "POST"])
def transactions():

    if request.method == "POST":
        vendor_id = request.form["VendorID"]
        item_material = request.form["ItemMaterial"].strip()
        category = request.form["Category"].strip()
        quantity = int(request.form["Quantity"])
        unit_price = float(request.form["UnitPrice"])
        total_value = quantity * unit_price
        transaction_date = request.form["TransactionDate"]
        delivery_status = request.form["DeliveryStatus"]
        payment_status = request.form["PaymentStatus"]

        transaction_id = generate_transaction_id()

        cursor.execute("""
            INSERT INTO procurement_transactions
            (TransactionID, VendorID, ItemMaterial, Category, Quantity,
             UnitPrice, TotalValue, TransactionDate, DeliveryStatus, PaymentStatus)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            transaction_id, vendor_id, item_material, category, quantity,
            unit_price, total_value, transaction_date,
            delivery_status, payment_status
        ))

        conn.commit()
        return redirect(url_for("transactions"))

    cursor.execute("""
        SELECT VendorID, VendorName, Category
        FROM vendors ORDER BY VendorName
    """)
    vendor_list = cursor.fetchall()

    cursor.execute("""
        SELECT t.*, v.VendorName
        FROM procurement_transactions t
        LEFT JOIN vendors v ON t.VendorID = v.VendorID
        ORDER BY t.TransactionDate DESC, t.TransactionID DESC
    """)
    transaction_list = cursor.fetchall()

    cursor.execute("""
        SELECT COALESCE(SUM(TotalValue), 0) AS total_value,
               COUNT(*) AS total_transactions
        FROM procurement_transactions
    """)
    summary = cursor.fetchone()

    return render_template(
        "transactions.html",
        vendors=vendor_list,
        transactions=transaction_list,
        total_value=summary["total_value"],
        total_transactions=summary["total_transactions"]
    )


@app.route("/delete_transaction/<transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):
    cursor.execute("""
        DELETE FROM procurement_transactions
        WHERE TransactionID = %s
    """, (transaction_id,))
    conn.commit()
    return redirect(url_for("transactions"))


# ============================================================
# REPORTS
# ============================================================

@app.route("/reports")
def reports():

    # --------------------------------------------------------
    # TOTAL
    # --------------------------------------------------------

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM vendors
    """)


    total = cursor.fetchone()["total"]


    # --------------------------------------------------------
    # RISK COUNTS
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            RiskLevel,
            COUNT(*) AS count
        FROM vendors
        GROUP BY RiskLevel
    """)


    risk_data = cursor.fetchall()


    low = 0

    medium = 0

    high = 0


    for row in risk_data:

        if row["RiskLevel"] == "Low":

            low = row["count"]


        elif row["RiskLevel"] == "Medium":

            medium = row["count"]


        elif row["RiskLevel"] == "High":

            high = row["count"]


    # --------------------------------------------------------
    # PERCENTAGES
    # --------------------------------------------------------

    if total > 0:

        low_percent = round(
            (low / total) * 100,
            1
        )

        medium_percent = round(
            (medium / total) * 100,
            1
        )

        high_percent = round(
            (high / total) * 100,
            1
        )

    else:

        low_percent = 0

        medium_percent = 0

        high_percent = 0


    # --------------------------------------------------------
    # AVERAGE PERFORMANCE
    # --------------------------------------------------------

    cursor.execute("""
        SELECT

            AVG(PriceScore)
                AS avg_price,

            AVG(QualityScore)
                AS avg_quality,

            AVG(DeliveryScore)
                AS avg_delivery,

            AVG(ReliabilityScore)
                AS avg_reliability,

            AVG(OnTimeDeliveryRate)
                AS avg_ontime,

            AVG(VendorScore)
                AS avg_vendor_score,

            AVG(UnitPrice)
                AS avg_unit_price

        FROM vendors
    """)


    averages = cursor.fetchone()


    avg_price = round(
        averages["avg_price"] or 0,
        2
    )


    avg_quality = round(
        averages["avg_quality"] or 0,
        2
    )


    avg_delivery = round(
        averages["avg_delivery"] or 0,
        2
    )


    avg_reliability = round(
        averages["avg_reliability"] or 0,
        2
    )


    avg_ontime = round(
        averages["avg_ontime"] or 0,
        2
    )


    avg_vendor_score = round(
        averages["avg_vendor_score"] or 0,
        2
    )


    avg_unit_price = round(
        averages["avg_unit_price"] or 0,
        2
    )


    # --------------------------------------------------------
    # PROCUREMENT TRANSACTION ANALYTICS
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            COUNT(*) AS total_transactions,
            COALESCE(SUM(TotalValue), 0) AS total_procurement_value,
            COALESCE(AVG(TotalValue), 0) AS avg_transaction_value
        FROM procurement_transactions
    """)

    transaction_summary = cursor.fetchone()

    total_transactions = transaction_summary["total_transactions"]
    total_procurement_value = round(
        float(transaction_summary["total_procurement_value"] or 0),
        2
    )
    avg_transaction_value = round(
        float(transaction_summary["avg_transaction_value"] or 0),
        2
    )

    # Spending by procurement category
    cursor.execute("""
        SELECT
            Category,
            COUNT(*) AS transaction_count,
            COALESCE(SUM(TotalValue), 0) AS total_value
        FROM procurement_transactions
        GROUP BY Category
        ORDER BY total_value DESC
    """)

    transaction_categories = cursor.fetchall()

    # Delivery status summary
    cursor.execute("""
        SELECT DeliveryStatus, COUNT(*) AS count
        FROM procurement_transactions
        GROUP BY DeliveryStatus
        ORDER BY count DESC
    """)

    delivery_status_data = cursor.fetchall()

    # Payment status summary
    cursor.execute("""
        SELECT PaymentStatus, COUNT(*) AS count
        FROM procurement_transactions
        GROUP BY PaymentStatus
        ORDER BY count DESC
    """)

    payment_status_data = cursor.fetchall()


    # --------------------------------------------------------
    # PRICE COMPARISON
    # --------------------------------------------------------
    # Compare vendors offering the same item/material.
    # Only groups with more than one vendor are useful for comparison.
    cursor.execute("""
        SELECT
            ItemMaterial,
            VendorID,
            VendorName,
            Category,
            UnitPrice,
            VendorScore,
            RiskLevel
        FROM vendors
        WHERE ItemMaterial IS NOT NULL
          AND ItemMaterial <> ''
          AND UnitPrice IS NOT NULL
        ORDER BY ItemMaterial ASC, UnitPrice ASC, VendorScore DESC
    """)
    price_comparison_data = cursor.fetchall()

    # --------------------------------------------------------
    # PROCUREMENT TREND ANALYSIS
    # --------------------------------------------------------
    # Monthly procurement value and transaction count.
    cursor.execute("""
        SELECT
            DATE_FORMAT(TransactionDate, '%Y-%m') AS month,
            DATE_FORMAT(TransactionDate, '%b %Y') AS month_label,
            COUNT(*) AS transaction_count,
            COALESCE(SUM(TotalValue), 0) AS total_value,
            COALESCE(AVG(UnitPrice), 0) AS avg_unit_price
        FROM procurement_transactions
        GROUP BY
            DATE_FORMAT(TransactionDate, '%Y-%m'),
            DATE_FORMAT(TransactionDate, '%b %Y')
        ORDER BY month ASC
    """)
    procurement_trend_data = cursor.fetchall()

    # --------------------------------------------------------
    # HIGH RISK VENDORS
    # --------------------------------------------------------

    cursor.execute("""
        SELECT

            VendorID,

            VendorName,

            Category,

            ItemMaterial,

            UnitPrice,

            VendorScore,

            RiskLevel

        FROM vendors

        WHERE RiskLevel = 'High'

        ORDER BY VendorScore ASC

        LIMIT 10
    """)


    high_risk_vendors = cursor.fetchall()


    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    return render_template(

        "reports.html",

        total=total,

        low=low,

        medium=medium,

        high=high,

        low_percent=low_percent,

        medium_percent=medium_percent,

        high_percent=high_percent,

        avg_price=avg_price,

        avg_quality=avg_quality,

        avg_delivery=avg_delivery,

        avg_reliability=avg_reliability,

        avg_ontime=avg_ontime,

        avg_vendor_score=avg_vendor_score,

        avg_unit_price=avg_unit_price,

        total_transactions=total_transactions,
        total_procurement_value=total_procurement_value,
        avg_transaction_value=avg_transaction_value,
        transaction_categories=transaction_categories,
        delivery_status_data=delivery_status_data,
        payment_status_data=payment_status_data,

        price_comparison_data=price_comparison_data,
        procurement_trend_data=procurement_trend_data,

        high_risk_vendors=high_risk_vendors

    )



# ============================================================
# PRICE & TREND ANALYSIS
# ============================================================

@app.route("/price_trends")
def price_trends():

    # --------------------------------------------------------
    # SEARCH / FILTERS
    # --------------------------------------------------------

    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    risk = request.args.get("risk", "").strip()

    # --------------------------------------------------------
    # PRICE RECORDS
    # --------------------------------------------------------

    query = """
        SELECT
            VendorID,
            VendorName,
            Category,
            COALESCE(NULLIF(ItemMaterial, ''), 'Not specified') AS ItemMaterial,
            UnitPrice,
            VendorScore,
            RiskLevel
        FROM vendors
        WHERE UnitPrice IS NOT NULL
          AND UnitPrice >= 0
    """

    values = []

    if search:
        query += """
            AND (
                VendorID LIKE %s
                OR VendorName LIKE %s
                OR ItemMaterial LIKE %s
                OR Category LIKE %s
            )
        """

        search_value = "%" + search + "%"
        values.extend([
            search_value,
            search_value,
            search_value,
            search_value
        ])

    if category:
        query += """
            AND Category = %s
        """
        values.append(category)

    if risk:
        query += """
            AND RiskLevel = %s
        """
        values.append(risk)

    query += """
        ORDER BY
            ItemMaterial ASC,
            UnitPrice ASC,
            VendorScore DESC
    """

    cursor.execute(query, tuple(values))
    price_data = cursor.fetchall()

    # --------------------------------------------------------
    # PRICE STATISTICS
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            COALESCE(MIN(UnitPrice), 0) AS lowest_price,
            COALESCE(MAX(UnitPrice), 0) AS highest_price,
            COALESCE(AVG(UnitPrice), 0) AS average_price,
            COUNT(UnitPrice) AS priced_vendor_count
        FROM vendors
        WHERE UnitPrice IS NOT NULL
          AND UnitPrice >= 0
    """)

    price_summary = cursor.fetchone()

    lowest_price = round(float(price_summary["lowest_price"] or 0), 2)
    highest_price = round(float(price_summary["highest_price"] or 0), 2)
    average_price = round(float(price_summary["average_price"] or 0), 2)
    priced_vendor_count = int(price_summary["priced_vendor_count"] or 0)

    # --------------------------------------------------------
    # PRICE COMPARISON BY ITEM / MATERIAL
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            COALESCE(NULLIF(ItemMaterial, ''), 'Not specified') AS ItemMaterial,
            COUNT(*) AS vendor_count,
            MIN(UnitPrice) AS lowest_price,
            MAX(UnitPrice) AS highest_price,
            AVG(UnitPrice) AS average_price
        FROM vendors
        WHERE UnitPrice IS NOT NULL
          AND UnitPrice >= 0
        GROUP BY COALESCE(NULLIF(ItemMaterial, ''), 'Not specified')
        ORDER BY ItemMaterial ASC
    """)

    item_price_summary = cursor.fetchall()

    # --------------------------------------------------------
    # CATEGORY LIST
    # --------------------------------------------------------

    cursor.execute("""
        SELECT DISTINCT Category
        FROM vendors
        WHERE Category IS NOT NULL
          AND Category <> ''
        ORDER BY Category
    """)

    price_categories = cursor.fetchall()

    # --------------------------------------------------------
    # RISK SUMMARY
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            RiskLevel,
            COUNT(*) AS vendor_count,
            COALESCE(AVG(UnitPrice), 0) AS average_price,
            COALESCE(AVG(VendorScore), 0) AS average_vendor_score
        FROM vendors
        WHERE UnitPrice IS NOT NULL
        GROUP BY RiskLevel
        ORDER BY
            CASE RiskLevel
                WHEN 'Low' THEN 1
                WHEN 'Medium' THEN 2
                WHEN 'High' THEN 3
                ELSE 4
            END
    """)

    risk_summary = cursor.fetchall()

    # --------------------------------------------------------
    # MONTHLY PROCUREMENT TREND
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            DATE_FORMAT(TransactionDate, '%Y-%m') AS month,
            DATE_FORMAT(TransactionDate, '%b %Y') AS month_label,
            COUNT(*) AS transaction_count,
            COALESCE(SUM(TotalValue), 0) AS total_value,
            COALESCE(AVG(UnitPrice), 0) AS avg_unit_price
        FROM procurement_transactions
        GROUP BY
            DATE_FORMAT(TransactionDate, '%Y-%m'),
            DATE_FORMAT(TransactionDate, '%b %Y')
        ORDER BY month ASC
    """)

    trend_data = cursor.fetchall()

    # --------------------------------------------------------
    # CATEGORY SPENDING TREND
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            Category,
            COUNT(*) AS transaction_count,
            COALESCE(SUM(TotalValue), 0) AS total_value,
            COALESCE(AVG(UnitPrice), 0) AS average_unit_price
        FROM procurement_transactions
        GROUP BY Category
        ORDER BY total_value DESC
    """)

    spending_trend = cursor.fetchall()

    # --------------------------------------------------------
    # PROCUREMENT SUMMARY
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            COUNT(*) AS total_transactions,
            COALESCE(SUM(TotalValue), 0) AS total_spending,
            COALESCE(AVG(TotalValue), 0) AS average_transaction
        FROM procurement_transactions
    """)

    procurement_summary = cursor.fetchone()

    total_transactions = int(procurement_summary["total_transactions"] or 0)
    total_spending = round(float(procurement_summary["total_spending"] or 0), 2)
    average_transaction = round(float(procurement_summary["average_transaction"] or 0), 2)

    # --------------------------------------------------------
    # HIGH-RISK PRICE RECORDS
    # --------------------------------------------------------

    cursor.execute("""
        SELECT
            VendorID,
            VendorName,
            Category,
            COALESCE(NULLIF(ItemMaterial, ''), 'Not specified') AS ItemMaterial,
            UnitPrice,
            VendorScore,
            RiskLevel
        FROM vendors
        WHERE RiskLevel = 'High'
          AND UnitPrice IS NOT NULL
        ORDER BY UnitPrice DESC
        LIMIT 20
    """)

    high_risk_price_data = cursor.fetchall()

    # --------------------------------------------------------
    # RENDER PAGE
    # --------------------------------------------------------

    return render_template(
        "price_trends.html",
        price_data=price_data,
        item_price_summary=item_price_summary,
        risk_summary=risk_summary,
        trend_data=trend_data,
        spending_trend=spending_trend,
        high_risk_price_data=high_risk_price_data,
        price_categories=price_categories,
        lowest_price=lowest_price,
        highest_price=highest_price,
        average_price=average_price,
        priced_vendor_count=priced_vendor_count,
        total_transactions=total_transactions,
        total_spending=total_spending,
        average_transaction=average_transaction,
        search=search,
        selected_category=category,
        selected_risk=risk
    )


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )