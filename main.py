from typing import List

from fastapi import FastAPI, Depends, Query
from fastapi import UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from celery_worker import process_csv_file
from models import PricingFeed, SessionLocal, init_db, PricingFeedUpdate, PricingFeedResponse, PricingFeedCreate, \
    PaginatedPricingFeedResponse, UpdateRequest, SearchRequest

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.post("/upload/")
async def upload_csv(file: UploadFile, db: Session = Depends(get_db)):
    file_location = f"/tmp/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(file.file.read())

    # Trigger Celery task
    task = process_csv_file.delay(file_location)
    return JSONResponse({"message": "File uploaded successfully", "task_id": task.id})


@app.get("/status/{task_id}")
def get_task_status(task_id: str):
    from celery.result import AsyncResult
    task_result = AsyncResult(task_id)
    return {"task_id": task_id, "status": task_result.status}


@app.post("/api/search/")
async def search_records(
        search: SearchRequest,
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        db: Session = Depends(get_db),
):
    print("search", search)
    query = db.query(PricingFeed)

    # Store ID Filter
    if search.store_id:
        query = query.filter(PricingFeed.store_id == search.store_id)

    # SKU Search (Case-Insensitive)
    if search.search_sku:
        search_text = search.search_sku.lower()
        query = query.filter(func.lower(PricingFeed.sku).like(f"%{search_text}%"))

    # Product Name Search (Case-Insensitive)
    if search.search_product_name:
        search_text = search.search_product_name.lower()
        query = query.filter(func.lower(PricingFeed.product_name).like(f"%{search_text}%"))

    # Price Range Filters
    if search.search_price_from is not None and search.search_price_to is not None:
        query = query.filter(
            PricingFeed.price.between(search.search_price_from, search.search_price_to)
        )
    elif search.search_price_from is not None:
        query = query.filter(PricingFeed.price >= search.search_price_from)

    # Date Range Filters
    if search.search_date_from and search.search_date_to:
        query = query.filter(
            PricingFeed.date.between(search.search_date_from, search.search_date_to)
        )
    elif search.search_date_from:
        query = query.filter(PricingFeed.date >= search.search_date_from)

    # Sort by ID in Ascending Order
    query = query.order_by(PricingFeed.id)

    # Get Total Count for Pagination
    total_count = query.count()
    skip = (page - 1) * size
    feeds = query.offset(skip).limit(size).all()

    return {
        "total_count": total_count,
        "page": page,
        "size": size,
        "total_pages": (total_count // size) + (1 if total_count % size > 0 else 0),
        "results": feeds,
    }


@app.post("/api/pricing_feeds/bulk_update")
def bulk_update_pricing_feeds(
        updates: List[UpdateRequest],
        db: Session = Depends(get_db)
):
    """
    Bulk update pricing feed records.
    Accepts a list of updates and modifies multiple records in a single request.
    """
    updated_records = []

    for update in updates:
        db_feed = db.query(PricingFeed).filter(PricingFeed.id == update.id).first()

        if not db_feed:
            raise HTTPException(status_code=404, detail=f"Pricing feed with ID {update.id} not found")

        for key, value in update.dict(exclude_unset=True).items():
            setattr(db_feed, key, value)

        updated_records.append(db_feed)

    db.commit()
    return {"message": f"{len(updated_records)} records updated successfully"}


# Create a new pricing feed
@app.post("/api/pricing_feeds/", response_model=PricingFeedResponse)
def create_pricing_feed(feed: PricingFeedCreate, db: Session = Depends(get_db)):
    db_feed = PricingFeed(**feed.dict())
    db.add(db_feed)
    db.commit()
    db.refresh(db_feed)
    return db_feed


# Get a list of pricing feeds
@app.get("/api/pricing_feeds/", response_model=PaginatedPricingFeedResponse)
def get_pricing_feeds(
        db: Session = Depends(get_db),
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1),
        store_id: str = Query(None, description="Filter by Store ID")
):
    """
    Fetch paginated pricing feeds with total record count.
    If store_id is provided, only count records for that store.
    """
    query = db.query(PricingFeed)

    if store_id:
        query = query.filter(PricingFeed.store_id == store_id)

    query = query.order_by(getattr(PricingFeed, 'id'))  # Ascending sort

    total_count = query.count()  # Count records based on filter
    skip = (page - 1) * size
    feeds = query.offset(skip).limit(size).all()

    return {
        "total_count": total_count,
        "page": page,
        "size": size,
        "total_pages": (total_count // size) + (1 if total_count % size > 0 else 0),
        "results": feeds,
    }


# Get a single pricing feed
@app.get("/api/pricing_feeds/{feed_id}", response_model=PricingFeedResponse)
def get_pricing_feed(feed_id: int, db: Session = Depends(get_db)):
    feed = db.query(PricingFeed).filter(PricingFeed.id == feed_id).first()
    if not feed:
        raise HTTPException(status_code=404, detail="Pricing feed not found")
    return feed


# Update a pricing feed
@app.put("/api/pricing_feeds/{feed_id}", response_model=PricingFeedResponse)
def update_pricing_feed(
        feed_id: int, feed: PricingFeedUpdate, db: Session = Depends(get_db)
):
    db_feed = db.query(PricingFeed).filter(PricingFeed.id == feed_id).first()
    if not db_feed:
        raise HTTPException(status_code=404, detail="Pricing feed not found")
    for key, value in feed.dict(exclude_unset=True).items():
        setattr(db_feed, key, value)
    db.commit()
    db.refresh(db_feed)
    return db_feed


# Delete a pricing feed
@app.delete("/api/pricing_feeds/{feed_id}")
def delete_pricing_feed(feed_id: int, db: Session = Depends(get_db)):
    db_feed = db.query(PricingFeed).filter(PricingFeed.id == feed_id).first()
    if not db_feed:
        raise HTTPException(status_code=404, detail="Pricing feed not found")
    db.delete(db_feed)
    db.commit()
    return {"message": "Pricing feed deleted successfully"}
