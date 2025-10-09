"""Ask command - Interactive Q&A about the database."""

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt

from rmagent.agent.genealogy_agent import GenealogyAgent

console = Console()


@click.command()
@click.argument('question', required=False)
@click.option(
    '--interactive',
    '-i',
    is_flag=True,
    help='Interactive conversation mode',
)
@click.pass_obj
def ask(ctx, question: str, interactive: bool):
    """
    Ask questions about the database.

    \b
    Examples:
        rmagent ask "Who were John Smith's parents?"
        rmagent ask "How many people born in Maryland?"
        rmagent ask --interactive  # Start conversation mode
    """
    try:
        config = ctx.load_config()
        agent = GenealogyAgent(
            db=ctx.get_database(),
            llm_provider=config.build_provider(),
        )

        if interactive:
            # Interactive conversation mode
            console.print("\n[bold]Interactive Q&A Mode[/bold]")
            console.print("Type 'exit' or 'quit' to end the conversation\n")

            conversation_history = []

            while True:
                # Get question from user
                user_question = Prompt.ask("[cyan]Question[/cyan]")

                if user_question.lower() in ['exit', 'quit', 'q']:
                    console.print("\n[dim]Goodbye![/dim]")
                    break

                # Get answer from agent
                with console.status("[dim]Thinking...[/dim]"):
                    answer = agent.ask(user_question, context=conversation_history)

                # Display answer
                console.print()
                console.print(Markdown(answer))
                console.print()

                # Add to conversation history
                conversation_history.append({
                    'question': user_question,
                    'answer': answer,
                })

        else:
            # Single question mode
            if not question:
                console.print("[red]Error:[/red] Please provide a question or use --interactive")
                raise click.Abort()

            # Get answer from agent
            with console.status("[dim]Searching database...[/dim]"):
                answer = agent.ask(question)

            # Display answer
            console.print()
            console.print(Markdown(answer))
            console.print()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        if ctx.verbose:
            console.print_exception()
        raise click.Abort()
