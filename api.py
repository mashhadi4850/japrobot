from fastapi import FastAPI
from database import init_db, get_user, get_top_users

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/user/{user_id}")
async def get_user_position(user_id: int):
    user = get_user(user_id)
    if not user:
        return {"error": "User not found"}
    top_users = get_top_users()
    rank = next((i + 1 for i, u in enumerate(top_users)
                if u[0] == user_id), None)
    return {
        "user_id": user[0],
        "referral_code": user[1],
        "friends_count": user[2],
        "stars": user[3],
        "pending_rewards": user[4],
        "rank": rank,
        "top_users": [
            {"user_id": u[0], "referral_code": u[1], "friends_count": u[2],
                "stars": u[3], "pending_rewards": u[4]}
            for u in top_users
        ]
    }