from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import date, datetime

class Subscriber(BaseModel):
    ric: str
    pin_code: str
    full_name: str
    phone_model: str
    phone_type: str
    service_type: str
    contract_start_date: date
    contract_duration_months: int
    monthly_fee: float
    is_active: bool = True
    last_payment_date: Optional[date] = None
    
    @computed_field
    def total_cost(self) -> float:
        return self.contract_duration_months * self.monthly_fee
    
class ServiceRequest(BaseModel):
    ric: str
    phone_model: str
    issue_description: str
    status: str = "open"
    created_at: datetime = Field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None

class DebtorReport(BaseModel):
    ric: str
    full_name: str
    debt_amount: float
    days_overdue: int