from aiogram.fsm.storage.base import BaseStorage, StorageKey
from sqlalchemy import Column, BigInteger, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select


Base = declarative_base()


class UserState(Base):
    __tablename__ = 'customers_state'
    user_id = Column(BigInteger)
    state = Column(String)


class PostgreSQLStorage(BaseStorage):
    def __init__(self, session):
        self.session = session

    async def set_state(self, key: StorageKey, state: str = None) -> None:
        user_id = key.user_id
        async with self.session.begin():
            result = await self.session.execute(select(UserState).where(UserState.user_id == user_id))
            user_state = result.scalar_one_or_none()

            if user_state:
                user_state.state = state
            else:
                user_state = UserState(user_id=user_id, state=state)
                self.session.add(user_state)

            await self.session.commit()
