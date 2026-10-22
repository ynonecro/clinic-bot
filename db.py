from datetime import datetime, timedelta, timezone
from sqlalchemy import (
    create_engine, BigInteger, String, ForeignKey, DateTime,
    UniqueConstraint, select,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass



class Doctor(Base):
    __tablename__ = "doctors"
    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200))
    specialization: Mapped[str] = mapped_column(String(100))


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        UniqueConstraint("doctor_id", "slot", name="uq_doctor_slot"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id"))
    slot: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def init_db():
    Base.metadata.create_all(engine)


def get_doctors():
    with Session() as s:
        return list(s.scalars(select(Doctor)).all())


def free_slots(doctor_id):
    now = datetime.now(timezone.utc)
    with Session() as s:
        taken = {row[0] for row in s.execute(
            select(Appointment.slot).where(
                Appointment.doctor_id == doctor_id,
                Appointment.slot >= now,
            )
        ).all()}

    result = []
    for d in range(7):
        day = (now + timedelta(days=d)).date()
        t = datetime(day.year, day.month, day.day, 9, tzinfo=timezone.utc)
        end = t.replace(hour=17)
        while t < end:
            if t > now and t not in taken:
                result.append(t)
            t += timedelta(minutes=30)
    return result


def book(doctor_id, user_id, slot):
    with Session() as s:
        s.add(Appointment(doctor_id=doctor_id, user_id=user_id, slot=slot))
        try:
            s.commit()
            return True
        except Exception:
            s.rollback()
            return False