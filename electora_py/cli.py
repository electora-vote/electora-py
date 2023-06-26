from datetime import datetime

import typer

import api

app = typer.Typer()


@app.command()
def decrypt_vote(ciphertext: str, timestamp: datetime) -> str:
    print(api.decrypt_vote(ciphertext, timestamp))


if __name__ == "__main__":
    app()
