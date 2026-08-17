"""Justicia Orienta -- paquete de la aplicación."""
import email_validator

# El proyecto usa direcciones internas tipo "usuario@justiciaorienta.local"
# como identificador de acceso (no tienen por qué ser correos reales de
# internet -- pensado para despliegue institucional/intranet). El validador
# de correos rechaza ".local" por defecto por ser un dominio de uso especial
# (RFC 6762, mDNS); se habilita explícitamente solo para ese caso.
if "local" in email_validator.SPECIAL_USE_DOMAIN_NAMES:
    email_validator.SPECIAL_USE_DOMAIN_NAMES.remove("local")
