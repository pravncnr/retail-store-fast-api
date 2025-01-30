from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Float, Date, create_engine
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import date, datetime

Base = declarative_base()
# DATABASE_URL = "postgresql://postgres:root@localhost/pricing_db"
DATABASE_URL = "postgresql://postgres:root@localhost/pricing_db_2"

class PricingFeed(Base):
    __tablename__ = "pricing_feeds"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(String, index=True)
    sku = Column(String, index=True)
    product_name = Column(String)
    price = Column(Float)
    date = Column(Date)

    class Config:
        json_encoders = {
            date: lambda dt: dt.isoformat()  # Convert date to ISO 8601 string (e.g., '2024-07-05')
        }


# Pydantic models for request and response
class PricingFeedCreate(BaseModel):
    store_id: str
    sku: str
    product_name: str
    price: float
    date: str

    @field_validator("date")
    def validate_date(cls, value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")

    class Config:
        json_encoders = {
            date: lambda dt: dt.isoformat()  # Convert date to ISO 8601 string (e.g., '2024-07-05')
        }


class UpdateRequest(BaseModel):
    id: int  # ID of the record to be updated
    store_id: Optional[str] = None
    sku: Optional[str] = None
    product_name: Optional[str] = None
    price: Optional[float] = None
    date: Optional[str] = None

    @field_validator("date")
    def validate_date(cls, value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")

    class Config:
        json_encoders = {
            date: lambda dt: dt.isoformat()  # Convert date to ISO 8601 string (e.g., '2024-07-05')
        }

class SearchRequest(BaseModel):
    store_id: Optional[str] = None
    search_sku: Optional[str] = None
    search_product_name: Optional[str] = None
    search_price_from: Optional[float] = None
    search_price_to: Optional[float] = None
    search_date_from: Optional[str] = None
    search_date_to: Optional[str] = None

    @field_validator("search_date_from")
    def validate_date(cls, value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")

    @field_validator("search_date_to")
    def validate_date(cls, value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")

    class Config:
        json_encoders = {
            date: lambda dt: dt.isoformat()  # Convert date to ISO 8601 string (e.g., '2024-07-05')
        }

class PricingFeedUpdate(BaseModel):
    store_id: Optional[str]
    sku: Optional[str]
    product_name: Optional[str]
    price: Optional[float]
    date: Optional[str]

    @field_validator("date")
    def validate_date(cls, value):
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")

    class Config:
        json_encoders = {
            date: lambda dt: dt.isoformat()  # Convert date to ISO 8601 string (e.g., '2024-07-05')
        }


class PricingFeedResponse(BaseModel):
    id: int
    store_id: str
    sku: str
    product_name: str
    price: float
    date: date

    class Config:
        json_encoders = {
            date: lambda dt: dt.isoformat()  # Convert date to ISO 8601 string (e.g., '2024-07-05')
        }

    @field_validator("date")
    def validate_date(cls, value):
        try:
            datetime.strftime(value, "%Y-%m-%d")
            return value
        except ValueError:
            raise ValueError("Invalid date format. Expected YYYY-MM-DD")


class PaginatedPricingFeedResponse(BaseModel):
    total_count: int
    page: int
    size: int
    total_pages: int
    results: List[PricingFeedResponse]


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
