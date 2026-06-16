from typing import List
from pydantic import BaseModel, Field

class BehaviorClass(BaseModel):
    name: str = Field(..., description="The name of the behavior class.")
    observable_indicator: str = Field(..., description="Visual indicator for detection.")

class BehaviorPair(BaseModel):
    domain: str = Field(..., description="The operational domain.")
    safe_behavior: BehaviorClass
    unsafe_behavior: BehaviorClass
    severity_signal: str = Field(..., description="Severity context string extracted from policy.")

class PolicySchema(BaseModel):
    behavior_pairs: List[BehaviorPair]
