from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_pain_points():
    return {"message": "Pain detector endpoint"}