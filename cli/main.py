import typer
from config.settings import initialize_directories
from utils.logger import logger
from core.engine import Engine


app = typer.Typer(
    help="TCAF - Telecom Compliance Automation Framework"
)

@app.command()
def run(
    clause: str = typer.Option(None, "--clause", help="Run a specific clause"),
    section: str = typer.Option(None, "--section", help="Run a section of clauses"),
):
    initialize_directories()
    
    logger.info("TCAF CLI started")
    
    ssh_command = input("Enter SSH command to connect to DUT: ")
    
    engine = Engine(
        clause=clause,
        section=section,
        ssh_command=ssh_command
    )

    engine.start()

def main():
    app()


if __name__ == "__main__":
    main()