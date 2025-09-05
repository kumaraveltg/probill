from .users import router as users_router
from .user_role import router as usersrole_router
from .company import router as company_router
from .currecny import router as currency_router

all_routers = [users_router, usersrole_router, company_router,currency_router]
