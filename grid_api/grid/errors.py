"""Errors raised by the grid. Every message is short and safe to show to the user as is."""


class GridError(Exception):
    status_code = 400


class InvalidConfig(GridError, ValueError):
    status_code = 400


class InvalidNode(GridError):
    status_code = 400


class InvalidMove(GridError):
    status_code = 400


class UnknownAgent(GridError):
    status_code = 404


class MissionFinished(GridError):
    status_code = 409


class NotInitialized(GridError):
    status_code = 409