"""
CLI entry point for GenQuery.

Allows quick experimentation from the command line:

    genquery "Show me all users" --conn sqlite:///mydb.db
    genquery "List top 10 orders" --conn postgresql://user:pass@localhost/db --model gpt-5.5
    genquery "Find recent orders" --conn sqlite:///mydb.db --base-url http://localhost:8080/v1
"""
import argparse
import os
import sys

from genquery import GenQuery
from genquery.adapters.openai_adapter import OpenAIAdapter
from genquery.logging import configure_logging, get_logger

logger = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GenQuery - AI-driven SQL query generation from natural language"
    )
    parser.add_argument("query", help="Natural language query to execute against the database")
    parser.add_argument(
        "--conn",
        required=True,
        help="Database connection string (e.g., sqlite:///my.db, postgresql://user:pass@localhost/db)",
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("OPENAI_API_KEY"),
        help="OpenAI API key (defaults to OPENAI_API_KEY environment variable)",
    )
    parser.add_argument(
        "--model",
        default="gpt-5.5",
        help="OpenAI model to use (default: gpt-5.5)",
    )
    parser.add_argument(
        "--base-url",
        default="https://api.openai.com/v1",
        help="Base URL for the OpenAI-compatible API (default: https://api.openai.com/v1). "
             "Useful for local proxies, self-hosted models, or alternative providers.",
    )
    parser.add_argument(
        "--schema",
        default="public",
        help="Database schema to use (default: public)",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to a YAML configuration file",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "debug", "info", "warning", "warn", "error", "critical"],
        help="Log level (default: INFO, or value from config file)",
    )

    args = parser.parse_args()

    configure_logging(args.log_level or "INFO")

    if not args.api_key:
        logger.error("OpenAI API key is required")
        print("Error: OpenAI API key is required. Provide it via --api-key or set the OPENAI_API_KEY environment variable.", file=sys.stderr)
        sys.exit(1)

    try:
        llm = OpenAIAdapter(api_key=args.api_key, model=args.model, base_url=args.base_url)
        gq = GenQuery(
            llm=llm,
            connection_string=args.conn,
            schema=args.schema,
            config_path=args.config,
            log_level=args.log_level,
        )
        df = gq.run(args.query)
        print(df)
    except Exception as e:
        logger.exception("CLI execution failed")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()