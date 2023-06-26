from nucypher.characters.lawful import Bob, Ursula
from nucypher.cli.utils import connect_to_blockchain
from nucypher.utilities.emitters import StdoutEmitter
from nucypher_core import ferveo

_GOERLI_URI = "https://goerli.infura.io/v3/663d60ae0f504f168b362c2bda60f81c"
_TEACHER_URI = "https://lynx.nucypher.network:9151"

BOB = Bob(
    eth_provider_uri=_GOERLI_URI,
    domain="lynx",
    known_nodes=[
        Ursula.from_teacher_uri(
            teacher_uri=_TEACHER_URI, min_stake=0, provider_uri=_GOERLI_URI
        )
    ],
)


def fetch_votes():
    pass


def _get_conditions(timestamp):
    time_condition = {
        "method": "timelock",
        "returnValueTest": {"comparator": ">=", "value": timestamp},
    }
    return [time_condition]


def decrypt_vote(ciphertext, timestamp):
    connect_to_blockchain(eth_provider_uri=_GOERLI_URI, emitter=StdoutEmitter())
    BOB.start_learning_loop(now=True)
    cleartext = BOB.threshold_decrypt(
        ritual_id=0,
        ciphertext=ferveo.Ciphertext.from_bytes(bytes.fromhex(ciphertext)),
        conditions=_get_conditions(timestamp),
    )
    return bytes(cleartext).decode()


def verify_vote(vote):
    pass


def count_votes():
    pass
