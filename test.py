
from email_validator import validate_email, EmailNotValidError

def validar_email(email:str):
  emailinfo = validate_email(email,check_deliverability=Fa)
  return emailinfo.normalized


print(validate_email("gugscla.000@gmail.com"))