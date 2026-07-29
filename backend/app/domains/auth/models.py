import enum
from sqlalchemy import String, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base

class UserRole(str, enum.Enum):
    """
    Enterprise Roles supporting Role-Based Access Control (RBAC).
    """
    ADMIN = "admin"
    SALES_REP = "sales_rep"
    MANAGER = "manager"
    EXECUTIVE = "executive"

class User(Base):
    """
    User database model representing enterprise staff members.
    Responsible for storing authentication parameters and RBAC role assignments.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.SALES_REP, nullable=False)
