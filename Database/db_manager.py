import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, URL, delete, select
from sqlalchemy.orm import sessionmaker, joinedload

from Database.db_models import (
    create_tables, User, Photo, FavoritePartner, BlockedPartner
)

load_dotenv()


class DBManager:

    def __init__(self):
        self.engine = create_engine(URL.create(
            drivername=f"{os.getenv('DB_DIALECT')}+{os.getenv('DB_DRIVER')}",
            username=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'))
        )
        self.session_maker = sessionmaker(bind=self.engine)
        create_tables(self.engine)

    def _add_or_update_data_in_users(self, user_data: dict):
        """
        Adds or updates data in the users table.
        """
        with self.session_maker() as session:
            user = session.get(User, user_data['user_id'])
            if user:
                user.first_name = user_data['first_name']
                user.last_name = user_data['last_name']
                user.sex = user_data['sex']
                user.age = user_data['age']
                user.city = user_data['city']
            else:
                user = User(
                    user_id=user_data['user_id'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    sex=user_data['sex'],
                    age=user_data['age'],
                    city=user_data['city']
                )
                session.add(user)
            session.commit()

    def _add_or_update_data_in_photos(self, user_data: dict):
        """
        Adds or updates data in the photos table.
        """
        with self.session_maker() as session:
            user = session.get(User, user_data['user_id'])
            if user and 'photo_ids' in user_data:
                user.photos.clear()
                for photo_id in user_data['photo_ids']:
                    user.photos.append(Photo(photo_id=photo_id))
                session.commit()

    def _add_data_in_favorite_partners(
        self, user_data: dict, partner_data: dict
    ):
        """
        Adds data to the favorite_partners table.
        """
        with self.session_maker() as session:
            favorite_partner = FavoritePartner(
                user_id=user_data['user_id'],
                partner_id=partner_data['user_id']
            )
            session.add(favorite_partner)
            session.commit()

    def _delete_data_in_favorite_partners(
        self, user_data: dict, partner_data: dict
    ):
        """
        Removes data from the favorite_partners table.
        """
        with self.session_maker() as session:
            session.execute(delete(FavoritePartner).where(
                FavoritePartner.user_id == user_data['user_id'],
                FavoritePartner.partner_id == partner_data['user_id'])
            )
            session.commit()

    def _add_data_in_blocked_partners(
        self, user_data: dict, partner_data: dict
    ):
        """
        Adds data to the blocked_partners table.
        """
        with self.session_maker() as session:
            blocked_partner = BlockedPartner(
                user_id=user_data['user_id'],
                partner_id=partner_data['user_id']
            )
            session.add(blocked_partner)
            session.commit()

    def _delete_data_in_blocked_partners(
        self, user_data: dict, partner_data: dict
    ):
        """
        Removes data from the blocked_partners table.
        """
        with self.session_maker() as session:
            session.execute(delete(BlockedPartner).where(
                BlockedPartner.user_id == user_data['user_id'],
                BlockedPartner.partner_id == partner_data['user_id'])
            )
            session.commit()

    def find_in_favorite_partners(self, user_data: dict, partner_data: dict):
        """
        Looking for a partner in the favorite partners of the VKinder user.
        """
        with self.session_maker() as session:
            stmt = select(FavoritePartner).where(
                FavoritePartner.user_id == user_data['user_id'],
                FavoritePartner.partner_id == partner_data['user_id']
            )
            result = session.execute(stmt).first()
        return result

    def add_to_favorite_partners(self, user_data: dict, partner_data: dict):
        """
        Adds a partner to the favorite partners of the VKinder user.
        """
        self._add_or_update_data_in_users(user_data)
        self._add_or_update_data_in_users(partner_data)
        self._add_or_update_data_in_photos(partner_data)
        is_favorite = self.find_in_favorite_partners(user_data, partner_data)
        is_blocked = self.find_in_blocked_partners(user_data, partner_data)
        if not is_favorite:
            self._add_data_in_favorite_partners(user_data, partner_data)
        if is_blocked:
            self._delete_data_in_blocked_partners(user_data, partner_data)

    def delete_from_favorite_partners(
        self, user_data: dict, partner_data: dict
    ):
        """
        Removes a partner from the favorite partners of the VKinder user.
        """
        is_favorite = self.find_in_favorite_partners(user_data, partner_data)
        if is_favorite:
            self._delete_data_in_favorite_partners(user_data, partner_data)

    def get_favorite_partners(self, user_data: dict):
        """
        Gets a list with data about partners added by the VKinder user to the
        favorite partners.
        """
        with self.session_maker() as session:
            stmt = (
                select(User)
                .options(
                    joinedload(User.favorite_partners)
                    .joinedload(FavoritePartner.partner)
                    .joinedload(User.photos)
                )
                .where(User.user_id == user_data['user_id'])
            )
            user = session.execute(stmt).unique().scalar_one_or_none()
            if not user:
                return []
            favorite_partners = [
                {
                    'user_id': fp.partner.user_id,
                    'first_name': fp.partner.first_name,
                    'last_name': fp.partner.last_name,
                    'age': fp.partner.age,
                    'city': fp.partner.city,
                    'photo_ids': [p.photo_id for p in fp.partner.photos]
                }
                for fp in user.favorite_partners
            ]
        return favorite_partners

    def find_in_blocked_partners(self, user_data: dict, partner_data: dict):
        """
        Looking for a partner in the blocked partners of the VKinder user.
        """
        with self.session_maker() as session:
            stmt = select(BlockedPartner).where(
                BlockedPartner.user_id == user_data['user_id'],
                BlockedPartner.partner_id == partner_data['user_id']
            )
            result = session.execute(stmt).first()
        return result

    def add_to_blocked_partners(self, user_data: dict, partner_data: dict):
        """
        Adds a partner to the blocked partners of the VKinder user.
        """
        self._add_or_update_data_in_users(user_data)
        self._add_or_update_data_in_users(partner_data)
        self._add_or_update_data_in_photos(partner_data)
        is_favorite = self.find_in_favorite_partners(user_data, partner_data)
        is_blocked = self.find_in_blocked_partners(user_data, partner_data)
        if is_favorite:
            self._delete_data_in_favorite_partners(user_data, partner_data)
        if not is_blocked:
            self._add_data_in_blocked_partners(user_data, partner_data)

    def delete_from_blocked_partners(
        self, user_data: dict, partner_data: dict
    ):
        """
        Removes a partner from the blocked partners of the VKinder user.
        """
        is_blocked = self.find_in_blocked_partners(user_data, partner_data)
        if is_blocked:
            self._delete_data_in_blocked_partners(user_data, partner_data)

    def get_blocked_partners(self, user_data: dict):
        """
        Gets a list with data about partners added by the VKinder user to the
        blocked partners.
        """
        with self.session_maker() as session:
            stmt = (
                select(User)
                .options(
                    joinedload(User.blocked_partners)
                    .joinedload(BlockedPartner.partner)
                    .joinedload(User.photos)
                )
                .where(User.user_id == user_data['user_id'])
            )
            user = session.execute(stmt).unique().scalar_one_or_none()
            if not user:
                return []
            blocked_partners = [
                {
                    'user_id': bp.partner.user_id,
                    'first_name': bp.partner.first_name,
                    'last_name': bp.partner.last_name,
                    'age': bp.partner.age,
                    'city': bp.partner.city,
                    'photo_ids': [p.photo_id for p in bp.partner.photos]
                }
                for bp in user.blocked_partners
            ]
        return blocked_partners
