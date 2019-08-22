import requests


def do_get(url, params=None, auth=None, code_ok=200):
    try:
        response = requests.get(
            url=url,
            auth=auth,
            params=params
        )
        return response
    except Exception:
        raise


def do_post(url, auth=None, data=None, params=None):
    requests.post(
        url=url,
        auth=auth,
        data=data,
        params=params
    )
