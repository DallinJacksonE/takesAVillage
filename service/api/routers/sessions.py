import uuid
from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException, Response


def create_router(services):
    router = APIRouter()

    @router.get("/api/verifySession")
    async def verify_session(user_session: Optional[str] = Cookie(None)):
        if user_session and services.database.user_exists(user_session):
            return {"userId": user_session, "message": "Session valid"}
        raise HTTPException(status_code=401, detail="No valid session")

    @router.post("/api/consent")
    async def consent(response: Response):
        user_id = str(uuid.uuid4())
        services.database.create_user(user_id, True)
        response.set_cookie(key="user_session", value=user_id, max_age=86400,
                            secure=False, samesite="lax")
        return {"message": "Consent logged", "userId": user_id}

    return router
