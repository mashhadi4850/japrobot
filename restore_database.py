# restore_database.py
from database import init_db, save_user_list, user_list

# داده‌های قبلی
users_to_restore = [
    {'user_id': 812476677, 'referral_code': '5H0KT07J', 'friends_count': 1, 'stars': 0,
        'pending_rewards': 0.0, 'payment_id': '6137461432', 'stellar_address': None},
    {'user_id': 114576904, 'referral_code': '5BI5AU82', 'friends_count': 0, 'stars': 0,
        'pending_rewards': 0.0, 'payment_id': '1842673030', 'stellar_address': None},
    {'user_id': 196872106, 'referral_code': '509BT0VY', 'friends_count': 0, 'stars': 0,
        'pending_rewards': 0.0, 'payment_id': '5962818754', 'stellar_address': None},
    {'user_id': 375331233, 'referral_code': 'V9X8S53J', 'friends_count': 0, 'stars': 0,
        'pending_rewards': 0.0, 'payment_id': '8366572168', 'stellar_address': None}
]

init_db()
# اضافه کردن داده‌های قبلی به user_list
for user in users_to_restore:
    if not any(u["user_id"] == user["user_id"] for u in user_list):
        user_list.append(user)
save_user_list()
print("Data restored to database")
