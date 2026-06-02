import asyncio
from fastapi_backend.core.database import AsyncSessionLocal
from sqlalchemy import text
from fastapi_backend.services.auth_service import AuthService

async def reset():
    new_password = "TestMaster@Admin2024!"
    hashed = AuthService.hash_password(new_password)
    async with AsyncSessionLocal() as db:
        await db.execute(text("UPDATE users SET password_hash = :hash WHERE username = 'admin'"), {"hash": hashed})
        await db.commit()
        print(f"Admin password reset successfully!")

        # Verify
        r = await db.execute(text("SELECT password_hash FROM users WHERE username = 'admin'"))
        row = r.fetchone()
        if row:
            import bcrypt
            verify = bcrypt.checkpw(new_password.encode(), row[0].encode())
            print(f"Password verify: {verify}")

asyncio.run(reset())
