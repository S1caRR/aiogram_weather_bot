from vedis import Vedis
import config


def get_users_city(user_id):
    """
    Get user's city from db
    """
    with Vedis(config.db_file) as db:
        try:
            return db[user_id].decode()
        except KeyError:
            raise KeyError("User didn't enter city")


def change_users_city(user_id, city):
    """
    Change user's city
    """
    with Vedis(config.db_file) as db:
        try:
            db[user_id] = city
            return True
        except:
            return False