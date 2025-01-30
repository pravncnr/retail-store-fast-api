from celery import Celery
import csv
from models import PricingFeed, SessionLocal
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

app = Celery("tasks", broker="redis://localhost:6379/0")

@app.task
def process_csv_file(file_path):
    db = SessionLocal()
    try:
        with open(file_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                logger.info(row)
                record = PricingFeed(
                    store_id=row["Store ID"],
                    sku=row["SKU"],
                    product_name=row["Product Name"],
                    price=float(row["Price"]),
                    date=row["Date"],
                )
                db.add(record)
        db.commit()
    finally:
        db.close()
