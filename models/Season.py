from models.Episode import Episode



class Season:

    def __init__(self, data, content_id):
        self.content_id = content_id

        self.n = data.get('number')
        self.id = data.get('id')
        self.episodes = [Episode(i, content_id, self.n) for i in data.get('episodes')]

        self.watched = self._watched()

    def to_episode_pages(self, device_settings: 'DeviceSettings' = None, action_for_episode=None):
        items = []
        focus_index = next(
            (i for i, episode in enumerate(self.episodes) if not episode.watched),
            0,
        )
        for i, episode in enumerate(self.episodes):
            action = (
                action_for_episode(episode)
                if action_for_episode is not None
                else episode.msx_action(device_settings=device_settings)
            )
            entry = {
                "label": episode.menu_title(),
                "playerLabel": episode.player_title(),
                'action': action,
                'stamp': '{ico:check}' if episode.watched else None,
                'focus': i == focus_index,
                'properties': episode.msx_properties(device_settings=device_settings),
            }
            items.append(entry)
        return items

    def _watched(self):
        watched = True
        for episode in self.episodes:
            watched = watched and episode.watched
        return watched
