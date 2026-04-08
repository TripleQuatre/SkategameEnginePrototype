class GameError(Exception):
    pass

class InvalidActionError(GameError):
    pass

class InvalidStateError(GameError):
    pass