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
def upsert_batch(payload: BatchIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Create or update a batch with nested unit records and all children.
    Farmer is always the authenticated user.
    """
    # Validate current user
    db_user = db.query(User).filter(User.id == user.id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    batch_id = payload.batchId or str(uuid4())

    # --- UPSERT Batch ---
    batch = db.query(Batch).filter(Batch.batch_id == batch_id).first()
    if batch:
        # update existing
        batch.batch_name = payload.batchName
        batch.fishtype = payload.fishtype
        batch.number_of_fishes = payload.numberoffishes
        batch.average_body_weight = payload.averagebodyweight
        batch.age_at_stock = payload.ageAtStock
        batch.is_completed = payload.isCompleted or 0
        batch.is_synced = payload.isSynced or 0
        batch.updated_at = payload.updatedAt or datetime.utcnow()
    else:
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
    db.flush()  # Ensure batch.id is available

    # --- UPSERT Units and UnitRecords ---
    for r in payload.records or []:
        # Unit UPSERT
        unit = db.query(Unit).filter(Unit.id == r.unitId).first()
        if not unit and r.unit:
            u = r.unit
            unit = Unit(
                id=u.id,
                farmer_id=user.id,
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
        elif not unit:
            raise HTTPException(status_code=400, detail=f"Unit {r.unitId} not found and unit payload not provided")

        # UnitRecord UPSERT
        rec = db.query(UnitRecord).filter(UnitRecord.id == r.id).first()
        if rec:
            # update
            rec.stocknumber = r.stocknumber
            rec.movedfishes = r.movedfishes
            rec.mortality = r.mortality
            rec.fishleft = r.fishleft
            rec.incomingfish = r.incomingfish
            rec.fishtype = r.fishtype
            rec.stockedon = r.stockedon
            rec.totalfishcost = r.totalfishcost
            rec.is_synced = r.isSynced or 0
            rec.updated_at = r.updatedAt or datetime.utcnow()
        else:
            rec = UnitRecord(
                id=r.id or str(uuid4()),
                farmer_id=user.id,
                batch_id=batch.id,
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

        # --- DailyRecords UPSERT ---
        for d in r.dailyRecords or []:
            dr = db.query(DailyRecord).filter(DailyRecord.id == d.id).first()
            if dr:
                dr.date = d.date
                dr.feed_name = d.feedName
                dr.feed_size = d.feedSize
                dr.feed_quantity = d.feedQuantity
                dr.mortality = d.mortality
                dr.coins = d.coins
                dr.is_synced = d.isSynced or 0
                dr.updated_at = d.updatedAt or datetime.utcnow()
            else:
                dr = DailyRecord(
                    id=d.id or str(uuid4()),
                    record_id=rec.id,
                    farmer_id=user.id,
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

        # --- WeightSamplings UPSERT ---
        for w in r.weightSamplings or []:
            ws = db.query(WeightSampling).filter(WeightSampling.id == w.id).first()
            if ws:
                ws.fish_numbers = w.fishNumbers
                ws.total_weight = w.totalWeight
                ws.completed = w.completed
                ws.is_synced = w.isSynced or 0
                ws.updated_at = w.updatedAt or datetime.utcnow()
            else:
                ws = WeightSampling(
                    id=w.id or str(uuid4()),
                    record_id=rec.id,
                    farmer_id=user.id,
                    batch_id=batch.id,
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

        # --- Grading & Sortings UPSERT ---
        for g in r.gradingAndSortings or []:
            grading = db.query(GradingAndSorting).filter(GradingAndSorting.id == g.id).first()
            if grading:
                grading.fish_numbers = g.fishNumbers
                grading.total_weight = g.totalWeight
                grading.completed = g.completed
                grading.is_synced = g.isSynced or 0
                grading.updated_at = g.updatedAt or datetime.utcnow()
            else:
                grading = GradingAndSorting(
                    id=g.id or str(uuid4()),
                    record_id=rec.id,
                    farmer_id=user.id,
                    batch_id=batch.id,
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

            # Grades
            for gr in g.grades or []:
                grade = db.query(Grade).filter(Grade.id == gr.id).first()
                if grade:
                    grade.average_fish_weight = gr.averageFishWeight
                    grade.fish_transferred = gr.fishTransferred
                    grade.is_synced = gr.isSynced or 0
                    grade.updated_at = gr.updatedAt or datetime.utcnow()
                else:
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
                        is_synced=gr.isSynced or 0,
                        created_at=gr.createdAt or datetime.utcnow(),
                        updated_at=gr.updatedAt or datetime.utcnow(),
                    )
                    db.add(grade)

        # --- Harvests UPSERT ---
        for h in r.harvests or []:
            hv = db.query(HarvestForm).filter(HarvestForm.id == h.id).first()
            if hv:
                hv.quantity_harvest = h.quantityHarvest
                hv.total_weight = h.totalWeight
                hv.price_per_kg = h.pricePerKg
                hv.total_sales = h.totalSales
                hv.is_synced = h.isSynced or 0
                hv.updated_at = h.updatedAt or datetime.utcnow()
            else:
                hv = HarvestForm(
                    id=h.id or str(uuid4()),
                    record_id=rec.id,
                    farmer_id=user.id,
                    batch_id=batch.id,
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

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving batch: {str(e)}")

    return {"detail": "Batch created/updated", "batchId": batch.batch_id}



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
# def create_batch(
#     payload: BatchIn,
#     db: Session = Depends(get_db),
#     user: User = Depends(get_current_user)
# ):
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
#                 u = r.unit  # UnitIn instance
#                 unit = Unit(
#                     id=u.id,
#                     farmer_id=u.farmerId or user.id,
#                     unit_name=u.unitName or "unknown",
#                     unit_type=u.unitType,
#                     unit_dimension=u.unitDimension,
#                     unit_capacity=u.unitCapacity,
#                     fishes=u.fishes,
#                     image_file=u.imageFile,
#                     image_url=u.imageUrl,
#                     unitcategory=getattr(u, "unitcategory", None),
#                     is_active=u.isActive or 0,
#                     is_synced=u.isSynced or 0,
#                     created_at=u.createdAt or datetime.utcnow(),
#                     updated_at=u.updatedAt or datetime.utcnow(),
#                 )
#                 db.add(unit)
#                 db.flush()
#             else:
#                 raise HTTPException(status_code=400, detail=f"Unit {r.unitId} not found and unit payload not provided")
#
#         # UnitRecord
#         # rec = UnitRecord(
#         #     id=r.id or str(uuid4()),
#         #     farmer_id=user.id,
#         #     batch_id=batch.batch_id,
#         #     unit_id=r.unitId,
#         #     stocknumber=r.stocknumber,
#         #     movedfishes=r.movedfishes,
#         #     mortality=r.mortality,
#         #     fishleft=r.fishleft,
#         #     incomingfish=r.incomingfish,
#         #     fishtype=r.fishtype,
#         #     stockedon=r.stockedon,
#         #     totalfishcost=r.totalfishcost,
#         #     is_synced=r.isSynced or 0,
#         #     created_at=r.createdAt or datetime.utcnow(),
#         #     updated_at=r.updatedAt or datetime.utcnow(),
#         # )
#         rec = UnitRecord(
#             id=r.id or str(uuid4()),
#             farmer_id=user.id,
#             batch_id=batch.id,  # <-- must be the PK that matches unit_records FK
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
#
#         db.add(rec)
#         db.flush()
#
#         # DailyRecords
#         for d in r.dailyRecords or []:
#             dr = DailyRecord(
#                 id=d.id or str(uuid4()),
#                 record_id=rec.id,
#                 farmer_id=user.id,
#                 # batch_id=
#                 # ,
#                 batch_id=batch.id,
#
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
#                 batch_id=batch.id,
#
#                 # batch_id=batch.batch_id,
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
#                 batch_id=batch.id,
#
#                 # batch_id=batch.batch_id,
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
#                     batch_id=batch.id,
#
#                     # batch_id=batch.batch_id,
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
#                 batch_id=batch.id,
#
#                 # batch_id=batch.batch_id,
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
#
#
# # from fastapi import APIRouter, Depends, HTTPException
# # from sqlalchemy.orm import Session
# # from uuid import uuid4
# # from datetime import datetime
# # from typing import List
# #
# # from ..database import get_db
# # from syncsehemas import BatchIn
# # from ..models import (
# #     User, Batch, Unit, UnitRecord, DailyRecord,
# #     WeightSampling, HarvestForm, Grade, GradingAndSorting
# # )
# # from ..dep.security import get_current_user
# #
# # router = APIRouter(prefix="/batches", tags=["Batch"])
# #
# #
# # @router.post("/", status_code=201)
# # def create_batch(payload: BatchIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
# #     """
# #     Create a batch with nested unit records and all children.
# #     Farmer is always the authenticated user.
# #     """
# #     # Validate current user
# #     db_user = db.query(User).filter(User.id == user.id).first()
# #     if not db_user:
# #         raise HTTPException(status_code=404, detail="User not found")
# #
# #     # Auto-generate batchId if not provided
# #     batch_id = payload.batchId or str(uuid4())
# #
# #     # Create Batch
# #     batch = Batch(
# #         batch_id=batch_id,
# #         farmer_id=user.id,
# #         batch_name=payload.batchName,
# #         fishtype=payload.fishtype,
# #         number_of_fishes=payload.numberoffishes,
# #         average_body_weight=payload.averagebodyweight,
# #         age_at_stock=payload.ageAtStock,
# #         is_completed=payload.isCompleted or 0,
# #         is_synced=payload.isSynced or 0,
# #         created_at=payload.createdAt or datetime.utcnow(),
# #         updated_at=payload.updatedAt or datetime.utcnow(),
# #     )
# #     db.add(batch)
# #     db.flush()  # Ensure batch_id is available
# #
# #     # Insert UnitRecords and nested children
# #     for r in payload.records or []:
# #         # Ensure Unit exists
# #         unit = db.query(Unit).filter(Unit.id == r.unitId).first()
# #         if not unit:
# #             if r.unit:
# #                 unit = Unit(
# #                     id=r.unit.get("id"),
# #                     farmer_id=r.unit.get("farmerId", user.id),
# #                     unit_name=r.unit.get("unitName", "unknown"),
# #                     unit_type=r.unit.get("unitType"),
# #                     unit_dimension=r.unit.get("unitDimension"),
# #                     unit_capacity=r.unit.get("unitCapacity"),
# #                     fishes=r.unit.get("fishes"),
# #                     image_file=r.unit.get("imageFile"),
# #                     image_url=r.unit.get("imageUrl"),
# #                     unitcategory=r.unit.get("unitcategory"),
# #                     is_active=r.unit.get("isActive", 0),
# #                     is_synced=r.unit.get("isSynced", 0),
# #                     created_at=r.unit.get("createdAt", datetime.utcnow()),
# #                     updated_at=r.unit.get("updatedAt", datetime.utcnow()),
# #                 )
# #                 db.add(unit)
# #                 db.flush()
# #             else:
# #                 raise HTTPException(status_code=400, detail=f"Unit {r.unitId} not found and unit payload not provided")
# #
# #         # UnitRecord
# #         rec = UnitRecord(
# #             id=r.id or str(uuid4()),
# #             farmer_id=user.id,
# #             batch_id=batch.batch_id,
# #             unit_id=r.unitId,
# #             stocknumber=r.stocknumber,
# #             movedfishes=r.movedfishes,
# #             mortality=r.mortality,
# #             fishleft=r.fishleft,
# #             incomingfish=r.incomingfish,
# #             fishtype=r.fishtype,
# #             stockedon=r.stockedon,
# #             totalfishcost=r.totalfishcost,
# #             is_synced=r.isSynced or 0,
# #             created_at=r.createdAt or datetime.utcnow(),
# #             updated_at=r.updatedAt or datetime.utcnow(),
# #         )
# #         db.add(rec)
# #         db.flush()
# #
# #         # DailyRecords
# #         for d in r.dailyRecords or []:
# #             dr = DailyRecord(
# #                 id=d.id or str(uuid4()),
# #                 record_id=rec.id,
# #                 farmer_id=user.id,
# #                 batch_id=batch.batch_id,
# #                 unit_id=d.unitId,
# #                 date=d.date,
# #                 feed_name=d.feedName,
# #                 feed_size=d.feedSize,
# #                 feed_quantity=d.feedQuantity,
# #                 mortality=d.mortality,
# #                 coins=d.coins,
# #                 is_synced=d.isSynced or 0,
# #                 created_at=d.createdAt or datetime.utcnow(),
# #                 updated_at=d.updatedAt or datetime.utcnow(),
# #             )
# #             db.add(dr)
# #
# #         # WeightSamplings
# #         for w in r.weightSamplings or []:
# #             ws = WeightSampling(
# #                 id=w.id or str(uuid4()),
# #                 record_id=rec.id,
# #                 farmer_id=user.id,
# #                 batch_id=batch.batch_id,
# #                 unit_id=w.unitId,
# #                 sample_name=w.sampleName,
# #                 date=w.date,
# #                 fish_numbers=w.fishNumbers,
# #                 total_weight=w.totalWeight,
# #                 completed=w.completed,
# #                 is_synced=w.isSynced or 0,
# #                 created_at=w.createdAt or datetime.utcnow(),
# #                 updated_at=w.updatedAt or datetime.utcnow(),
# #             )
# #             db.add(ws)
# #
# #         # Grading & Sortings + Grades
# #         for g in r.gradingAndSortings or []:
# #             grading = GradingAndSorting(
# #                 id=g.id or str(uuid4()),
# #                 record_id=rec.id,
# #                 farmer_id=user.id,
# #                 batch_id=batch.batch_id,
# #                 unit_id=g.unitId,
# #                 grade_with=g.gradeWith,
# #                 sample_name=g.sampleName,
# #                 date=g.date,
# #                 grading_pond_number=g.gradingPondNumber,
# #                 fish_numbers=g.fishNumbers,
# #                 total_weight=g.totalWeight,
# #                 completed=g.completed,
# #                 is_synced=g.isSynced or 0,
# #                 created_at=g.createdAt or datetime.utcnow(),
# #                 updated_at=g.updatedAt or datetime.utcnow(),
# #             )
# #             db.add(grading)
# #             db.flush()
# #
# #             for gr in g.grades or []:
# #                 grade = Grade(
# #                     id=gr.id or str(uuid4()),
# #                     sorting_id=grading.id,
# #                     destination_batch_id=gr.destinationBatchId,
# #                     destination_batch_name=gr.destinationBatchName,
# #                     destination_unit_id=gr.destinationUnitId,
# #                     destination_unit_name=gr.destinationUnitName,
# #                     average_fish_weight=gr.averageFishWeight,
# #                     fish_transferred=gr.fishTransferred,
# #                     sample_name=gr.sampleName,
# #                     record_id=rec.id,
# #                     batch_id=batch.batch_id,
# #                     is_synced=gr.isSynced or 0,
# #                     created_at=gr.createdAt or datetime.utcnow(),
# #                     updated_at=gr.updatedAt or datetime.utcnow(),
# #                 )
# #                 db.add(grade)
# #
# #         # Harvests
# #         for h in r.harvests or []:
# #             hv = HarvestForm(
# #                 id=h.id or str(uuid4()),
# #                 record_id=rec.id,
# #                 farmer_id=user.id,
# #                 batch_id=batch.batch_id,
# #                 unit_id=h.unitId,
# #                 date=h.date,
# #                 sales_invoice_number=h.salesInvoiceNumber,
# #                 quantity_harvest=h.quantityHarvest,
# #                 total_weight=h.totalWeight,
# #                 price_per_kg=h.pricePerKg,
# #                 total_sales=h.totalSales,
# #                 is_synced=h.isSynced or 0,
# #                 created_at=h.createdAt or datetime.utcnow(),
# #                 updated_at=h.updatedAt or datetime.utcnow(),
# #             )
# #             db.add(hv)
# #
# #     # Commit once
# #     try:
# #         db.commit()
# #     except Exception as e:
# #         db.rollback()
# #         raise HTTPException(status_code=500, detail=f"Error saving batch: {str(e)}")
# #
# #     return {"detail": "Batch created", "batchId": batch.batch_id}
