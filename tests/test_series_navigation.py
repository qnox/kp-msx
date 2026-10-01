import unittest
from types import SimpleNamespace
from unittest.mock import patch

import config
from models.Content import Content


def episode(number, watched, url=None):
    files = []
    if url is not None:
        files.append({
            'quality': '1080p',
            'quality_id': 1,
            'url': {'hls4': url},
        })
    return {
        'number': number,
        'title': f'Episode {number}',
        'watched': 1 if watched else 0,
        'files': files,
        'subtitles': [],
    }


def series(seasons):
    return Content({
        'id': 42,
        'title': 'Test Series',
        'plot': 'Test series plot.',
        'posters': {'big': 'https://example.test/poster.jpg'},
        'seasons': [
            {'number': number, 'episodes': episodes}
            for number, episodes in seasons
        ],
    })


class SeriesNavigationTests(unittest.TestCase):
    def setUp(self):
        self.settings = SimpleNamespace(
            alternative_player=False,
            poster_proxy='direct',
            poster_size='big',
            proxy=False,
        )

    @patch.object(config, 'TIZEN', True)
    def test_new_series_plays_first_episode_directly(self):
        content = series([(1, [
            episode(1, False, 'https://example.test/s1e1.m3u8'),
            episode(2, False, 'https://example.test/s1e2.m3u8'),
        ])])

        page = content.to_msx_content(device_settings=self.settings)
        buttons = {item.get('id'): item for item in page['pages'][0]['items']}

        self.assertEqual('Смотреть S1E1', buttons['watch_button']['label'])
        self.assertIn('playlist:', buttons['watch_button']['action'])
        self.assertTrue(buttons['watch_button']['action'].endswith('>index:0'))
        self.assertNotIn('episodes_button', buttons)

    @patch.object(config, 'TIZEN', True)
    def test_partially_watched_series_plays_next_unwatched_episode(self):
        content = series([
            (1, [
                episode(1, True, 'https://example.test/s1e1.m3u8'),
                episode(2, False, 'https://example.test/s1e2.m3u8'),
            ]),
            (2, [episode(1, False, 'https://example.test/s2e1.m3u8')]),
        ])

        page = content.to_msx_content(device_settings=self.settings)
        buttons = {item.get('id'): item for item in page['pages'][0]['items']}

        self.assertEqual('Продолжить S1E2', buttons['watch_button']['label'])
        self.assertTrue(buttons['watch_button']['action'].endswith('>index:1'))

        playlist = content.to_msx_playlist(device_settings=self.settings)
        properties = playlist['items'][1]['properties']
        self.assertIn('trigger:90%', properties)
        self.assertNotIn('trigger:ready', properties)
        self.assertEqual('large', properties['info:size'])
        self.assertEqual('full', properties['info:overlay'])
        self.assertIn('Test Series{br}S1E2', properties['info:text'])
        self.assertIn('Test series plot.', properties['info:text'])
        self.assertEqual('https://example.test/poster.jpg', properties['info:image'])
        self.assertIn('player:content:', properties['button:content:action'])

    @patch.object(config, 'TIZEN', True)
    def test_fully_watched_series_restarts_from_first_episode(self):
        content = series([(1, [
            episode(1, True, 'https://example.test/s1e1.m3u8'),
            episode(2, True, 'https://example.test/s1e2.m3u8'),
        ])])

        page = content.to_msx_content(device_settings=self.settings)
        buttons = {item.get('id'): item for item in page['pages'][0]['items']}

        self.assertEqual('Сначала S1E1', buttons['watch_button']['label'])
        self.assertTrue(buttons['watch_button']['action'].endswith('>index:0'))

    def test_episode_and_season_pickers_have_one_focus_target(self):
        content = series([
            (1, [episode(1, True, 'https://example.test/s1e1.m3u8')]),
            (2, [
                episode(1, False, 'https://example.test/s2e1.m3u8'),
                episode(2, False, 'https://example.test/s2e2.m3u8'),
            ]),
        ])

        seasons = content.to_seasons_msx_panel()['items']
        episodes = content.to_episodes_msx_panel(2, device_settings=self.settings)['items']

        self.assertEqual([False, True], [item['focus'] for item in seasons])
        self.assertEqual([True, False], [item['focus'] for item in episodes])
        self.assertTrue(episodes[1]['action'].endswith('>index:2'))

    @patch.object(config, 'TIZEN', True)
    def test_playlist_keeps_episode_order_and_native_actions(self):
        content = series([
            (1, [episode(1, True, 'https://example.test/s1e1.m3u8')]),
            (2, [episode(1, False, 'https://example.test/s2e1.m3u8')]),
        ])

        playlist = content.to_msx_playlist(device_settings=self.settings)

        self.assertEqual(['s1e1', 's2e1'], [item['id'] for item in playlist['items']])
        self.assertEqual(
            ['video:https://example.test/s1e1.m3u8', 'video:https://example.test/s2e1.m3u8'],
            [item['action'] for item in playlist['items']],
        )


if __name__ == '__main__':
    unittest.main()
