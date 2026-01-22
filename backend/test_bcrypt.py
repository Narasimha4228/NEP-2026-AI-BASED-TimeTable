from passlib.context import CryptContext
ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
try:
    hashed = ctx.hash("Reddy1234")
    print("Hash:", hashed)
    print("Verify:", ctx.verify("Reddy1234", hashed))
except Exception as e:
    print("ERROR:", e)
