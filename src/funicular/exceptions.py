"""Exceptions raised by our funicular package."""


class FunicularException(Exception):
    """Base Funicular Exception."""

    pass


class NotFound(FunicularException):
    """Something could not be found."""

    pass


class ProjectNotFound(NotFound):
    """Could not find the project from which we want to extract."""

    pass


class ColumnNotFound(NotFound):
    """Could not find the project column."""

    pass
