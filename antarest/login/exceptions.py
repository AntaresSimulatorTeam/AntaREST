from werkzeug import exceptions


class UserAlreadyExistError(exceptions.Conflict):
    pass
