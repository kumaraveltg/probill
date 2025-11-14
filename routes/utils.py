from passlib.context import CryptContext
from cryptography.fernet import Fernet

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash a plain password."""
    return pwd_context.hash(password)

#===================haspassword end============



# Generate a key once and store it securely (e.g., in .env)
FERNET_KEY = b'R9x5WbHXOLa_3A5PteCB7gI3FXokWbclZfQTDKkHzTA='  # example: Fernet.generate_key()
fernet = Fernet(FERNET_KEY)

def encrypt_password(password: str) -> str:
    return fernet.encrypt(password.encode()).decode()

def decrypt_password(encrypted: str) -> str:
    return fernet.decrypt(encrypted.encode()).decode()