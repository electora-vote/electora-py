from typing import Dict, List

import requests
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from nucypher.characters.lawful import Bob, Ursula
from nucypher.cli.utils import connect_to_blockchain
from nucypher.policy.conditions.lingo import ConditionLingo
from nucypher.policy.conditions.types import Lingo
from nucypher.utilities.emitters import StdoutEmitter
from nucypher_core import ferveo

_RITUAL_ID = 2
_GOERLI_URI = "https://goerli.infura.io/v3/663d60ae0f504f168b362c2bda60f81c"
_COORDINATOR_URI = (
    "https://polygon-mumbai.infura.io/v3/a11313ddcf61443898b6a47e952d255c"
)
_TEACHER_URI = "https://lynx.nucypher.network:9151"
_ELECTORA_ARWEAVE_TAG = "ballot_uuid"
_ARWEAVE_GQL_ENDPOINT = "https://devnet.bundlr.network/graphql"
_ARWEAVE_DATA_ENDPOINT = "https://arweave.net/"
_ELECTION_END_TIMESTAMP = 1688028284.323  # ballot 70e4edc7c0247a40960357e23111b6b0
_GET_ELECTION_VOTES_QUERY_TEMPLATE = """
query getElectionVotes ($tagName: String!, $electionId: String!) {
    transactions(tags: [{ name: $tagName, values: [$electionId] }]) {
        edges {
            node {
                id
            }
        }
    }
}
"""

BOB = Bob(
    eth_provider_uri=_GOERLI_URI,
    domain="lynx",
    coordinator_network="mumbai",
    coordinator_provider_uri=_COORDINATOR_URI,
    known_nodes=[
        Ursula.from_teacher_uri(
            teacher_uri=_TEACHER_URI, min_stake=0, provider_uri=_GOERLI_URI
        )
    ],
)


def _fetch_vote_transactions(
    election_id: str, endpoint: str = _ARWEAVE_GQL_ENDPOINT
) -> Dict:
    """Fetches all arweave transactions tagged for a particular ballot ID."""
    transport = AIOHTTPTransport(url=endpoint)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    variables_map = {"tagName": _ELECTORA_ARWEAVE_TAG, "electionId": election_id}
    return client.execute(
        gql(_GET_ELECTION_VOTES_QUERY_TEMPLATE), variable_values=variables_map
    )


def _fetch_vote_data(transactions) -> List[str]:
    """parses gql response and fetches vote data from arweave."""
    edges = transactions["transactions"]["edges"]
    vote_ciphertexts = []
    for transaction in edges:
        transaction_id = transaction["node"]["id"]
        response = requests.get(_ARWEAVE_DATA_ENDPOINT + transaction_id)
        if response.status_code == 200:
            vote_ciphertexts.append(response.text)
        else:
            raise Exception("Could not fetch vote data from arweave")
    return vote_ciphertexts


def fetch_votes(election_id: str, endpoint: str = _ARWEAVE_GQL_ENDPOINT) -> List[str]:
    """Fetches and decrypts all valid votes for a particular election ID."""
    connect_to_blockchain(eth_provider_uri=_GOERLI_URI, emitter=StdoutEmitter())
    BOB.start_learning_loop(now=True)
    transactions = _fetch_vote_transactions(election_id=election_id, endpoint=endpoint)
    ciphertexts = _fetch_vote_data(transactions=transactions)
    return _decrypt_votes(vote_ciphertexts=ciphertexts)


def _decrypt_votes(vote_ciphertexts) -> List[str]:
    """Decrypts a single encrypted vote.

    If a vote cannot be decrypted, it is skipped.
    """
    cleartexts = []
    failed = 0
    for ciphertext in vote_ciphertexts:
        try:
            cleartext = _decrypt_vote(
                ciphertext=ciphertext, timestamp=_ELECTION_END_TIMESTAMP
            )
        except Ursula.NotEnoughUrsulas:
            failed += 1
            continue
        cleartexts.append(cleartext)
    print(f"{failed} invalid votes skipped out of {len(vote_ciphertexts)}")
    return cleartexts


def _get_conditions(timestamp: int) -> Lingo:
    time_condition = {
        "method": "blocktime",
        "chain": 5,
        "returnValueTest": {"comparator": ">=", "value": timestamp},
    }
    return {
        "version": ConditionLingo.VERSION,
        "condition": time_condition,
    }


def _decrypt_vote(ciphertext, timestamp) -> str:
    ciphertext = ferveo.Ciphertext.from_bytes(bytes.fromhex(ciphertext))
    cleartext = BOB.threshold_decrypt(
        ritual_id=_RITUAL_ID,
        ciphertext=ciphertext,
        conditions=_get_conditions(timestamp),
    )
    return bytes(cleartext).decode()


def verify_vote(vote):
    pass


def count_votes():
    pass
