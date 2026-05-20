class EmailConflict(Exception):
    pass


class UserNotFound(Exception):
    pass


class AlreadyActive(Exception):
    pass


class InvalidCode(Exception):
    pass


class ExpiredCode(Exception):
    pass
