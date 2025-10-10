from datetime import datetime


def create_now() -> datetime:
    import datetime as dt

    return dt.datetime.now(dt.UTC)
