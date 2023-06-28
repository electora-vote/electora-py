from datetime import datetime

import typer

from electora_py import api

app = typer.Typer()


@app.command()
def decrypt_vote(ciphertext: str, timestamp: datetime) -> str:
    return api.decrypt_vote(ciphertext, timestamp)


if __name__ == "__main__":
    app()
