from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id
from app.models.school_setting import SchoolSetting
from app.schemas.school_setting import SettingUpdate, SettingOut

router = APIRouter(prefix="/school-settings", tags=["Settings"])

# Secret fields: an empty string clears them, a non-empty value overwrites, unset keeps.
SECRET_FIELDS = ("razorpay_key_secret", "sms_api_key", "whatsapp_api_key")


def _out(s: SchoolSetting) -> SettingOut:
    return SettingOut(
        school_id=s.school_id, currency=s.currency, timezone=s.timezone,
        academic_year=s.academic_year, razorpay_key_id=s.razorpay_key_id,
        razorpay_secret_set=bool(s.razorpay_key_secret),
        sms_key_set=bool(s.sms_api_key),
        whatsapp_key_set=bool(s.whatsapp_api_key),
        session_timeout_minutes=s.session_timeout_minutes,
        password_min_length=s.password_min_length,
    )


async def _get_or_create(db: AsyncSession, school_id: str) -> SchoolSetting:
    s = (
        await db.execute(select(SchoolSetting).where(SchoolSetting.school_id == school_id))
    ).scalar_one_or_none()
    if not s:
        s = SchoolSetting(school_id=school_id)
        db.add(s)
        await db.flush()
    return s


@router.get("", response_model=SettingOut)
async def get_settings(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    return _out(await _get_or_create(db, str(school_id)))


@router.patch("", response_model=SettingOut)
async def update_settings(
    body: SettingUpdate,
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    s = await _get_or_create(db, str(school_id))
    for field, value in body.model_dump(exclude_unset=True).items():
        if field in SECRET_FIELDS and value == "":
            setattr(s, field, None)   # explicit clear
        else:
            setattr(s, field, value)
    await db.flush()
    return _out(s)
