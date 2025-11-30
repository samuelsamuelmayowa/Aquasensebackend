from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
from typing import List

from ..database import get_db
from syncsehemas import BatchIn
from ..models import (
    User, Batch, Unit, UnitRecord, DailyRecord,
    WeightSampling, HarvestForm, Grade, GradingAndSorting
)
from ..dep.security import get_current_user

router = APIRouter(prefix="/batches", tags=["Batch"])


@router.post("/", status_code=201)
def create_batch(
    payload: BatchIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Create a batch with nested unit records and all children.
    Farmer is always the authenticated user.
    """
    # Validate current user
    db_user = db.query(User).filter(User.id == user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Auto-generate batchId if not provided
    batch_id = payload.batchId or str(uuid4())

    # Create Batch
    batch = Batch(
        batch_id=batch_id,
        farmer_id=user.id,
        batch_name=payload.batchName,
        fishtype=payload.fishtype,
        number_of_fishes=payload.numberoffishes,
        average_body_weight=payload.averagebodyweight,
        age_at_stock=payload.ageAtStock,
        is_completed=payload.isCompleted or 0,
        is_synced=payload.isSynced or 0,
        created_at=payload.createdAt or datetime.utcnow(),
        updated_at=payload.updatedAt or datetime.utcnow(),
    )
    db.add(batch)
    db.flush()  # Ensure batch_id is available

    # Insert UnitRecords and nested children
    for r in payload.records or []:
        # Ensure Unit exists
        unit = db.query(Unit).filter(Unit.id == r.unitId).first()
        if not unit:
            if r.unit:
                u = r.unit  # UnitIn instance
                unit = Unit(
                    id=u.id,
                    farmer_id=u.farmerId or user.id,
                    unit_name=u.unitName or "unknown",
                    unit_type=u.unitType,
                    unit_dimension=u.unitDimension,
                    unit_capacity=u.unitCapacity,
                    fishes=u.fishes,
                    image_file=u.imageFile,
                    image_url=u.imageUrl,
                    unitcategory=getattr(u, "unitcategory", None),
                    is_active=u.isActive or 0,
                    is_synced=u.isSynced or 0,
                    created_at=u.createdAt or datetime.utcnow(),
                    updated_at=u.updatedAt or datetime.utcnow(),
                )
                db.add(unit)
                db.flush()
            else:
                raise HTTPException(status_code=400, detail=f"Unit {r.unitId} not found and unit payload not provided")

        # UnitRecord
        # rec = UnitRecord(
        #     id=r.id or str(uuid4()),
        #     farmer_id=user.id,
        #     batch_id=batch.batch_id,
        #     unit_id=r.unitId,
        #     stocknumber=r.stocknumber,
        #     movedfishes=r.movedfishes,
        #     mortality=r.mortality,
        #     fishleft=r.fishleft,
        #     incomingfish=r.incomingfish,
        #     fishtype=r.fishtype,
        #     stockedon=r.stockedon,
        #     totalfishcost=r.totalfishcost,
        #     is_synced=r.isSynced or 0,
        #     created_at=r.createdAt or datetime.utcnow(),
        #     updated_at=r.updatedAt or datetime.utcnow(),
        # )
        rec = UnitRecord(
            id=r.id or str(uuid4()),
            farmer_id=user.id,
            batch_id=batch.id,  # <-- must be the PK that matches unit_records FK
            unit_id=r.unitId,
            stocknumber=r.stocknumber,
            movedfishes=r.movedfishes,
            mortality=r.mortality,
            fishleft=r.fishleft,
            incomingfish=r.incomingfish,
            fishtype=r.fishtype,
            stockedon=r.stockedon,
            totalfishcost=r.totalfishcost,
            is_synced=r.isSynced or 0,
            created_at=r.createdAt or datetime.utcnow(),
            updated_at=r.updatedAt or datetime.utcnow(),
        )

        db.add(rec)
        db.flush()

        # DailyRecords
        for d in r.dailyRecords or []:
            dr = DailyRecord(
                id=d.id or str(uuid4()),
                record_id=rec.id,
                farmer_id=user.id,
                # batch_id=
                # ,
                batch_id=batch.id,

                unit_id=d.unitId,
                date=d.date,
                feed_name=d.feedName,
                feed_size=d.feedSize,
                feed_quantity=d.feedQuantity,
                mortality=d.mortality,
                coins=d.coins,
                is_synced=d.isSynced or 0,
                created_at=d.createdAt or datetime.utcnow(),
                updated_at=d.updatedAt or datetime.utcnow(),
            )
            db.add(dr)

        # WeightSamplings
        for w in r.weightSamplings or []:
            ws = WeightSampling(
                id=w.id or str(uuid4()),
                record_id=rec.id,
                farmer_id=user.id,
                batch_id=batch.id,

                # batch_id=batch.batch_id,
                unit_id=w.unitId,
                sample_name=w.sampleName,
                date=w.date,
                fish_numbers=w.fishNumbers,
                total_weight=w.totalWeight,
                completed=w.completed,
                is_synced=w.isSynced or 0,
                created_at=w.createdAt or datetime.utcnow(),
                updated_at=w.updatedAt or datetime.utcnow(),
            )
            db.add(ws)

        # Grading & Sortings + Grades
        for g in r.gradingAndSortings or []:
            grading = GradingAndSorting(
                id=g.id or str(uuid4()),
                record_id=rec.id,
                farmer_id=user.id,
                batch_id=batch.id,

                # batch_id=batch.batch_id,
                unit_id=g.unitId,
                grade_with=g.gradeWith,
                sample_name=g.sampleName,
                date=g.date,
                grading_pond_number=g.gradingPondNumber,
                fish_numbers=g.fishNumbers,
                total_weight=g.totalWeight,
                completed=g.completed,
                is_synced=g.isSynced or 0,
                created_at=g.createdAt or datetime.utcnow(),
                updated_at=g.updatedAt or datetime.utcnow(),
            )
            db.add(grading)
            db.flush()

            for gr in g.grades or []:
                grade = Grade(
                    id=gr.id or str(uuid4()),
                    sorting_id=grading.id,
                    destination_batch_id=gr.destinationBatchId,
                    destination_batch_name=gr.destinationBatchName,
                    destination_unit_id=gr.destinationUnitId,
                    destination_unit_name=gr.destinationUnitName,
                    average_fish_weight=gr.averageFishWeight,
                    fish_transferred=gr.fishTransferred,
                    sample_name=gr.sampleName,
                    record_id=rec.id,
                    batch_id=batch.id,

                    # batch_id=batch.batch_id,
                    is_synced=gr.isSynced or 0,
                    created_at=gr.createdAt or datetime.utcnow(),
                    updated_at=gr.updatedAt or datetime.utcnow(),
                )
                db.add(grade)

        # Harvests
        for h in r.harvests or []:
            hv = HarvestForm(
                id=h.id or str(uuid4()),
                record_id=rec.id,
                farmer_id=user.id,
                batch_id=batch.id,

                # batch_id=batch.batch_id,
                unit_id=h.unitId,
                date=h.date,
                sales_invoice_number=h.salesInvoiceNumber,
                quantity_harvest=h.quantityHarvest,
                total_weight=h.totalWeight,
                price_per_kg=h.pricePerKg,
                total_sales=h.totalSales,
                is_synced=h.isSynced or 0,
                created_at=h.createdAt or datetime.utcnow(),
                updated_at=h.updatedAt or datetime.utcnow(),
            )
            db.add(hv)

    # Commit once
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving batch: {str(e)}")

    return {"detail": "Batch created", "batchId": batch.batch_id}


# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from uuid import uuid4
# from datetime import datetime
# from typing import List
#
# from ..database import get_db
# from syncsehemas import BatchIn
# from ..models import (
#     User, Batch, Unit, UnitRecord, DailyRecord,
#     WeightSampling, HarvestForm, Grade, GradingAndSorting
# )
# from ..dep.security import get_current_user
#
# router = APIRouter(prefix="/batches", tags=["Batch"])
#
#
# @router.post("/", status_code=201)
# def create_batch(payload: BatchIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
#     """
#     Create a batch with nested unit records and all children.
#     Farmer is always the authenticated user.
#     """
#     # Validate current user
#     db_user = db.query(User).filter(User.id == user.id).first()
#     if not db_user:
#         raise HTTPException(status_code=404, detail="User not found")
#
#     # Auto-generate batchId if not provided
#     batch_id = payload.batchId or str(uuid4())
#
#     # Create Batch
#     batch = Batch(
#         batch_id=batch_id,
#         farmer_id=user.id,
#         batch_name=payload.batchName,
#         fishtype=payload.fishtype,
#         number_of_fishes=payload.numberoffishes,
#         average_body_weight=payload.averagebodyweight,
#         age_at_stock=payload.ageAtStock,
#         is_completed=payload.isCompleted or 0,
#         is_synced=payload.isSynced or 0,
#         created_at=payload.createdAt or datetime.utcnow(),
#         updated_at=payload.updatedAt or datetime.utcnow(),
#     )
#     db.add(batch)
#     db.flush()  # Ensure batch_id is available
#
#     # Insert UnitRecords and nested children
#     for r in payload.records or []:
#         # Ensure Unit exists
#         unit = db.query(Unit).filter(Unit.id == r.unitId).first()
#         if not unit:
#             if r.unit:
#                 unit = Unit(
#                     id=r.unit.get("id"),
#                     farmer_id=r.unit.get("farmerId", user.id),
#                     unit_name=r.unit.get("unitName", "unknown"),
#                     unit_type=r.unit.get("unitType"),
#                     unit_dimension=r.unit.get("unitDimension"),
#                     unit_capacity=r.unit.get("unitCapacity"),
#                     fishes=r.unit.get("fishes"),
#                     image_file=r.unit.get("imageFile"),
#                     image_url=r.unit.get("imageUrl"),
#                     unitcategory=r.unit.get("unitcategory"),
#                     is_active=r.unit.get("isActive", 0),
#                     is_synced=r.unit.get("isSynced", 0),
#                     created_at=r.unit.get("createdAt", datetime.utcnow()),
#                     updated_at=r.unit.get("updatedAt", datetime.utcnow()),
#                 )
#                 db.add(unit)
#                 db.flush()
#             else:
#                 raise HTTPException(status_code=400, detail=f"Unit {r.unitId} not found and unit payload not provided")
#
#         # UnitRecord
#         rec = UnitRecord(
#             id=r.id or str(uuid4()),
#             farmer_id=user.id,
#             batch_id=batch.batch_id,
#             unit_id=r.unitId,
#             stocknumber=r.stocknumber,
#             movedfishes=r.movedfishes,
#             mortality=r.mortality,
#             fishleft=r.fishleft,
#             incomingfish=r.incomingfish,
#             fishtype=r.fishtype,
#             stockedon=r.stockedon,
#             totalfishcost=r.totalfishcost,
#             is_synced=r.isSynced or 0,
#             created_at=r.createdAt or datetime.utcnow(),
#             updated_at=r.updatedAt or datetime.utcnow(),
#         )
#         db.add(rec)
#         db.flush()
#
#         # DailyRecords
#         for d in r.dailyRecords or []:
#             dr = DailyRecord(
#                 id=d.id or str(uuid4()),
#                 record_id=rec.id,
#                 farmer_id=user.id,
#                 batch_id=batch.batch_id,
#                 unit_id=d.unitId,
#                 date=d.date,
#                 feed_name=d.feedName,
#                 feed_size=d.feedSize,
#                 feed_quantity=d.feedQuantity,
#                 mortality=d.mortality,
#                 coins=d.coins,
#                 is_synced=d.isSynced or 0,
#                 created_at=d.createdAt or datetime.utcnow(),
#                 updated_at=d.updatedAt or datetime.utcnow(),
#             )
#             db.add(dr)
#
#         # WeightSamplings
#         for w in r.weightSamplings or []:
#             ws = WeightSampling(
#                 id=w.id or str(uuid4()),
#                 record_id=rec.id,
#                 farmer_id=user.id,
#                 batch_id=batch.batch_id,
#                 unit_id=w.unitId,
#                 sample_name=w.sampleName,
#                 date=w.date,
#                 fish_numbers=w.fishNumbers,
#                 total_weight=w.totalWeight,
#                 completed=w.completed,
#                 is_synced=w.isSynced or 0,
#                 created_at=w.createdAt or datetime.utcnow(),
#                 updated_at=w.updatedAt or datetime.utcnow(),
#             )
#             db.add(ws)
#
#         # Grading & Sortings + Grades
#         for g in r.gradingAndSortings or []:
#             grading = GradingAndSorting(
#                 id=g.id or str(uuid4()),
#                 record_id=rec.id,
#                 farmer_id=user.id,
#                 batch_id=batch.batch_id,
#                 unit_id=g.unitId,
#                 grade_with=g.gradeWith,
#                 sample_name=g.sampleName,
#                 date=g.date,
#                 grading_pond_number=g.gradingPondNumber,
#                 fish_numbers=g.fishNumbers,
#                 total_weight=g.totalWeight,
#                 completed=g.completed,
#                 is_synced=g.isSynced or 0,
#                 created_at=g.createdAt or datetime.utcnow(),
#                 updated_at=g.updatedAt or datetime.utcnow(),
#             )
#             db.add(grading)
#             db.flush()
#
#             for gr in g.grades or []:
#                 grade = Grade(
#                     id=gr.id or str(uuid4()),
#                     sorting_id=grading.id,
#                     destination_batch_id=gr.destinationBatchId,
#                     destination_batch_name=gr.destinationBatchName,
#                     destination_unit_id=gr.destinationUnitId,
#                     destination_unit_name=gr.destinationUnitName,
#                     average_fish_weight=gr.averageFishWeight,
#                     fish_transferred=gr.fishTransferred,
#                     sample_name=gr.sampleName,
#                     record_id=rec.id,
#                     batch_id=batch.batch_id,
#                     is_synced=gr.isSynced or 0,
#                     created_at=gr.createdAt or datetime.utcnow(),
#                     updated_at=gr.updatedAt or datetime.utcnow(),
#                 )
#                 db.add(grade)
#
#         # Harvests
#         for h in r.harvests or []:
#             hv = HarvestForm(
#                 id=h.id or str(uuid4()),
#                 record_id=rec.id,
#                 farmer_id=user.id,
#                 batch_id=batch.batch_id,
#                 unit_id=h.unitId,
#                 date=h.date,
#                 sales_invoice_number=h.salesInvoiceNumber,
#                 quantity_harvest=h.quantityHarvest,
#                 total_weight=h.totalWeight,
#                 price_per_kg=h.pricePerKg,
#                 total_sales=h.totalSales,
#                 is_synced=h.isSynced or 0,
#                 created_at=h.createdAt or datetime.utcnow(),
#                 updated_at=h.updatedAt or datetime.utcnow(),
#             )
#             db.add(hv)
#
#     # Commit once
#     try:
#         db.commit()
#     except Exception as e:
#         db.rollback()
#         raise HTTPException(status_code=500, detail=f"Error saving batch: {str(e)}")
#
#     return {"detail": "Batch created", "batchId": batch.batch_id}
