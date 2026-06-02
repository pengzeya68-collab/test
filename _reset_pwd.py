import asyncio
from fastapi_backend.core.database import AsyncSessionLocal
from sqlalchemy import text
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def reset():
    new_password = "TestMaster@Admin2024!"
    hashed = pwd_context.hash(new_password)
    async with AsyncSessionLocal() as db:
        await db.execute(text("UPDATE users SET password_hash = :hash WHERE username = 'admin'"), {"hash": hashed})
        await db.commit()
        print(f"Admin password reset to: {new_password}")
        print(f"Hash: {hashed[:50]}...")

        # Verify
        r = await db.execute(text("SELECT password_hash FROM users WHERE username = 'admin'"))
        row = r.fetchone()
        if row:
            verify = pwd_context.verify(new_password, row[0])
            print(f"Verify: {verify}")

asyncio.run(reset())
