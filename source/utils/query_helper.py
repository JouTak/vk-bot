from mcipc.query import Client


class MinecraftServerQuery:
    def __init__(self, host='joutak', port=25611):
        self.host = host
        self.port = port

    def get_info(self):
        with Client(self.host, self.port) as client:
            stats = client.stats(full=True)
            # plugins = stats['plugins']
            # num_players = stats['num_players']
            players = stats['players']
            version = stats['version']
            return players, version

    def get_dummy_info(self):
        host, port = self.host, self.port
        players = ['EnderDissa', 'Zve1223']
        version = '1.21.5'
        return players, version
