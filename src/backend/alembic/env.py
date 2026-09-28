from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import get_settings  # noqa: E402
from app.core.database import Base  # noqa: E402
from app.models.bulto import Bulto  # noqa: F401, E402
from app.models.auditoria import Auditoria  # noqa: F401, E402
from app.models.hoja_ruta import HojaRuta  # noqa: F401, E402
from app.models.incidencia import Incidencia  # noqa: F401, E402
from app.models.pistoleo import Pistoleo  # noqa: F401, E402
from app.models.reasignacion import Reasignacion  # noqa: F401, E402
from app.models.rol import Rol  # noqa: F401, E402
from app.models.usuario import Usuario  # noqa: F401, E402

config = context.config
settings = get_settings()

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
