import os


def get_proxy(proxy: str = None):
    proxy = (
            proxy
            or os.environ.get("all_proxy")
            or os.environ.get("ALL_PROXY")
            or os.environ.get("https_proxy")
            or os.environ.get("HTTPS_PROXY")
            or None
    )
    if proxy is not None and proxy.startswith("socks5h://"):
        proxy = "socks5://" + proxy[len("socks5h://"):]
    return proxy
