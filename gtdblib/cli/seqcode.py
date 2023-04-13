import typer

from gtdblib.seqcode.update import seqcode_update

app = typer.Typer()


@app.command()
def update(
        from_id: int = typer.Option(
            1,
            min=1,
            help='The minimum SeqCode number in search range'
        ),
        to_id: int = typer.Option(
            1,
            min=1,
            help='The maximum SeqCode number in search range.'
        ),
        batch_size: int = typer.Option(
            1,
            min=1,
            help='The number of batches between SQL update operations.'
        ),
        cpus: int = typer.Option(
            1,
            min=1,
            help='The number of CPUs to use.'
        ),
):
    """
    Update the SeqCode database with the latest data.
    """
    seqcode_update(from_id, to_id, batch_size, cpus)
