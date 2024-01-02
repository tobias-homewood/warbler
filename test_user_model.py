"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.session.rollback()
        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()


    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)
        self.assertEqual(u.username, "testuser")
        self.assertEqual(u.email, "test@test.com")
        self.assertEqual(u.password, "HASHED_PASSWORD")

    def test_repr(self):
        """Does the repr method work as expected?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        self.assertEqual(u.__repr__(), f"<User #{u.id}: {u.username}, {u.email}>")
    

    def test_is_following(self):
        """Does is_following successfully detect when user1 is following user2?"""

        u1 = User(
            email="user1@test.com",
            username="user1",
            password="HASHED_PASSWORD"
        )
        u2 = User(
            email="user2@test.com",
            username="user2",
            password="HASHED_PASSWORD"
        )
    
        # this is the ORM way of doing it
        u1.following.append(u2)

        # this is the SQL way of doing it
        # add the follow in the Follows table
        # f = Follows(user_being_followed_id=u2.id, user_following_id=u1.id)
        # db.session.add(f)

        db.session.add_all([u1, u2])
        db.session.commit()

        self.assertEqual(u1.is_following(u2), True)
        self.assertEqual(u2.is_following(u1), False)

    def test_is_followed_by(self):
        """Does is_followed_by successfully detect when user1 is followed by user2?"""

        u1 = User(
            email="user1@test.com",
            username="user1",
            password="HASHED_PASSWORD"
        )
        u2 = User(
            email="user2@test.com",
            username="user2",
            password="HASHED_PASSWORD"
        )

        u1.followers.append(u2)

        db.session.add_all([u1, u2])
        db.session.commit()

        self.assertEqual(u1.is_followed_by(u2), True)
        self.assertEqual(u2.is_followed_by(u1), False)

    def test_signup(self):
        """Does User.signup successfully create a new user given valid credentials?"""

        u = User.signup(
            username="testuser",
            email="test@test.com",
            password="real_password",
            image_url=None
        )

        db.session.commit()

        self.assertEqual(u, db.session.query(User).get(u.id))

    def test_signup_repeated_fail(self):
        """Does User.signup fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?"""

        u = User.signup(
            username="testuser",
            email="test@test.com",
            password="real_password",
            image_url=None
        )
        db.session.commit()

        repeated = User.signup(
            username="testuser",
            email="different@email.com",
            password="real_password",
            image_url=None
        )

        self.assertRaises(Exception, db.session.commit)

    
    def test_signup_invalid_fail(self):
        """Does User.signup fail to create a new user if any of the validations (e.g. uniqueness, non-nullable fields) fail?"""

        no_username = User.signup(
            username=None,
            email="whatever",
            password="real_password",
            image_url=None
        )

        self.assertRaises(Exception, db.session.commit)

        no_email = User.signup(
            username="something",
            email=None,
            password="real_password",
            image_url=None
        )

        self.assertRaises(Exception, db.session.commit)

    def test_authenticate(self):
        """Does User.authenticate successfully return a user when given a valid username and password?"""

        u = User.signup(
            username="testuser",
            email="test@test.com",
            password="real_password",
            image_url=None
        )

        db.session.commit()

        self.assertEqual(User.authenticate("testuser", "real_password"), u)

    def test_authenticate_fail(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""

        u = User.signup(
            username="testuser",
            email="test@test.com",
            password="real_password",
            image_url=None
        )

        db.session.commit()

        self.assertFalse(User.authenticate("wronguser", "real_password"))
        self.assertFalse(User.authenticate("testuser", "wrong_password"))