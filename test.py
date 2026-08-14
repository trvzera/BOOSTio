
from email_validator import validate_email, EmailNotValidError

try:
    validate_email("test@.com")
    print("válido")
except EmailNotValidError as e:
    print("inválido:", e)