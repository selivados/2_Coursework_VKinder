import psycopg2

from Settings.db_config import DB_NAME, DB_USER, DB_PASSWORD


class DBManager:

    def _create_db_connection(self):
        self.connect = psycopg2.connect(database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        self.cursor = self.connect.cursor()

    def _close_db_connection(self):
        self.connect.commit()
        self.cursor.close()
        self.connect.close()

    def create_tables(self):
        """
        Creates tables in the database.
        If the tables already exist, then does nothing.
        """
        self._create_db_connection()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id    INTEGER     PRIMARY KEY,
                first_name VARCHAR(40) NOT NULL,
                last_name  VARCHAR(40) NOT NULL,
                sex        INTEGER     NOT NULL,
                age        INTEGER     NOT NULL,
                city       VARCHAR(60) NOT NULL
            );

            CREATE TABLE IF NOT EXISTS photos (
                user_id   INTEGER PRIMARY KEY REFERENCES users (user_id),
                photo_ids TEXT    UNIQUE NOT NULL
            );

            CREATE TABLE IF NOT EXISTS favorite_list (
                PRIMARY KEY (user_id, partner_id),
                user_id    INTEGER REFERENCES users (user_id),
                partner_id INTEGER REFERENCES users (user_id)
            );

            CREATE TABLE IF NOT EXISTS black_list (
                PRIMARY KEY (user_id, partner_id),
                user_id    INTEGER REFERENCES users (user_id),
                partner_id INTEGER REFERENCES users (user_id)
            );
            """
        )
        self._close_db_connection()

    def _delete_tables(self):
        """
        Removes tables from the database.
        """
        self._create_db_connection()
        self.cursor.execute(
            """
            DROP TABLE IF EXISTS favorite_list;
            DROP TABLE IF EXISTS black_list;
            DROP TABLE IF EXISTS photos;
            DROP TABLE IF EXISTS users;
            """
        )
        self._close_db_connection()

    def _add_data_in_users(self, user_data: dict):
        """
        Adds data about the VKontakte user to the users table.
        """
        self._create_db_connection()
        self.cursor.execute(
            """
            INSERT INTO users
            VALUES (%s, %s, %s, %s, %s, %s);
            """, (
                user_data['user_id'],
                user_data['first_name'],
                user_data['last_name'],
                user_data['sex'],
                user_data['age'],
                user_data['city']
            )
        )
        self._close_db_connection()

    def _update_data_in_users(self, user_data: dict):
        """
        Updates data about the VKontakte user in the users table.
        """
        self._create_db_connection()
        self.cursor.execute(
            """
            UPDATE users
               SET first_name = %s,
                   last_name = %s,
                   sex = %s,
                   age = %s,
                   city = %s
             WHERE user_id = %s;
            """, (
                user_data['first_name'],
                user_data['last_name'],
                user_data['sex'],
                user_data['age'],
                user_data['city'],
                user_data['user_id']
            )
        )
        self._close_db_connection()

    def _find_in_users(self, user_data: dict) -> int:
        """
        Looks for records about the VKontakte user in the users table.
        """
        self._create_db_connection()
        self.cursor.execute(
            """
            SELECT COUNT(*)
              FROM users
             WHERE user_id = %s;
            """,
            (user_data['user_id'],)
        )
        result = self.cursor.fetchone()[0]
        self._close_db_connection()
        return result

    def _add_data_in_photos(self, user_data: dict):
        """
        Adds data about photos of the VKontakte user to the photos table.
        """
        self._create_db_connection()
        self.cursor.execute(
            """
            INSERT INTO photos
            VALUES (%s, %s);
            """, (
                user_data['user_id'],
                ','.join(user_data['photo_ids'])
            )
        )
        self._close_db_connection()

    def _update_data_in_photos(self, user_data: dict):
        """
        Updates data about photos of the VKontakte user in the photos table.
        """
        self._create_db_connection()
        self.cursor.execute(
            """
            UPDATE photos
               SET photo_ids = %s
             WHERE user_id = %s;
            """, (
                ','.join(user_data['photo_ids']),
                user_data['user_id']
            )
        )
        self._close_db_connection()

    def _add_data_in_favorite_list(self, user_data: dict, partner_data: dict):
        """
        Adds data to the favorite_list table.
        """
        self._create_db_connection()
        self.cursor.execute(
            """
            INSERT INTO favorite_list
            VALUES (%s, %s);
            """, (
                user_data['user_id'],
                partner_data['user_id']
            )
        )
        self._close_db_connection()

    def _delete_data_in_favorite_list(self, user_data: dict, partner_data: dict):
        """
        Removes data from the favorite_list table.
        """
        self._create_db_connection()
        self.cursor.execute(
            """
            DELETE FROM favorite_list
             WHERE user_id = %s
               AND partner_id = %s;
            """, (
                user_data['user_id'],
                partner_data['user_id']
            )
        )
        self._close_db_connection()

    def _add_or_update_data_in_users_and_photos(self, user_data: dict, partner_data: dict):
        """
        Adds or updates data in the users and photos tables.
        """
        found_user = self._find_in_users(user_data)
        found_partner = self._find_in_users(partner_data)
        if found_user:
            self._update_data_in_users(user_data)
        else:
            self._add_data_in_users(user_data)
        if found_partner:
            self._update_data_in_users(partner_data)
            self._update_data_in_photos(partner_data)
        else:
            self._add_data_in_users(partner_data)
            self._add_data_in_photos(partner_data)

    def find_in_favorite_list(self, user_data: dict, partner_data: dict) -> int:
        """
        Looking for a partner in the favorite list of the VKinder user.
        """
        self._create_db_connection()
        self.cursor.execute(
            """
            SELECT COUNT(*)
              FROM favorite_list
             WHERE user_id = %s
               AND partner_id = %s;
            """, (
                user_data['user_id'],
                partner_data['user_id']
            )
        )
        result = self.cursor.fetchone()[0]
        self._close_db_connection()
        return result

    def add_to_favorite_list(self, user_data: dict, partner_data: dict) -> bool:
        """
        Adds a partner to the favorite list of the VKinder user.
        """
        found_partner_in_fl = self.find_in_favorite_list(user_data, partner_data)
        if found_partner_in_fl:
            return False
        self._add_or_update_data_in_users_and_photos(user_data, partner_data)
        self._add_data_in_favorite_list(user_data, partner_data)
        return True

    def delete_from_favorite_list(self, user_data: dict, partner_data: dict) -> bool:
        """
        Removes a partner from the favorite list of the VKinder user.
        """
        found_partner_in_fl = self.find_in_favorite_list(user_data, partner_data)
        if found_partner_in_fl:
            self._delete_data_in_favorite_list(user_data, partner_data)
            return True
        return False

    def get_favorite_list(self, user_data: dict) -> list:
        """
        Gets a list with data about partners added by the VKinder user to the favorite list.
        """
        self._create_db_connection()
        self.cursor.execute(
            """
            SELECT partner_id, first_name, last_name, age, city, photo_ids
              FROM users AS u
                   JOIN favorite_list AS f
                   ON u.user_id = f.partner_id
                   JOIN photos AS p
                   ON f.partner_id = p.user_id
             WHERE f.user_id = %s;
            """,
            (user_data['user_id'],)
        )
        db_data = self.cursor.fetchall()
        self._close_db_connection()
        favorite_list = []
        for data in db_data:
            partner_data = {
                'user_id': data[0],
                'first_name': data[1],
                'last_name': data[2],
                'age': data[3],
                'city': data[4],
                'photo_ids': data[5].split(',')
            }
            favorite_list.append(partner_data)
        return favorite_list

    def _add_data_in_black_list(self, user_data: dict, partner_data: dict):
        """
        Adds data to the black_list table.
        """
        self._create_db_connection()
        self.cursor.execute(
            """
            INSERT INTO black_list
            VALUES (%s, %s);
            """, (
                user_data['user_id'],
                partner_data['user_id']
            )
        )
        self._close_db_connection()

    def _delete_data_in_black_list(self, user_data: dict, partner_data: dict):
        """
        Removes data from the black_list table.
        """
        self._create_db_connection()
        self.cursor.execute(
            """
            DELETE FROM black_list
             WHERE user_id = %s
               AND partner_id = %s;
            """, (
                user_data['user_id'],
                partner_data['user_id']
            )
        )
        self._close_db_connection()

    def find_in_black_list(self, user_data: dict, partner_data: dict) -> int:
        """
        Looking for a partner in the black list of the VKinder user.
        """
        self._create_db_connection()
        self.cursor.execute(
            """
            SELECT COUNT(*)
              FROM black_list
             WHERE user_id = %s
               AND partner_id = %s;
            """, (
                user_data['user_id'],
                partner_data['user_id']
            )
        )
        result = self.cursor.fetchone()[0]
        self._close_db_connection()
        return result

    def add_to_black_list(self, user_data: dict, partner_data: dict) -> bool:
        """
        Adds a partner to the black list of the VKinder user.
        """
        found_partner_in_bl = self.find_in_black_list(user_data, partner_data)
        if found_partner_in_bl:
            return False
        self._add_or_update_data_in_users_and_photos(user_data, partner_data)
        self._add_data_in_black_list(user_data, partner_data)
        return True

    def delete_from_black_list(self, user_data: dict, partner_data: dict) -> bool:
        """
        Removes a partner from the black list of the VKinder user.
        """
        found_partner_in_bl = self.find_in_black_list(user_data, partner_data)
        if found_partner_in_bl:
            self._delete_data_in_black_list(user_data, partner_data)
            return True
        return False

    def get_black_list(self, user_data: dict) -> list:
        """
        Gets a list with data about partners added by the VKinder user to the black list.
        """
        self._create_db_connection()
        self.cursor.execute(
            """
            SELECT partner_id, first_name, last_name, age, city, photo_ids
              FROM users AS u
                   JOIN black_list AS b
                   ON u.user_id = b.partner_id
                   JOIN photos AS p
                   ON b.partner_id = p.user_id
             WHERE b.user_id = %s;
            """,
            (user_data['user_id'],)
        )
        db_data = self.cursor.fetchall()
        self._close_db_connection()
        black_list = []
        for data in db_data:
            partner_data = {
                'user_id': data[0],
                'first_name': data[1],
                'last_name': data[2],
                'age': data[3],
                'city': data[4],
                'photo_ids': data[5].split(',')
            }
            black_list.append(partner_data)
        return black_list

if __name__ == '__main__':
    db = DBManager()
    db._delete_tables()