from sqlalchemy import CheckConstraint, Column, Integer, ForeignKey, String
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class FavoritePartner(Base):
    __tablename__ = 'favorite_partners'

    user_id = Column(
        Integer,
        ForeignKey('users.user_id', ondelete='CASCADE'),
        primary_key=True
    )
    partner_id = Column(
        Integer,
        ForeignKey('users.user_id', ondelete='CASCADE'),
        primary_key=True
    )

    user = relationship(
        'User', foreign_keys=[user_id], back_populates='favorite_partners'
    )
    partner = relationship(
        'User', foreign_keys=[partner_id], back_populates='favorited_by'
    )

    __table_args__ = (
        CheckConstraint('user_id != partner_id', name='favorite_not_self'),
    )


class BlockedPartner(Base):
    __tablename__ = 'blocked_partners'

    user_id = Column(
        Integer,
        ForeignKey('users.user_id', ondelete='CASCADE'),
        primary_key=True
    )
    partner_id = Column(
        Integer,
        ForeignKey('users.user_id', ondelete='CASCADE'),
        primary_key=True
    )

    user = relationship(
        'User', foreign_keys=[user_id], back_populates='blocked_partners'
    )
    partner = relationship(
        'User', foreign_keys=[partner_id], back_populates='blocked_by'
    )

    __table_args__ = (
        CheckConstraint('user_id != partner_id', name='blocked_not_self'),
    )


class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    sex = Column(Integer, nullable=False)
    age = Column(Integer, nullable=False)
    city = Column(String(50), nullable=False)

    photos = relationship(
        'Photo', cascade='all, delete-orphan', back_populates='user'
    )
    favorite_partners = relationship(
        'FavoritePartner',
        foreign_keys=[FavoritePartner.user_id],
        cascade='all, delete-orphan',
        back_populates='user'
    )
    favorited_by = relationship(
        'FavoritePartner',
        foreign_keys=[FavoritePartner.partner_id],
        back_populates='partner'
    )
    blocked_partners = relationship(
        'BlockedPartner',
        foreign_keys=[BlockedPartner.user_id],
        cascade='all, delete-orphan',
        back_populates='user'
    )
    blocked_by = relationship(
        'BlockedPartner',
        foreign_keys=[BlockedPartner.partner_id],
        back_populates='partner'
    )

    __table_args__ = (
        CheckConstraint('sex IN (1, 2)', name='valid_sex'),
        CheckConstraint('age > 0', name='valid_age'),
    )


class Photo(Base):
    __tablename__ = 'photos'

    photo_id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer,
        ForeignKey('users.user_id', ondelete='CASCADE'),
        nullable=False
    )

    user = relationship('User', back_populates='photos')


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
