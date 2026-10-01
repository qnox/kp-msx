import unittest

from util import observability


class ClientObservabilityTests(unittest.TestCase):
    def test_record_redacts_urls_and_ignores_unknown_fields(self):
        event = observability.record_client_event({
            'event': 'plugin_error',
            'detail': 'Failed https://example.test/video.m3u8?token=secret',
            'ready_state': 2,
            'stream_url': 'https://example.test/private.m3u8',
        }, client_ip='192.0.2.10', user_agent='Test TV')

        self.assertEqual('Failed [url]', event['detail'])
        self.assertEqual(2, event['ready_state'])
        self.assertNotIn('stream_url', event)

    def test_event_name_is_required(self):
        with self.assertRaises(ValueError):
            observability.record_client_event({'detail': 'missing event'})

    def test_rate_limit_is_bounded_per_client(self):
        self.assertTrue(observability.allow_client_event('test-client', limit=2))
        self.assertTrue(observability.allow_client_event('test-client', limit=2))
        self.assertFalse(observability.allow_client_event('test-client', limit=2))


if __name__ == '__main__':
    unittest.main()
