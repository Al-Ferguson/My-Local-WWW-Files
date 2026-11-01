def application(environ, start_fn):  # noqa: ANN001, ANN201, ARG001, CPY001, D100, D103
    start_fn("200 OK", [("Content-Type", "text/plain")])
    return [b"Hello, World!\n"]
