import unittest
from types import SimpleNamespace
from unittest.mock import patch

import config
from util import msx
from models.Channel import Channel


class PlayerSelectionTests(unittest.TestCase):
    def setUp(self):
        self.native = SimpleNamespace(alternative_player=False, proxy=False)
        self.alternative = SimpleNamespace(alternative_player=True, proxy=False)

    @patch.object(config, 'TIZEN', True)
    def test_tizen_uses_native_player_by_default(self):
        action = msx.play_action('https://example.test/video.m3u8', self.native, disable_proxy=True)
        self.assertEqual('video:https://example.test/video.m3u8', action)
        self.assertIn('interaction/tizen.html', msx.player_action_btn(self.native))

    @patch.object(config, 'TIZEN', True)
    @patch.object(config, 'ALTERNATIVE_PLAYER', 'https://example.test/html5x.html')
    def test_alternative_player_overrides_tizen(self):
        action = msx.play_action('https://example.test/video.m3u8', self.alternative, disable_proxy=True)
        self.assertTrue(action.startswith('video:plugin:https://example.test/html5x.html?'))
        self.assertEqual('panel:request:player:options', msx.player_action_btn(self.alternative))

    @patch.object(config, 'TIZEN', True)
    @patch.object(config, 'ALTERNATIVE_PLAYER', 'https://example.test/html5x.html')
    def test_channels_honor_alternative_player(self):
        channel = Channel({'title': 'Test', 'stream': 'https://example.test/live.m3u8'})
        self.assertEqual('video:https://example.test/live.m3u8', channel.to_msx(self.native)['action'])
        self.assertTrue(channel.to_msx(self.alternative)['action'].startswith(
            'video:plugin:https://example.test/html5x.html?'
        ))


if __name__ == '__main__':
    unittest.main()
