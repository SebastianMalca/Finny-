# backend/models/__init__.py
# Exports the SQLAlchemy db instance and all models so imports stay clean.

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models so SQLAlchemy can discover them for create_all()
from backend.models.user        import User          # noqa: F401, E402
from backend.models.purchase    import Purchase      # noqa: F401, E402
from backend.models.budget      import Budget        # noqa: F401, E402
from backend.models.profile     import UserProfile   # noqa: F401, E402
from backend.models.streak      import Streak        # noqa: F401, E402
from backend.models.mission     import Mission       # noqa: F401, E402
from backend.models.achievement import Achievement   # noqa: F401, E402
