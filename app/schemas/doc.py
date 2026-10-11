from pydantic import BaseModel
from sqlalchemy import date

class request_doc(BaseModel):
  invoice_id:str
  cust_name:str
  cust_email:str
  invoice_date:date
  currency: str
  total_amount: float
  summary: str