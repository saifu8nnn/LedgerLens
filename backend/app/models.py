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
    
   
    item_name = Column(String, unique=True, index=True)
    
   
    approved_quantity = Column(Integer)
    
    
    approved_price = Column(Float)