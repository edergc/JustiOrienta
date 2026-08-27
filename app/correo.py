"""Envío de correo para "olvidé mi contraseña" -- SMTP simple, sin ningún
servicio de terceros ni costo. Deliberadamente no se llama email.py: ese
nombre chocaría con el paquete email de la librería estándar que se usa
aquí mismo (email.mime.text, email.mime.multipart).
"""
import html
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger("justicia_orienta")

# Mismos tokens de marca que styles.css (--accent2-strong, --accent2, etc.)
# -- el correo debe verse del mismo sistema, no como un aviso genérico.
_TEAL_OSCURO = "#144b3f"
_TEAL = "#1f6e5c"
_TINTA = "#1a2130"
_TINTA_SUAVE = "#4e5a67"
_LINEA = "#d3d6cc"
_PAPEL = "#eef0ea"
_FUENTE_TITULO = "Georgia, 'Iowan Old Style', 'Palatino Linotype', serif"
_FUENTE_TEXTO = "'Segoe UI', Arial, Helvetica, sans-serif"


def _plantilla_restablecer_html(nombre: str, enlace: str, minutos: int) -> str:
    nombre_seguro = html.escape(nombre)
    enlace_seguro = html.escape(enlace)
    return f"""\
<div style="background:{_PAPEL}; padding:32px 16px; font-family:{_FUENTE_TEXTO};">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
         style="max-width:520px; margin:0 auto; background:#ffffff; border-radius:12px; overflow:hidden; border:1px solid {_LINEA};">
    <tr>
      <td style="background:{_TEAL_OSCURO}; padding:24px 32px;">
        <span style="font-family:{_FUENTE_TITULO}; font-size:19px; font-weight:700; color:#ffffff; letter-spacing:0.01em;">
          Justicia Orienta
        </span>
        <div style="font-size:12px; color:#cfe6df; margin-top:2px;">Panel de administración del catálogo</div>
      </td>
    </tr>
    <tr>
      <td style="padding:32px;">
        <h1 style="margin:0 0 16px; font-family:{_FUENTE_TITULO}; font-weight:400; font-size:21px; color:{_TINTA};">
          Restablecer tu contraseña
        </h1>
        <p style="margin:0 0 14px; font-size:15px; line-height:1.6; color:{_TINTA_SUAVE};">Hola {nombre_seguro},</p>
        <p style="margin:0 0 26px; font-size:15px; line-height:1.6; color:{_TINTA_SUAVE};">
          Pediste restablecer la contraseña de tu cuenta en el panel de administración de Justicia Orienta.
          Este enlace es válido por {minutos} minutos.
        </p>
        <table role="presentation" cellpadding="0" cellspacing="0">
          <tr>
            <td style="border-radius:8px; background:{_TEAL};">
              <a href="{enlace_seguro}"
                 style="display:inline-block; padding:13px 30px; font-family:{_FUENTE_TEXTO}; font-size:15px;
                        font-weight:700; color:#ffffff; text-decoration:none; border-radius:8px;">
                Elegir nueva contraseña
              </a>
            </td>
          </tr>
        </table>
        <p style="margin:26px 0 0; font-size:13px; line-height:1.5; color:{_TINTA_SUAVE};">
          Si el botón no funciona, copia y pega este enlace en tu navegador:<br />
          <a href="{enlace_seguro}" style="color:{_TEAL_OSCURO}; word-break:break-all;">{enlace_seguro}</a>
        </p>
        <p style="margin:22px 0 0; font-size:13px; line-height:1.5; color:{_TINTA_SUAVE};">
          Si no fuiste tú quien lo pidió, ignora este correo -- tu contraseña actual sigue funcionando.
        </p>
      </td>
    </tr>
    <tr>
      <td style="padding:16px 32px; background:{_PAPEL}; border-top:1px solid {_LINEA}; font-size:12px; color:{_TINTA_SUAVE};">
        Coordinación de Informática — Corte Superior de Justicia de Lima
      </td>
    </tr>
  </table>
</div>
"""


def _plantilla_restablecer_texto(nombre: str, enlace: str, minutos: int) -> str:
    return (
        f"Hola {nombre},\n\n"
        "Pediste restablecer la contraseña de tu cuenta en el panel de Justicia Orienta.\n"
        f"Entra a este enlace en los próximos {minutos} minutos para elegir una nueva:\n\n{enlace}\n\n"
        "Si no fuiste tú quien lo pidió, ignora este correo -- tu contraseña actual sigue funcionando.\n\n"
        "-- Coordinación de Informática, Corte Superior de Justicia de Lima"
    )


def enviar_correo_restablecer(destino: str, nombre: str, enlace: str, minutos: int) -> None:
    enviar_correo(
        destino,
        "Restablecer tu contraseña -- Justicia Orienta",
        _plantilla_restablecer_texto(nombre, enlace, minutos),
        cuerpo_html=_plantilla_restablecer_html(nombre, enlace, minutos),
    )


def enviar_correo(destino: str, asunto: str, cuerpo_texto: str, cuerpo_html: str | None = None) -> None:
    if not settings.smtp_host:
        # Desarrollo local sin SMTP configurado: se deja constancia de qué
        # se habría enviado, para poder probar el flujo completo (incluido
        # el enlace con el token) sin depender de un servidor de correo real.
        logger.info("SMTP no configurado -- correo simulado a %s\nAsunto: %s\n%s", destino, asunto, cuerpo_texto)
        return

    if cuerpo_html:
        # multipart/alternative: el cliente de correo elige la versión HTML si
        # sabe mostrarla: si no (o el usuario prefiere texto plano), cae a la
        # versión de texto -- nunca se manda solo una sin la otra.
        mensaje = MIMEMultipart("alternative")
        mensaje.attach(MIMEText(cuerpo_texto, "plain", "utf-8"))
        mensaje.attach(MIMEText(cuerpo_html, "html", "utf-8"))
    else:
        mensaje = MIMEText(cuerpo_texto, "plain", "utf-8")
    mensaje["Subject"] = asunto
    mensaje["From"] = settings.smtp_remitente
    mensaje["To"] = destino

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as servidor:
        servidor.ehlo()
        # Un relay interno (típico en puerto 25, dentro de la red institucional)
        # normalmente no ofrece STARTTLS ni pide autenticación -- se usan solo
        # si el servidor los anuncia, en vez de asumir que todo SMTP es igual
        # a Gmail/Outlook.
        if servidor.has_extn("STARTTLS"):
            servidor.starttls()
            servidor.ehlo()
        if settings.smtp_usuario:
            servidor.login(settings.smtp_usuario, settings.smtp_password)
        servidor.send_message(mensaje)
