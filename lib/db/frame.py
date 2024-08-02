import os
from sqlalchemy import create_engine, Column, Integer, String, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

class DB:
    session = None
    """
        A method to establish a connection to the database, create necessary tables, and initialize a session.
    """
    @classmethod
    def db_connect(cls, config):
        # Create an engine
        db_config = config.get("SQLALCHEMY_DATABASE_URI", "sqlite:///wechat_bot_dev.db")
        engine = create_engine(db_config)

        # Define the base
        Base = declarative_base()

        # Create the tables
        Base.metadata.create_all(engine)

        # Create a session
        Session = sessionmaker(bind=engine)
        cls.session = Session()
        
    @classmethod
    def get_session(cls):
        return cls.session


# Create a new user
# new_user = User(name='John', fullname='John Doe', nickname='johnny')
# session.add(new_user)
# session.commit()

# # Query all users
# users = session.query(User).all()
# for user in users:
#     print(user.name, user.fullname, user.nickname)

# # Update a user
# user = session.query(User).filter_by(name='John').first()
# user.nickname = 'johnny_d'
# session.commit()

# # Delete a user
# user_to_delete = session.query(User).filter_by(name='John').first()
# session.delete(user_to_delete)
# session.commit()

# # Close the session
# session.close()
