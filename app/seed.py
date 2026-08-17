"""Crea el usuario administrador inicial.

Uso:
    python -m app.seed

Cambia la contraseña por defecto de inmediato una vez que inicies sesión.
"""
from app import models, security
from app.database import Base, SessionLocal, engine

ADMIN_EMAIL = "admin@justiciaorienta.local"
ADMIN_PASSWORD_INICIAL = "CambiarAhora2026"


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existe = db.query(models.Usuario).filter(models.Usuario.email == ADMIN_EMAIL).first()
        if existe:
            print(f"El usuario administrador ya existe: {ADMIN_EMAIL}")
            return

        admin = models.Usuario(
            nombre="Administrador Justicia Orienta",
            email=ADMIN_EMAIL,
            password_hash=security.hash_password(ADMIN_PASSWORD_INICIAL),
            rol="admin",
            activo=True,
        )
        db.add(admin)
        db.commit()
        print("Usuario administrador creado:")
        print(f"  correo:     {ADMIN_EMAIL}")
        print(f"  contraseña: {ADMIN_PASSWORD_INICIAL}  (cámbiala apenas inicies sesión)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
