import sqlite3

DATABASE_PATH = "users.db"
user_list = []


def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER, referral_code TEXT, friends_count INTEGER, stars INTEGER, pending_rewards REAL, payment_id TEXT, stellar_address TEXT)''')
    conn.commit()
    conn.close()


def load_user_list():
    global user_list
    user_list = []
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        rows = c.fetchall()
        for row in rows:
            user_list.append({
                "user_id": row[0],
                "referral_code": row[1],
                "friends_count": row[2],
                "stars": row[3],
                "pending_rewards": row[4],
                "payment_id": row[5],
                "stellar_address": row[6]
            })
        conn.close()
        print(f"[DEBUG] Loaded {len(user_list)} users from database")
    except Exception as e:
        print(f"[ERROR] Failed to load user list: {e}")
    print_user_list()


def save_user_list():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM users")
        for user in user_list:
            c.execute("INSERT INTO users (user_id, referral_code, friends_count, stars, pending_rewards, payment_id, stellar_address) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (user["user_id"], user["referral_code"], user["friends_count"], user["stars"], user["pending_rewards"], user.get("payment_id"), user["stellar_address"]))
        conn.commit()
        conn.close()
        print("[DEBUG] User list saved to database")
    except Exception as e:
        print(f"[ERROR] Failed to save user list: {e}")


def print_user_list():
    print("[DEBUG] Current user_list:")
    for user in user_list:
        print(user)


def add_user(user):
    user_list.append(user)


def get_user(user_id):
    return next((user for user in user_list if user["user_id"] == user_id), None)


def get_top_users(limit=20):
    sorted_users = sorted(user_list, key=lambda x: (
        x["friends_count"], x["stars"]), reverse=True)
    return sorted_users[:limit]
