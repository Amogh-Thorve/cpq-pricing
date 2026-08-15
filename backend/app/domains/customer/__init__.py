from backend.app.domains.customer.routes import router
from backend.app.domains.customer.models import Customer, Contact, CustomerAddress

__all__ = ["router", "Customer", "Contact", "CustomerAddress"]
