from .users import router as users_router
from .user_role import router as usersrole_router
from .company import router as company_router
from .currecny import router as currency_router
from .finyr import router as finyr_router
from .uom import router as uom_router
from .taxmaster import router as taxmaster_router
from .product import router as product_router

all_routers = [users_router, usersrole_router, company_router,currency_router,finyr_router,uom_router,taxmaster_router,product_router]
