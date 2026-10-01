import unittest

from util import http


class HttpSessionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        await http.close_session()

    async def test_session_is_reused_and_timeouts_are_bounded(self):
        first = http.get_session()
        second = http.get_session()

        self.assertIs(first, second)
        self.assertLessEqual(first.timeout.total, 5)
        self.assertLessEqual(first.timeout.connect, 5)


if __name__ == '__main__':
    unittest.main()
