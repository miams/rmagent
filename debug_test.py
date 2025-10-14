#!/usr/bin/env python3
"""Debug script to test CLI commands."""
import sys

from click.testing import CliRunner

from rmagent.cli.main import cli


def main():
    runner = CliRunner()
    result = runner.invoke(cli, ["--database", "data/Iiams.rmtree", "bio", "1", "--no-ai"])

    print(f"Exit code: {result.exit_code}")
    print(f"Output: {result.output}")
    if result.exception:
        print(f"Exception: {result.exception}")
        import traceback

        traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)

    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
