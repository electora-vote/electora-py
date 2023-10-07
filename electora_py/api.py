import json
from typing import Dict, List

import requests
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from javascript import require  # type: ignore
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
_SISMO_APP_ID = "0x022828235eed6dc1978b239bdd735bae"

_TEST_COMPRESSED_PROOF = "H4sIAAAAAAAAA8VVvY5eRwh9l6-2IxhmBnAZpUltp4pcAAP2Svun_daWLcvvHjZypEgpXeTe5oph4MA5cL9d7PHx93N5c4EvMIb0Syvz7BOoLD5I_Rym5ZaXV5d7u8vro0X2hTu7uW_T53y63jzct-F6c717eB0P9_cZz68_Yx8-Pj081PXy5s9vl7i1m7t_fb77-thR4NXlw9PDp38gnL1i1zQ9Wb4zNUIhneY0ZMh1-eH-7qZxPNvdY9-6tef-fkFit586JL665JfnJ_vNnq2P--Dm-jZvG5P5bf769Y9rPl3elN1e8_v7HxB_-MKXYVhHKkqP-do5I9Y-CLsgxQqBeKCFVxb7WVQHsg3tsXBpHpCxvauY3UEO8EV0CsA4OAKdUL3rItt0gjhlzJgsylNDcroPXk5qmCNwEmjnn5MhiHair3aB0amXSDJLuNQCDJ_Y2Safjl8NMvjMHWiSyHimEdhcChwDuXSSjqVEWl2cuBBhhlHniDnGnI0Yj6WfjgKwjYfuiVNogJBJ2SkdsDVWHN-4Nuvua6kADmu-pICzJY5o1LasUyJCweAcrt5hrctMWrOJjUNZWzfjDK0hB1DGgTWS8MR50QN44-wwrUOWxZu8NoNKkHZ92321dSQqrnEOVpe-hkidgVtFeG4vhxLovp-VUhxbUo0dtCbE1obJx6Kj_t8PN_q1caQv7gGUVkfr42SEw45WoWNjn4szbSpYa2HqGErahHnzwtB8yFyrWcijSiVdmQCv6raQMImNVRDavTaFFXCqNY_SbTB0axFVa7PWaNEMskSM4RBtGwlNJCen7eSm8oW8LX1POKGoG-qYAEiOYgHtvUe16Ox0Yd660k1yas8z2GDt4nlw9KSNGGXRCnNkbzF6rezN01IU78HBmqiHe8AOM6qtF1rFW-nHbI8RSl1NC_gnu48tQqfFDbRbuie7CxcfpV5FUD2IrnhokvS40nErYBnqQPX387P5AYta8DY6AQ2XUWejkvg2SmcENu3VklSuqp6NybOsCKr3hCzHFatxrp49mL0JhuoZMJCMJXNDL5_VB3RQeqd7aE9Hj910PGND_jT8nw1w-c_y7v38-eb-w9v4mHcvv52PX8-Tvb6OX_Dy_f33vwBmwIwSwAYAAA"  # noqa: E501
_TEST_GROUP_ID = "0xd65c6f4a9defb6ee9cc90eb344a170e5"

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
    result = client.execute(
        gql(_GET_ELECTION_VOTES_QUERY_TEMPLATE), variable_values=variables_map
    )
    return result


def _fetch_vote_data(transactions) -> List[str]:
    """parses gql response and fetches vote data from arweave."""
    edges = transactions["transactions"]["edges"]
    vote_ciphertexts = list()
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
    cleartexts = _decrypt_votes(vote_ciphertexts=ciphertexts)
    return cleartexts


def _decrypt_votes(vote_ciphertexts) -> List[str]:
    """Decrypts a single encrypted vote.

    If a vote cannot be decrypted, it is skipped.
    """
    cleartexts = list()
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
    conditions = {
        "version": ConditionLingo.VERSION,
        "condition": time_condition,
    }
    return conditions


def _decrypt_vote(ciphertext, timestamp) -> str:
    ciphertext = ferveo.Ciphertext.from_bytes(bytes.fromhex(ciphertext))
    cleartext = BOB.threshold_decrypt(
        ritual_id=_RITUAL_ID,
        ciphertext=ciphertext,
        conditions=_get_conditions(timestamp),
    )
    return bytes(cleartext).decode()


def verify_proof(compressed_response: str, group_id: str) -> bool:
    sismo_server = require("@sismo-core/sismo-connect-server", "0.0.11")
    pako = require("pako")
    js_base64 = require("js-base64")
    config = {"appId": _SISMO_APP_ID}
    connection = sismo_server.SismoConnect(config)
    ungzip = pako.ungzip
    toUint8Array = js_base64.toUint8Array
    uncompressed_response = json.loads(
        ungzip(toUint8Array(compressed_response), {"to": "string"})
    )
    print(uncompressed_response)
    result = connection.verify(
        uncompressed_response,
        {"claims": [{"groupId": group_id}]},
    )
    return result


_test = verify_proof(_TEST_COMPRESSED_PROOF, _TEST_GROUP_ID)
print(_test)


def count_votes():
    pass
