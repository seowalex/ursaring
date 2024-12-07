from fastapi import Request


def get_http_client(request: Request):
    return request.state.http_client
