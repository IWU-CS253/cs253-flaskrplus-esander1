import os
import app as flaskr
import unittest
import tempfile

class FlaskrTestCase(unittest.TestCase):

    def setUp(self):
        self.db_fd, flaskr.app.config['DATABASE'] = tempfile.mkstemp()
        flaskr.app.testing = True
        self.app = flaskr.app.test_client()
        with flaskr.app.app_context():
            flaskr.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(flaskr.app.config['DATABASE'])

    def test_empty_db(self):
        rv = self.app.get('/')
        assert b'No entries here so far' in rv.data

    def test_messages(self):
        rv = self.app.post('/add', data=dict(
            title='<Hello>',
            text='<strong>HTML</strong> allowed here',
            category='A category'
        ), follow_redirects=True)
        assert b'No entries here so far' not in rv.data
        assert b'&lt;Hello&gt;' in rv.data
        assert b'<strong>HTML</strong> allowed here' in rv.data
        assert b'A category' in rv.data

    def test_add_entry(self):
        rv = self.app.post('/add', data=dict(
            title='test title',
            text='test text',
            category='test category'
        ), follow_redirects=True)
        assert b'test title' in rv.data
        assert b'test text' in rv.data
        assert b'test category' in rv.data

    def test_delete_entry(self):
        self.app.post('/add', data=dict(
            title='entry to delete',
            text='this text should be removed',
            category='delete category'
        ), follow_redirects=True)
        rv = self.app.get('/')
        assert b'entry to delete' in rv.data

        with flaskr.app.app_context():
            db = flaskr.get_db()
            cur = db.execute('SELECT id FROM entries WHERE title = ?', ('entry to delete',))
            entry_id = cur.fetchone()['id']

        self.app.post(f'/delete/{entry_id}', follow_redirects=True)
        rv = self.app.get('/')
        assert b'entry to delete' not in rv.data

    def test_filter_by_category(self):
        self.app.post('/add', data=dict(
            title='category test 1',
            text='this is category A',
            category='A'
        ), follow_redirects=True)
        self.app.post('/add', data=dict(
            title='category test 2',
            text='this is category B',
            category='B'
        ), follow_redirects=True)

        rv = self.app.get('/?category=A')
        assert b'category test 1' in rv.data
        assert b'category test 2' not in rv.data

        rv = self.app.get('/?category=B')
        assert b'category test 1' not in rv.data
        assert b'category test 2' in rv.data

    def test_edit_post(self):
        self.app.post('/add', data=dict(
            title='old title',
            text='old text',
            category='old category'
        ), follow_redirects=True)

        with flaskr.app.app_context():
            db = flaskr.get_db()
            cur = db.execute('SELECT id FROM entries WHERE title = ?', ('old title',))
            entry_id = cur.fetchone()['id']

        rv = self.app.post(f'/edit/{entry_id}', data=dict(
            title='new title',
            text='new text',
            category='new category'
        ), follow_redirects=True)

        assert b'new title' in rv.data
        assert b'new text' in rv.data
        assert b'new category' in rv.data
        assert b'old title' not in rv.data
        assert b'old text' not in rv.data
        assert b'old category' not in rv.data

    def test_edit_non_existent_post(self):
        rv = self.app.post('/edit/9999', data=dict(
            title='doesnt exist',
            text='none existent',
            category='none'
        ), follow_redirects=True)

        assert b'Post not found' in rv.data

    def test_edit_with_missing_fields(self):
        self.app.post('/add', data=dict(
            title='edit this',
            text='this too',
            category='also this'
        ), follow_redirects=True)

        with flaskr.app.app_context():
            db = flaskr.get_db()
            cur = db.execute('SELECT id FROM entries WHERE title = ?', ('edit this',))
            entry_id = cur.fetchone()['id']

        rv = self.app.post(f'/edit/{entry_id}', data=dict(
            title='',
            text='not blank',
            category='blank title'
        ), follow_redirects=True)

        assert b'All fields are required' in rv.data
        rv = self.app.get('/')
        assert b'edit this' in rv.data
        assert b'blank title' not in rv.data

if __name__ == '__main__':
    unittest.main()