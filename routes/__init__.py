from .users import router as users_router
from .user_role import router as usersrole_router
from .company import router as company_router
from .currecny import router as currency_router
from .finyr import router as finyr_router
from .uom import router as uom_router
from .taxmaster import router as taxmaster_router
from .product import router as product_router
from .customer import router as customer_router
from .country import router as country_router
from .state import router as state_router
from .city import router as city_router
from .dbexcel import router as dbexcel_router
from .importdb import router as importdb_router

all_routers = [users_router, usersrole_router, company_router,currency_router,finyr_router,uom_router,taxmaster_router,product_router,customer_router,country_router,state_router,city_router,dbexcel_router,importdb_router]
