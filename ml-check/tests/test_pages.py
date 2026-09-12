import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.parse import urlencode
from urllib.request import Request, build_opener, ProxyHandler
from urllib.error import HTTPError
from app.main import load_bank, make_handler
from app.pages import error_page


class PracticePages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bank = load_bank()
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(cls.bank))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f'http://127.0.0.1:{cls.server.server_port}/ml-check'
        cls.client = build_opener(ProxyHandler({}))

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def fetch(self, path='', data=None, method=None):
        request = Request(self.base + path, data=urlencode(data).encode() if data is not None else None, method=method)
        return self.client.open(request, timeout=5)

    def test_home_has_every_lesson_and_css(self):
        with self.fetch() as r:
            body = r.read().decode()
            for lesson in self.bank['lessons']:
                self.assertIn('/ml-check/lessons/' + lesson['lesson_id'], body)
        with self.fetch('/assets/site.css') as r:
            self.assertIn('text/css', r.headers['Content-Type'])
            self.assertGreater(len(r.read()), 1000)
        with self.fetch(method='HEAD') as r:
            self.assertEqual(r.read(), b'')
            self.assertGreater(int(r.headers['Content-Length']), 1000)

    def test_both_rounds_and_feedback_for_every_lesson(self):
        for lesson in self.bank['lessons']:
            for phase in ('A', 'B'):
                path = '/lessons/' + lesson['lesson_id']
                questions = [q for q in lesson['questions'] if q['phase'] == phase]
                with self.fetch(path + '?phase=' + phase) as r:
                    body = r.read().decode()
                    self.assertNotIn('参考选项', body)
                    for q in questions:
                        self.assertIn(q['id'], body)
                data = {'phase': phase, **{q['id']: q['answer'] for q in questions}}
                with self.fetch(path + '/check', data) as r:
                    body = r.read().decode()
                    self.assertIn('这轮判断都与题目依据一致', body)
                    self.assertEqual(body.count('参考选项'), 5)
                data[questions[0]['id']] = (questions[0]['answer'] + 1) % 4
                with self.fetch(path + '/check', data) as r:
                    self.assertIn('有 1 道题值得再想一想', r.read().decode())

    def test_invalid_submissions_and_unknown_lesson(self):
        for path, data, code in [('/lessons/C01/check', {'phase': 'A'}, 400), ('/lessons/C01/check', {'phase': 'X'}, 400), ('/lessons/C01?phase=X', None, 400), ('/lessons/S31', None, 404), ('/lessons/S31/check', {'phase': 'A'}, 404)]:
            with self.assertRaises(HTTPError) as caught:
                self.fetch(path, data)
            self.assertEqual(caught.exception.code, code)

    def test_error_message_is_escaped(self):
        self.assertNotIn('<script>', error_page('<script>'))
