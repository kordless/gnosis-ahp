import click
import httpx
from .config import set_config_value, get_config_value
from .client import AHPClient

@click.group()
@click.pass_context
def cli(ctx):
    """A CLI client for the Agentic Hypercall Protocol (AHP) server."""
    try:
        ctx.obj = AHPClient()
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        # Allow configure command to run even if client fails to init
        if ctx.invoked_subcommand != "configure":
            ctx.exit(1)

@cli.command()
@click.option("--server-url", help="The URL of the AHP server.")
@click.option("--ahp-token", help="The pre-shared key for the AHP server.")
def configure(server_url, ahp_token):
    """Configure the CLI client."""
    if server_url:
        set_config_value("server_url", server_url)
        click.echo(f"Server URL set to: {server_url}")
    if ahp_token:
        set_config_value("ahp_token", ahp_token)
        click.echo("AHP token has been set.")
    
    if not server_url and not ahp_token:
        click.echo("Please provide either --server-url or --ahp-token.")

@cli.command()
@click.argument("url")
@click.pass_context
def execute(ctx, url):
    """Execute a raw AHP URL."""
    client = ctx.obj
    try:
        # We need to parse the URL and extract the params
        # For now, we assume the URL is just the path and query string
        # and we use the configured base URL.
        response = client.http_client.get(url)
        response.raise_for_status()
        click.echo(response.text)
    except httpx.HTTPStatusError as e:
        click.echo(f"Error: {e.response.text}", err=True)
        ctx.exit(1)
    except httpx.RequestError as e:
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)

def create_tool_command(tool_name: str, tool_schema: dict):
    """Dynamically creates a click command for a tool."""
    @click.command(name=tool_name, help=tool_schema.get("description", ""))
    @click.pass_context
    def tool_command(ctx, **kwargs):
        client = ctx.obj
        try:
            result = client.execute_tool(tool_name, **kwargs)
            click.echo(result)
        except httpx.HTTPStatusError as e:
            click.echo(f"Error: {e.response.text}", err=True)
            ctx.exit(1)

    # Add parameters to the command
    params = tool_schema.get("parameters", {}).get("properties", {})
    for param_name, param_schema in params.items():
        option_name = f"--{param_name.replace('_', '-')}"
        option_kwargs = {
            "help": param_schema.get("description", ""),
            "type": str, # For simplicity, treat all as strings for now
        }
        click.option(option_name, **option_kwargs)(tool_command)
        
    return tool_command

def load_dynamic_commands():
    """Loads tool commands dynamically from the server."""
    server_url = get_config_value("server_url")
    if not server_url:
        return

    try:
        client = AHPClient(server_url)
        tools = client.get_tools()

        for tool_schema in tools:
            tool_name = tool_schema.get("name")
            if tool_name:
                cli.add_command(create_tool_command(tool_name, tool_schema))

    except (httpx.RequestError, ValueError) as e:
        # Silently fail if server is not available, but print a warning.
        # The CLI can still be used for configuration.
        # click.echo(f"Warning: Could not connect to server to load tools: {e}", err=True)
        pass

load_dynamic_commands()


if __name__ == "__main__":
    cli()
