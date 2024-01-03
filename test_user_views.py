"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def login(self):
        """Log in user."""
        with self.client.session_transaction() as session:
            session[CURR_USER_KEY] = self.testuser.id

    def test_list_users(self):
        """Can we view the list of users?"""

        with self.client as c:
            resp = c.get("/users")

            self.assertIn("@testuser", str(resp.data))

    def test_user_show(self):
        """Can we view a user?"""

        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}")

            self.assertIn("@testuser", str(resp.data))

    def test_user_following(self):
        """Can we view a user's following page?"""

        with self.client as c:
            self.login()
            resp = c.get(f"/users/{self.testuser.id}/following")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))

    def test_user_following_no_authentication(self):
        """Can we view a user's following page without authentication?"""

        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}/following", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_user_followers(self):
        """Can we view a user's followers page?"""

        with self.client as c:
            self.login()
            resp = c.get(f"/users/{self.testuser.id}/followers")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))

    def test_user_followers_no_authentication(self):
        """Can we view a user's followers page without authentication?"""

        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}/followers", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_user_likes(self):
        """Can we view a user's likes page?"""

        with self.client as c:
            self.login()
            resp = c.get(f"/users/{self.testuser.id}/likes")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser", str(resp.data))

    def test_user_likes_no_authentication(self):
        """Can we view a user's likes page without authentication?"""

        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}/likes", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_add_follow(self):
        """Can we add a follow?"""
        with self.client as c:
            self.login()

            u = User(
                email="user2@test.com",
                username="user2",
                password="HASHED_PASSWORD"
            )

            db.session.add(u)
            db.session.commit()

            self.testuser = db.session.query(User).get(self.testuser.id)
            self.assertEqual(len(self.testuser.following), 0)


            resp = c.post(f"/users/follow/{u.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            # retrieve the updated user from the db
            self.testuser = db.session.query(User).get(self.testuser.id)
            self.assertEqual(len(self.testuser.following), 1)

    def test_add_follow_no_authentication(self):
        """Can we add a follow without authentication?"""
        with self.client as c:
            u = User(
                email="user2@test.com",
                username="user2",
                password="HASHED_PASSWORD"
            )

            db.session.add(u)
            db.session.commit()

            resp = c.post(f"/users/follow/{u.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))
            
    def test_stop_following(self):
        """Can we stop following?"""
        with self.client as c:
            self.login()

            u = User(
                email="user2@test.com",
                username="user2",
                password="HASHED_PASSWORD"
            )
            db.session.add(u)
            db.session.commit()

            self.testuser = db.session.query(User).get(self.testuser.id)
            self.testuser.following.append(u)
            db.session.add(self.testuser)
            db.session.commit()


            resp = c.post(f"/users/stop-following/{u.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            # retrieve the updated user from the db
            self.testuser = db.session.query(User).get(self.testuser.id)
            self.assertEqual(len(self.testuser.following), 0)

    def test_stop_following_no_authentication(self):
        """Can we stop following without authentication?"""
        with self.client as c:

            u = User(
                email="user2@test.com",
                username="user2",
                password="HASHED_PASSWORD"
            )
            db.session.add(u)
            db.session.commit()

            resp = c.post(f"/users/stop-following/{u.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", str(resp.data))

    def test_user_edit(self):
        """Can we edit our profile?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # GET REQUEST
            resp = c.get(f"/users/profile")

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<h2 class="join-message">Edit Your Profile.</h2>', str(resp.data))

            # POST REQUEST
            resp = c.post(f"/users/profile", data={
                "username": "testuser2",
                "email": "edited_email@ex.com",
                "image_url": None,
                "header_image_url": None,
                "bio": None,
                "password": "testuser",
                }, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            
            # check the user was updated
            self.testuser = db.session.query(User).get(self.testuser.id)

            self.assertEqual(self.testuser.username, "testuser2")
            self.assertEqual(self.testuser.email, "edited_email@ex.com")

    def test_user_edit_no_authentication(self):
        """Can we edit our profile without authentication?"""

        with self.client as c:

            # GET REQUEST
            resp = c.get(f"/users/profile", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))           

            # POST REQUEST
            resp = c.post(f"/users/profile", data={}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_user_delete(self):
        """Can we delete our profile?"""

        with self.client as c:
            self.login()

            resp = c.post(f"/users/delete", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            # check the user was deleted
            self.assertIsNone(db.session.query(User).get(self.testuser.id))

    def test_user_delete_no_authentication(self):
        """Can we delete our profile without authentication?"""

        with self.client as c:

            resp = c.post(f"/users/delete", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))