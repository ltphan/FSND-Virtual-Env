from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, Item, User

engine = create_engine('sqlite:///itemscatalog.db')

# confused here...
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# is DBsession now a function?
session = DBSession()

#Create dummy user
User1 = User(name="Rob", email="rob@udacity.com", picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

User2 = User(name="Linh", email="linh@udacity.com", picture='http://www.bbc.com/news')
session.add(User2)
session.commit()

User3 = User(name="Hien", email="hien@udacity.com", picture='https://www.instagram.com/')
session.add(User3)
session.commit()

# Snowboarding category and item
# where are ids added?
category1 = Category(name="Snowboard", user_id=User1.id)
session.add(category1)
session.commit()

item1 = Item(name="Board", description="used to slide down the mountains", category=category1, user_id=User1.id)
session.add(item1)
session.commit()

# Skateboard category and item
category2 = Category(name="Skateboard", user_id=User2.id)
session.add(category2)
session.commit()

item2 = Item(name="Skateboard", description="four-wheeled board", category=category2, user_id=User2.id)
session.add(item2)
session.commit()

# Hiking category and item
category3 = Category(name="Hiking", user_id=User3.id)
session.add(category3)
session.commit()

item3 = Item(name="Hiking Boots", description="to walk up hills", category=category3, user_id=User3.id)
session.add(item3)
session.commit()

print "Added items"
