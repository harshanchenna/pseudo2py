"""CLI entry point for pseudo2py."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from pseudo2py.agent import run
from pseudo2py.config import (
    ConfigError,
    init_config,
    load_config,
    validate_config,
)

console = Console(stderr=True)
output_console = Console()


class PseudoGroup(click.Group):
    """Custom group that treats unknown args as pseudocode input."""

    def parse_args(self, ctx, args):
        # If first arg looks like a subcommand, let Click route it.
        if args and args[0] in self.commands:
            return super().parse_args(ctx, args)
        # Otherwise, collect all non-option args as pseudocode.
        # Split into options and positional words.
        opts = []
        positional = []
        i = 0
        while i < len(args):
            if args[i].startswith("-"):
                opts.append(args[i])
                # If it's not a flag, consume the next arg as option value.
                if args[i] in ("-f", "--file", "-o", "--output", "-c", "--config"):
                    if i + 1 < len(args):
                        opts.append(args[i + 1])
                        i += 2
                        continue
                i += 1
            else:
                positional.append(args[i])
                i += 1
        ctx.params["_pseudocode"] = " ".join(positional) if positional else None
        return super().parse_args(ctx, opts)


@click.group(cls=PseudoGroup, invoke_without_command=True)
@click.option("-f", "--file", "input_file", type=click.Path(exists=True), help="Read pseudocode from file.")
@click.option("-o", "--output", "output_path", help="Override output filename.")
@click.option("-c", "--config", "config_path", type=click.Path(), help="Config file path.")
@click.option("--no-save", is_flag=True, help="Print code only, don't save files.")
@click.option("-q", "--quiet", is_flag=True, help="Output code only, no progress or formatting.")
@click.pass_context
def main(ctx, input_file, output_path, config_path, no_save, quiet):
    """Convert pseudocode to runnable Python.

    Pass pseudocode as an argument, via -f FILE, or pipe through stdin.

    \b
    Examples:
        pseudo2py "sort a list of dicts by age"
        pseudo2py -f sketch.txt
        echo "read a csv and plot it" | pseudo2py
        pseudo2py init
    """
    if ctx.invoked_subcommand is not None:
        return

    pseudocode = ctx.params.get("_pseudocode")
    text = _get_input(pseudocode, input_file)
    if not text:
        click.echo(ctx.get_help())
        ctx.exit(0)
        return

    # Load config.
    cfg_path = Path(config_path) if config_path else None
    try:
        config = load_config(cfg_path)
        validate_config(config)
    except ConfigError as e:
        if quiet:
            click.echo(f"Error: {e}", err=True)
        else:
            console.print(f"[red]Config error:[/red] {e}")
        ctx.exit(2)
        return

    # Run agent.
    if not quiet:
        console.print(Panel.fit("[bold]pseudo2py[/bold]", border_style="dim"))

    def on_search(query: str) -> None:
        if not quiet:
            console.print(f"  [dim]Searching:[/dim] {query}")

    if not quiet:
        with console.status("[dim]Generating code...[/dim]"):
            result = run(text, config, on_search=on_search)
    else:
        result = run(text, config)

    if not result.code:
        if quiet:
            click.echo("Error: No code generated.", err=True)
        else:
            console.print("[red]No code generated.[/red]")
        ctx.exit(1)
        return

    if not result.valid:
        if not quiet:
            console.print(f"[yellow]Warning:[/yellow] Generated code has syntax errors: {result.error}")

    # Output.
    filename = output_path or result.filename

    if quiet:
        click.echo(result.code)
    else:
        syntax = Syntax(result.code, "python", theme="monokai", line_numbers=True)
        output_console.print(syntax)

    # Save files.
    if not no_save:
        save_dir = Path(config.output.save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        code_path = save_dir / filename
        code_path.write_text(result.code + "\n")

        if not quiet:
            console.print(f"\n  [green]Saved:[/green] {code_path}")

        if result.requirements:
            req_path = save_dir / "requirements.txt"
            req_path.write_text("\n".join(result.requirements) + "\n")
            if not quiet:
                reqs_str = ", ".join(result.requirements)
                console.print(f"  [green]Saved:[/green] {req_path} ({reqs_str})")


@main.command()
@click.option("-c", "--config", "config_path", type=click.Path(), help="Config file path.")
def init(config_path):
    """Initialize a config file with defaults."""
    path = Path(config_path) if config_path else None
    result = init_config(path)
    console.print(f"[green]Config written to:[/green] {result}")
    console.print("Edit it to set your LLM endpoint and model.")


def _get_input(pseudocode: str | None, input_file: str | None) -> str:
    """Resolve input from argument, file, or stdin."""
    if pseudocode:
        return pseudocode
    if input_file:
        return Path(input_file).read_text().strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""
