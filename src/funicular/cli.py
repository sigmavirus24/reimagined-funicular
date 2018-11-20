"""Logic for the command-line portion of this code."""
import argparse
import csv
import sys
import typing

import structlog

from . import github

log = structlog.get_logger()


def build_parser() -> argparse.ArgumentParser:
    """Build an ArgumentParser."""
    parser = argparse.ArgumentParser(description="Export GitHub issues to CSV")
    parser.add_argument(
        "--app-id",
        type=int,
        help="The id for the Github App used for authentication.",
    )
    parser.add_argument(
        "--installation-id",
        type=int,
        help="The id for the installation of the GitHub App used for "
             "authentication.",
    )
    parser.add_argument(
        "--private-key-file",
        type=argparse.FileType("rb"),
        help="The file with the GitHub App's private key.",
    )
    parser.add_argument(
        "--output-file",
        type=argparse.FileType("w"),
        default=sys.stdout,
        help="The path to the output file. It will be overwritten.",
    )
    parser.add_argument(
        "--project",
        type=int,
        help="The number of the project inside your GitHub org.",
    )
    parser.add_argument(
        "--organization",
        type=str,
        help="The name of the organization housing the GitHub project.",
    )
    return parser


def github_from(arguments: argparse.Namespace) -> github.GitHub:
    """Make a GitHub object from our parsed arguments."""
    return github.GitHub(
        app_id=arguments.app_id,
        installation_id=arguments.installation_id,
        private_key_pem_bytes=arguments.private_key_file.read(),
    )


def csvwriter_from(arguments: argparse.Namespace) -> csv.DictWriter:
    """Make a CSV Writer from our arguments."""
    writer = csv.DictWriter(
        arguments.output_file,
        fieldnames=[
            "project column",
            "issue title",
            "issue description",
            "labels",
        ],
        quoting=csv.QUOTE_ALL,
    )
    writer.writeheader()
    return writer


def issue_dictionary_from(column, issue) -> dict:
    """Map issue to dictionary with field names."""
    return {
        "project column": column.name,
        "issue title": issue.title,
        "issue description": f"{issue.body}\n\n---\n\n{issue.html_url}",
        "labels": ";".join(f"'{label.name}'"
                           for label in issue.original_labels),
    }


def main(*, args: typing.List[str] = None):
    """Run our little data transfer program."""
    parser = build_parser()
    arguments = parser.parse_args()
    log.debug('args.parsed', arguments=arguments)

    gh = github_from(arguments)
    csvwriter = csvwriter_from(arguments)
    project = gh.project(organization=arguments.organization,
                         number=arguments.project)
    for column in project.columns():
        for issue in gh.issues_from(column=column):
            csvwriter.writerow(issue_dictionary_from(column, issue))
    #        log.debug("issue.found",
    #                  issue_number=issue.number,
    #                  repository=str(issue.repository),
    #                  )
    return
