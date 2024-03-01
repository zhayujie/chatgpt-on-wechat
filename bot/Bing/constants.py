import socket
import uuid

take_ip_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
take_ip_socket.connect(("8.8.8.8", 80))
FORWARDED_IP: str = take_ip_socket.getsockname()[0]
take_ip_socket.close()


DELIMITER = "\x1e"

PLUGINS = {
    "notebook": "c310c353-b9f0-4d76-ab0d-1dd5e979cf68",
    "instacart": "46664d33-1591-4ce8-b3fb-ba1022b66c11",
    "kayak": "d6be744c-2bd9-432f-95b7-76e103946e34",
    "klarna": "5f143ea3-8c80-4efd-9515-185e83b7cf8a",
    "opentable": "543a7b1b-ebc6-46f4-be76-00c202990a1b",
    "shop": "39e3566a-d481-4d99-82b2-6d739b1e716e",
    "suno": "22b7f79d-8ea4-437e-b5fd-3e21f09f7bc1"
}

HEADERS = {
    "accept": "application/json",
    "accept-language": "en;q=0.9,en-US;q=0.8",
    "accept-encoding": "gzip, deflate, br, zsdch",
    "content-type": "application/json",
    "sec-ch-ua": '"Not A(Brand";v="99", '
                 '"Microsoft Edge";v="121", '
                 '"Chromium";v="121"',
    "sec-ch-ua-arch": '"x86"',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-full-version": '"121.0.2277.128"',
    "sec-ch-ua-full-version-list": '"Not A(Brand";v="99.0.0.0", '
                                   '"Microsoft Edge";v="121.0.2277.128", '
                                   '"Chromium";v="121.0.6167.184"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": "",
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"15.0.0"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "sec-ms-gec-version": "1-120.0.2210.133",
    "x-ms-client-request-id": str(uuid.uuid4()),
    "x-ms-useragent": "azsdk-js-api-client-factory/1.0.0-beta.1 core-rest-pipeline/1.12.3 OS/Windows",
    "Referer": "https://www.bing.com/search?form=NTPCHB&q=Bing+AI&showconv=1",
    "Referrer-Policy": "origin-when-cross-origin",
    "x-forwarded-for": FORWARDED_IP,
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                  " AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/121.0.0.0 Safari/537.36 "
                  "Edg/121.0.0.0",
}

HEADERS_INIT_CONVER = {
    "accept": "application/json",
    "accept-language": "en;q=0.9,en-US;q=0.8",
    "cache-control": "max-age=0",
    "sec-ch-ua": '"Not A(Brand";v="99", '
                 '"Microsoft Edge";v="121", '
                 '"Chromium";v="121"',
    "sec-ch-ua-arch": '"x86"',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-full-version": '"121.0.2277.128"',
    "sec-ch-ua-full-version-list": '"Not A(Brand";v="99.0.0.0", '
                                   '"Microsoft Edge";v="121.0.2277.128", '
                                   '"Chromium";v="121.0.6167.184"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": '""',
    "sec-ch-ua-platform": '"Windows"',
    "sec-ch-ua-platform-version": '"15.0.0"',
    "upgrade-insecure-requests": "1",
    "x-edge-shopping-flag": "1",
    "X-Ms-Useragent": "azsdk-js-api-client-factory/1.0.0-beta.1 core-rest-pipeline/1.12.3 OS/Windows",
    "x-forwarded-for": FORWARDED_IP,
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                  " AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/121.0.0.0 Safari/537.36 "
                  "Edg/121.0.0.0",
}

IMAGE_HEADER = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "multipart/form-data",
    "Referer": "https://www.bing.com/search?q=Bing+AI&showconv=1&FORM=hpcodx",
    "sec-ch-ua": '"Not A(Brand";v="99", '
                 '"Microsoft Edge";v="121", '
                 '"Chromium";v="121"',
    "sec-ch-ua-arch": '"x86"',
    "sec-ch-ua-bitness": '"64"',
    "sec-ch-ua-full-version": '"121.0.2277.128"',
    "sec-ch-ua-full-version-list": '"Not A(Brand";v="99.0.0.0", '
                                   '"Microsoft Edge";v="121.0.2277.128", '
                                   '"Chromium";v="121.0.6167.184"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": "Windows",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                  " AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/121.0.0.0 Safari/537.36 "
                  "Edg/121.0.0.0",
}

BUNDLE_VERSION = "1.1573.4"
APP_ID = "6c0f12ef-97d3-4869-bc42-c1d9bdb4a759"

SYDNEY_INIT_HEADER = HEADERS_INIT_CONVER.update(
    {
        "Referer": "https://copilot.microsoft.com/",
        "X-Edge-Shopping-Flag": "0",
    }
)

SYDNEY_HEADER = HEADERS.update(
    {
        "Host": "sydney.bing.com",
        "Cache-Control": "no-cache",
        "Connection": "Upgrade",
        "Origin": "https://www.bing.com",
        "Pragma": "no-cache",
    }
)
