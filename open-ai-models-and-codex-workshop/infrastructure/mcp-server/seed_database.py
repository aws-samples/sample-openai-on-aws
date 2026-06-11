import sqlite3
import random
from datetime import datetime, timedelta

random.seed(42)

db = sqlite3.connect("workshop.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE customers (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    plan_tier TEXT NOT NULL,
    region TEXT NOT NULL,
    signup_date TEXT NOT NULL
)""")

cursor.execute("""
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    monthly_price REAL NOT NULL
)""")

cursor.execute("""
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
)""")

cursor.execute("""
CREATE TABLE tickets (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    subject TEXT NOT NULL,
    status TEXT NOT NULL,
    priority TEXT NOT NULL,
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(id)
)""")

products = [
    ("EC2 Standard", "compute", 45.00),
    ("EC2 GPU", "compute", 320.00),
    ("Lambda Pro", "compute", 25.00),
    ("ECS Fargate", "compute", 55.00),
    ("S3 Standard", "storage", 23.00),
    ("S3 Glacier", "storage", 4.00),
    ("EBS Performance", "storage", 35.00),
    ("EFS Shared", "storage", 30.00),
    ("RDS PostgreSQL", "database", 85.00),
    ("DynamoDB", "database", 65.00),
    ("Aurora Serverless", "database", 120.00),
    ("ElastiCache", "database", 75.00),
    ("Bedrock Pro", "ai-ml", 200.00),
    ("SageMaker Studio", "ai-ml", 150.00),
    ("Rekognition", "ai-ml", 40.00),
    ("Comprehend", "ai-ml", 35.00),
    ("GuardDuty", "security", 30.00),
    ("WAF Advanced", "security", 55.00),
    ("Inspector", "security", 20.00),
    ("Macie", "security", 45.00),
]
cursor.executemany(
    "INSERT INTO products (name, category, monthly_price) VALUES (?, ?, ?)",
    products
)

first_names = ["Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace",
               "Henry", "Iris", "Jack", "Karen", "Leo", "Mia", "Noah",
               "Olivia", "Pete", "Quinn", "Rosa", "Sam", "Tina"]
last_names = ["Chen", "Smith", "Patel", "Kim", "Garcia", "Mueller", "Santos",
              "Tanaka", "Williams", "Brown", "Singh", "Nakamura", "Lopez",
              "Anderson", "Taylor", "Wilson", "Martinez", "Johnson", "Lee", "Clark"]
tiers = ["free", "starter", "business", "enterprise"]
tier_weights = [0.3, 0.3, 0.25, 0.15]
regions = ["us-east", "us-west", "eu-west", "apac"]

customers = []
for i in range(1, 101):
    name = f"{random.choice(first_names)} {random.choice(last_names)}"
    email = f"{name.lower().replace(' ', '.')}+{i}@example.com"
    tier = random.choices(tiers, weights=tier_weights, k=1)[0]
    region = random.choice(regions)
    signup = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 800))
    customers.append((name, email, tier, region, signup.strftime("%Y-%m-%d")))

cursor.executemany(
    "INSERT INTO customers (name, email, plan_tier, region, signup_date) VALUES (?, ?, ?, ?, ?)",
    customers
)

orders = []
for i in range(300):
    customer_id = random.randint(1, 100)
    product_id = random.randint(1, 20)
    quantity = random.choices([1, 2, 3, 5, 10], weights=[0.4, 0.25, 0.15, 0.1, 0.1], k=1)[0]
    order_date = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 500))
    orders.append((customer_id, product_id, quantity, order_date.strftime("%Y-%m-%d")))

cursor.executemany(
    "INSERT INTO orders (customer_id, product_id, quantity, order_date) VALUES (?, ?, ?, ?)",
    orders
)

subjects = [
    "Cannot access dashboard", "Billing discrepancy", "Performance degradation",
    "Feature request: SSO", "API rate limit hit", "Data export failed",
    "Permission denied error", "Slow query performance", "Integration broken",
    "Need help with setup", "Account locked out", "Certificate expiring",
    "Deployment failed", "Monitoring alerts firing", "Cost optimization request"
]
statuses = ["open", "in_progress", "resolved", "closed"]
priorities = ["low", "medium", "high", "critical"]
priority_weights = [0.25, 0.4, 0.25, 0.1]

tickets = []
for i in range(500):
    customer_id = random.randint(1, 100)
    subject = random.choice(subjects)
    status = random.choice(statuses)
    priority = random.choices(priorities, weights=priority_weights, k=1)[0]
    created = datetime(2024, 6, 1) + timedelta(hours=random.randint(0, 8000))

    resolved = None
    if status in ("resolved", "closed"):
        hours_to_resolve = {
            "critical": random.randint(1, 8),
            "high": random.randint(4, 48),
            "medium": random.randint(12, 120),
            "low": random.randint(24, 336),
        }[priority]
        resolved = (created + timedelta(hours=hours_to_resolve)).strftime("%Y-%m-%d %H:%M:%S")

    tickets.append((customer_id, subject, status, priority,
                    created.strftime("%Y-%m-%d %H:%M:%S"), resolved))

cursor.executemany(
    "INSERT INTO tickets (customer_id, subject, status, priority, created_at, resolved_at) VALUES (?, ?, ?, ?, ?, ?)",
    tickets
)

db.commit()
db.close()
print("Created workshop.db with 100 customers, 20 products, 300 orders, 500 tickets")
