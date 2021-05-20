from werkzeug import exceptions


class UserAlreadyExistError(exceptions.BadRequest):
    pass
