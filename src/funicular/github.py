"""Logic for funicular to be used with GitHub."""
import urllib.parse
import re
import typing

import attr
import github3
import structlog

from . import exceptions


Organization = typing.Union[github3.orgs.Organization, str]
Project = typing.Union[github3.projects.Project, int]
Column = typing.Union[github3.projects.ProjectColumn, str]

URL_PATH_RE = re.compile(
    r"/repos/(?P<owner>[^/]+)/(?P<repository>[^/]+)/issues/(?P<number>\d+)"
)

log = structlog.get_logger()


@attr.s
class GitHub:
    """Our wrapper around github3.py."""

    app_id: int = attr.ib(converter=int)
    installation_id: int = attr.ib(converter=int)
    private_key_pem_bytes: bytes = attr.ib()
    github: github3.GitHub = attr.ib(factory=github3.GitHub)

    def __attrs_post_init__(self):
        """Login after creating our object."""
        self.login()

    def login(self):
        """Log into GitHub."""
        self.github.login_as_app_installation(
            private_key_pem=self.private_key_pem_bytes,
            app_id=self.app_id,
            installation_id=self.installation_id,
        )

    def column(self, *,
               project: Project,
               name: str,
               organization: typing.Optional[Organization] = None,
               ):
        """Retrieve a project column."""
        if isinstance(project, int):
            project = self.project(organization=organization, number=project)
        for column in project.columns():
            if column.name == name:
                return column

        raise exceptions.ColumnNotFound()

    def organization(self, *, name: str):
        """Retrieve the named organization.

        :param str name:
            The name of the organization to fetch.
        :returns:
            The organization.
        :rtype:
            :class:`github3.orgs.Organization`
        """
        return self.github.organization(name)

    def project(self, *,
                organization: Organization,
                number: int,
                ):
        """Retrieve a project by its number.

        :param organization:
            The organization housing the project.
        :type organization:
            :class:`github3.orgs.Organization`
        :param int number:
            The number of the project, e.g.,
            https://github.com/orgs/org_name/projects/11 would be 11.
        :returns:
            The associated Project.
        :rtype:
            :class:`github3.projects.Project`
        """
        if isinstance(organization, str):
            organization = self.organization(name=organization)

        for project in organization.projects():
            if project.number == number:
                return project

        raise exceptions.ProjectNotFound()

    def cards_from(self, *,
                   column: Column,
                   organization: typing.Optional[Organization] = None,
                   project: typing.Optional[Project] = None,
                   ):
        """Retrieve the cards from a project column.

        :param column:
            The column in the project to retrieve issues from.
        :param organization:
            The organization housing the project.
        :param project:
            The project to retrieve issues from if column is a string.
        :returns:
            Generator of issues.
        """
        if isinstance(column, str):
            if isinstance(project, int):
                project = self.project(organization=organization,
                                       number=project)
            column = self.column(project=project, name=column)

        for card in column.cards():
            yield card

    def issues_from(self, *,
                    column: Column,
                    organization: typing.Optional[Organization] = None,
                    project: typing.Optional[Project] = None,
                    ):
        """Retrieve the issues from a project column.

        :param column:
            The column in the project to retrieve issues from.
        :param organization:
            The organization housing the project.
        :param project:
            The project to retrieve issues from if column is a string.
        :returns:
            Generator of issues.
        """
        for card in self.cards_from(column=column,
                                    organization=organization,
                                    project=project):
            if not card.content_url:
                continue
            content_url = urllib.parse.urlparse(card.content_url)
            match = URL_PATH_RE.match(content_url.path)
            if not match:
                log.debug("Could not parse issue info from content url",
                          content_url=card.content_url,
                          parsed_path=content_url.path,
                          )
                continue
            match = match.groupdict()
            owner = match.get('owner')
            repository = match.get('repository')
            number = int(match.get('number'))
            issue = self.github.issue(owner, repository, number)
            yield issue
