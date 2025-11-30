from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# -------------------------
# Daily Record
# -------------------------
class DailyRecordIn(BaseModel):
    id: Optional[str] = None
    recordId: Optional[str] = None
    farmerId: Optional[int] = None
    batchId: Optional[str] = None
    unitId: Optional[str] = None
    date: Optional[datetime] = None
    feedName: Optional[str] = None
    feedSize: Optional[str] = None
    feedQuantity: Optional[float] = None
    mortality: Optional[int] = None
    coins: Optional[int] = None
    isSynced: Optional[int] = 0
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


# -------------------------
# Weight Sampling
# -------------------------
class WeightSamplingIn(BaseModel):
    id: Optional[str] = None
    recordId: Optional[str] = None
    farmerId: Optional[int] = None
    batchId: Optional[str] = None
    unitId: Optional[str] = None
    sampleName: Optional[str] = None
    date: Optional[datetime] = None
    fishNumbers: Optional[int] = None
    totalWeight: Optional[float] = None
    completed: Optional[int] = None
    isSynced: Optional[int] = 0
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


# -------------------------
# Grade
# -------------------------
class GradeIn(BaseModel):
    id: Optional[str] = None
    sortingId: Optional[str] = None
    destinationBatchId: Optional[str] = None
    destinationBatchName: Optional[str] = None
    destinationUnitId: Optional[str] = None
    destinationUnitName: Optional[str] = None
    averageFishWeight: Optional[float] = None
    fishTransferred: Optional[int] = None
    sampleName: Optional[str] = None
    recordId: Optional[str] = None
    batchId: Optional[str] = None
    isSynced: Optional[int] = 0
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


# -------------------------
# Grading & Sorting
# -------------------------
class GradingAndSortingIn(BaseModel):
    id: Optional[str] = None
    recordId: Optional[str] = None
    farmerId: Optional[int] = None
    batchId: Optional[str] = None
    unitId: Optional[str] = None
    gradeWith: Optional[str] = None
    sampleName: Optional[str] = None
    date: Optional[datetime] = None
    gradingPondNumber: Optional[str] = None
    fishNumbers: Optional[int] = None
    totalWeight: Optional[float] = None
    completed: Optional[int] = None
    isSynced: Optional[int] = 0
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    grades: List[GradeIn] = Field(default_factory=list)


# -------------------------
# Harvest
# -------------------------
class HarvestIn(BaseModel):
    id: Optional[str] = None
    recordId: Optional[str] = None
    farmerId: Optional[int] = None
    batchId: Optional[str] = None
    unitId: Optional[str] = None
    date: Optional[datetime] = None
    salesInvoiceNumber: Optional[str] = None
    quantityHarvest: Optional[int] = None
    totalWeight: Optional[float] = None
    pricePerKg: Optional[float] = None
    totalSales: Optional[float] = None
    isSynced: Optional[int] = 0
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


# -------------------------
# Unit (full unit details from mobile)
# -------------------------
class UnitIn(BaseModel):
    id: Optional[str] = None
    farmerId: Optional[int] = None
    unitName: Optional[str] = None
    unitType: Optional[str] = None
    unitDimension: Optional[str] = None
    unitCapacity: Optional[int] = None
    fishes: Optional[int] = None
    imageFile: Optional[str] = None
    imageUrl: Optional[str] = None
    unitcategory: Optional[str] = None
    isActive: Optional[int] = 0
    isSynced: Optional[int] = 0
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


# -------------------------
# Unit Record
# -------------------------
class UnitRecordIn(BaseModel):
    id: Optional[str] = None
    farmerId: Optional[int] = None  # <- make optional
    # farmerId: Optional[int] = None
    batchId: Optional[str] = None
    unitId: Optional[str] = None
    stocknumber: Optional[int] = None
    movedfishes: Optional[int] = None
    mortality: Optional[int] = None
    fishleft: Optional[int] = None
    incomingfish: Optional[int] = None
    fishtype: Optional[str] = None
    stockedon: Optional[datetime] = None
    totalfishcost: Optional[float] = None
    isSynced: Optional[int] = 0
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    unit: Optional[UnitIn] = None
    dailyRecords: List[DailyRecordIn] = Field(default_factory=list)
    weightSamplings: List[WeightSamplingIn] = Field(default_factory=list)
    gradingAndSortings: List[GradingAndSortingIn] = Field(default_factory=list)
    harvests: List[HarvestIn] = Field(default_factory=list)


# -------------------------
# Batch
# -------------------------
class BatchIn(BaseModel):
    batchId: Optional[str] = None
    # farmerId: int
    farmerId: Optional[int] = None  # <- make optional
    batchName: Optional[str] = None
    fishtype: Optional[str] = None
    numberoffishes: Optional[int] = None
    averagebodyweight: Optional[float] = None
    ageAtStock: Optional[int] = None
    isCompleted: Optional[int] = 0
    isSynced: Optional[int] = 0
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    records: List[UnitRecordIn] = Field(default_factory=list)
