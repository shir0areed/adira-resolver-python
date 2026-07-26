class IndexServer:
    def __init__(self, protocol_params):
        # protocol_params = {"extra_index_url": "..."} など
        self.extra_index_url = protocol_params.get("extra_index_url")

    def fetch(self, identity, output_path):
        """
        pip index 方式では、実体取得は pip がやるのでここでは何もしない。
        main.py のシグネチャに合わせるためのダミー。
        """
        return None
