# main.py

import typer
from typing import Optional
from src.agents.data_loader_agent import DataLoaderAgent, DataLoaderAgentConfig
from src.agents.research_agent import ResearchAgent, ResearchAgentConfig
from src.agents.qa_agent import QualityAssuranceAgent, QAAgentConfig
from dotenv import load_dotenv
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()

app = typer.Typer(help="Atomic RAG System - Multi-agent PDF search system")
console = Console()


@app.command()
def load(
    pdf_dir: str = typer.Option(
        "./data/pdfs", "--pdf-dir", help="Directory containing PDF files"
    )
):
    """Load and process PDF documents"""
    console.print(Panel("🔄 Initializing Data Loader Agent...", style="blue"))

    try:
        # Initialize Data Loader Agent
        loader_config = DataLoaderAgentConfig(pdf_directory=pdf_dir)
        loader_agent = DataLoaderAgent(loader_config)

        # Process all PDFs
        console.print(Panel("📄 Processing PDFs...", style="blue"))
        results = loader_agent.process_directory()

        # Display results
        table = Table(title="Processing Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Total PDFs", str(results["total_pdfs"]))
        table.add_row("Successful", str(results["successful"]))
        table.add_row("Failed", str(results["failed"]))

        console.print(table)

        if results["failed"] > 0:
            console.print("\n⚠️  Some PDFs failed to process:")
            for detail in results["details"]:
                if "error" in detail:
                    console.print(f"   - {detail['pdf']}: {detail['error']}")

        console.print(Panel("✅ Processing complete!", style="green"))

    except Exception as e:
        console.print(Panel(f"❌ Error: {e}", style="red"))
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    pdf_dir: str = typer.Option(
        "./data/pdfs", "--pdf-dir", help="Directory containing PDF files"
    ),
):
    """Search for information in processed documents"""
    console.print(Panel(f"🔍 Searching for: {query}", style="blue"))

    try:
        # Initialize Research Agent
        research_config = ResearchAgentConfig()
        research_agent = ResearchAgent(research_config)

        # Execute search
        search_results = research_agent.search(query)

        # Initialize QA Agent
        qa_config = QAAgentConfig()
        qa_agent = QualityAssuranceAgent(qa_config)

        # Generate answer
        console.print(Panel("💡 Generating answer...", style="blue"))
        answer = qa_agent.generate_answer(query, search_results)

        # Display results
        console.print(Panel(f"Query: {answer['query']}", style="bold blue"))
        
        # Show translation info if applicable
        if answer.get("translation_needed"):
            console.print(f"[yellow]Language detected: {answer['detected_language']}[/yellow]")
            console.print(f"[yellow]Translated query: {answer['english_query']}[/yellow]")
        
        console.print(Panel(answer["answer"], style="white"))

        # Display metadata
        table = Table(title="Answer Metadata")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("Confidence", f"{answer['confidence_score']:.2%}")
        table.add_row("Completeness", f"{answer['completeness_score']:.2%}")
        table.add_row("Accuracy", f"{answer['accuracy_score']:.2%}")
        table.add_row("Sources Used", str(answer["sources_used"]))
        table.add_row("Search Strategy", answer["metadata"]["search_strategy"])

        console.print(table)

        if answer.get("warnings"):
            console.print("\n⚠️  Warnings:")
            for warning in answer["warnings"]:
                console.print(f"   - {warning}")

    except Exception as e:
        console.print(Panel(f"❌ Error: {e}", style="red"))
        raise typer.Exit(1)


@app.command()
def test():
    """Run test queries"""
    console.print(Panel("🧪 Running test queries...", style="blue"))

    # Test queries from requirements
    test_queries = [
        "Was ist die Farbtemperatur von SIRIUS HRI 330W 2/CS 1/SKU?",
        "Welche Leuchten sind gut für die Ausstattung im Operationssaal geeignet?",
        "Gebe mir alle Leuchtmittel mit mindestens 1000 Watt und Lebensdauer von mehr als 400 Stunden.",
        "Welche Leuchte hat die primäre Erzeugnisnummer 4062172212311?",
    ]

    try:
        research_agent = ResearchAgent(ResearchAgentConfig())
        qa_agent = QualityAssuranceAgent(QAAgentConfig())

        for i, query in enumerate(test_queries, 1):
            console.print(Panel(f"TEST {i}/4: {query}", style="bold yellow"))

            search_results = research_agent.search(query)
            answer = qa_agent.generate_answer(query, search_results)

            # Show translation info if applicable
            if answer.get("translation_needed"):
                console.print(f"[yellow]Language detected: {answer['detected_language']}[/yellow]")
                console.print(f"[yellow]Translated query: {answer['english_query']}[/yellow]")

            console.print(Panel(answer["answer"], style="white"))
            console.print(f"✓ Confidence: {answer['confidence_score']:.2%}")
            console.print("")

        console.print(Panel("✅ All tests completed!", style="green"))

    except Exception as e:
        console.print(Panel(f"❌ Error: {e}", style="red"))
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
