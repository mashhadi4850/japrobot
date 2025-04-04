# test_database.py
from database import init_db, load_user_list, save_user_list, user_list

init_db()
load_user_list()
print("After loading:")
for user in user_list:
    print(user)
