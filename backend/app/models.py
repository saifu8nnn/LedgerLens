from sqlalchemy import Column, Integer, String, Float
from .database import Base

class PurchaseOrder(Base):
    """
    This model represents the enterprise's internal database of approved 
    Purchase Orders (POs). In a real 3-Way Match scenario, the system 
    compares the external vendor's invoice against this internal truth.
    """
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    
    # The exact name of the item ordered (e.g., "Lenovo ThinkPad L14")
    item_name = Column(String, unique=True, index=True)
    
    # The maximum quantity the vendor is authorized to bill for
    approved_quantity = Column(Integer)
    
    # The contracted unit price negotiated with the vendor (in Rupees)
    approved_price = Column(Float)