from . import login
from . import register
from . import profile
from . import logout
from . import token_refresh
from . import movies
from . import genres
from . import showtimes
from . import reservations

from fastapi import APIRouter
import sys
import os

# Permite importar desde carpetas superiores
sys.path.append(os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../")))

router = APIRouter()

# Rutas Auth
router.include_router(register.router, tags=["Auth"])
router.include_router(login.router, tags=["Auth"])
router.include_router(logout.router, tags=["Auth"])
router.include_router(token_refresh.router, tags=["Auth"])

# Rutas de perfil de usuario
router.include_router(profile.router, tags=["User"])
router.include_router(movies.router)
router.include_router(genres.router)
router.include_router(showtimes.router)
router.include_router(reservations.router)
