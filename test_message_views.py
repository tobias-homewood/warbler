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


class MessageViewTestCase(TestCase):
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

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_not_authenticated(self):
        """Can user add a message when not logged in?"""

        resp = self.client.post("/messages/new", data={"text": "Hello"},
                        follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized", str(resp.data))

    def test_message_show(self):
        """Can user see message?"""

        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser.id
        )

        db.session.add(m)
        db.session.commit()

        resp = self.client.get(f'/messages/{m.id}')

        self.assertEqual(resp.status_code, 200)
        self.assertIn(m.text, str(resp.data))

    def test_message_delete(self):
        """Can user delete a message?"""
        self.login()
        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser.id
        )

        db.session.add(m)
        db.session.commit()

        resp = self.client.post(f'/messages/{m.id}/delete', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        m = Message.query.get(m.id)
        self.assertIsNone(m)

    def test_message_delete_no_authentication(self):
        """Can user delete a message without authentication?"""
        m = Message(
            id=1234,
            text="a test message",
            user_id=self.testuser.id
        )

        db.session.add(m)
        db.session.commit()

        resp = self.client.post(f'/messages/{m.id}/delete', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized", str(resp.data))

        m = Message.query.get(m.id)
        self.assertIsNotNone(m)

    def test_message_like(self):
        """Can user like a message?"""
        self.login()
        m = Message(
            id=1234,
            text="a test message to be liked",
            user_id=self.testuser.id
        )

        db.session.add(m)
        db.session.commit()

        resp = self.client.post(f'/users/toggle_like/{m.id}', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # retrieve the updated user from the db
        self.testuser = db.session.query(User).get(self.testuser.id)

        likes = self.testuser.likes
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].id, 1234)

    def test_message_like_no_authentication(self):
        """Can user like a message without authentication?"""
        
        m = Message(
            text="a test message to be liked",
            user_id=self.testuser.id
        )

        db.session.add(m)
        db.session.commit()

        resp = self.client.post(f'/users/toggle_like/{m.id}', follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Access unauthorized", str(resp.data))
