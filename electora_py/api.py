from typing import Dict, List

import requests
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from javascript import require, eval_js
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

_TEST_COMPRESSED_PROOF = "3000000000000000b23f64076fef2a9870f7704c13a40ee5114434f996389cd860ba15774c060db107bd03c92baa0d207bd2e8f3b090d5066000000000000000ae2630d00019c35fd9dbf9cc2a90ca9dbc3804e38b568d210bf224b4212f5237a9db9c185114190024b55c5a9be1a7b601aea246307fc7d3cf5a1a577b1146026a28709ccced470761d18e75b3a378ece786a1d719ee4b1f62e45a776d4d29358c04000000000000f515fdafc4b6441939b2c7cc5013163c79dca7e2050895e14a01179e915fadcf2e2c7f8ccd5dbfebd6a32a7194fe4cb5b8a178819f5a1d3e265274a37fe6966ca29eaf7f6bb6199fff32ce9b4eba1fd8fb4d5a7aa2fd3b59d1b00ffa99ecc565fc6e9ca802b892f00d67088cd24673f315002bfc11161c834e0c27633fd5e12f01b29534283235e87657e3b08620f3abc248b08c8f2e149412f0d7c17c3f3f632d11f74c1643c330bbe7a6cd080e25b851daab189a9be0b4430444a696e58776c16b591aa35371bdc6a57b48d0431fe4de1c3ee1a1f5943deb2bcde2457178b8650bde0ec6e1157562b44793f5d582a3607cb1139813b4d4920659c33ec060bf38195ee0ddcf51d1534947b4c1d4e0579ceb5bc50e6ca1d2eb568804a0b5bfde2f66e161abf5731f6523f5acbc0b40f6589419459b48c0d0e97b35b2f0596e46fdd53baf1b7e75e6534f3823c7babb53ac0c73dd44477b95e8415a464c2ccd6a9eb0fd47a5f51da70bcd3ac039d1078aff34b882dff1bff3fd691a0ff20a648cebec7dcdb78944151d13ba46c21e7ce279c0630520d46426582f3ebb71dffaa51cd260aa58a551701359508b7dd5d3d61fd8c03a6b3b1cc15a1ba122ba13daf316eafeb1842153428f8050791b3f16e89b6f3158e488a3963cf6e28c7d02790df88eab968e9f079fd1756677d461a9eb7847fc5880215ca69c5da4f8ac1dddab76e7ff2a5e5302f45ca31af78f4300755e84d677a007feb9a736bb97d96a8885c70ca686f9f4e13d61d342296252869182d985ac1182d0839016b1fbbe3a87b91b57bafbb2dc398e3b255d1313f9afdb7f52773271c1e7539eb3f8992570a9ec1a0a02b086bc6b28a0b97429ad377b05b0e5ad72e321a0bd46f75b7eaba3fb8d1d6c9413846143ec4b255999da59c572ceb826250c7c116073dff162fdc0010256d57e66143cffbd30679c662715f5f3239a039fb0394b6d534ed682bde4e5601f609447b8e2d108a4be9fecb4b5e66cf69eea18ded9638b268c811b59f9a7adca7b616a47b92dd72c2557e537c9e4abca6d5dde4c90846609653679121229840afbaea052b3c017efe46ee798c55ba5a3c8f8b766728f3402c61aa8bf504abe12ccf677b06a1d673671409eaf437c28c2197574628427765965ecfb1c4620a12efc37bd73e76ff0736dc4056a09bc62f8d3dce26f2aacec0f6acc55ecce640c7315f6b81f9e29a05cdca0cfe6d9a5af42261ffd220af6024adf65995b79b9ed2c6c7cb1eacd8b38daf337f658b72855debbf0611d1f3b4dcf519b0d45a609c5b90ca4e15c2efea526ced305da29224f159e9dbe20a52a11ab774aec53ebfb697f274c824a32ef533bca6443fcd162b58fcc49461a1eb231c821d287006d804ba8ad98bee78be139fe0e5e6eee67eb59a144590c9c6df1b77c4604e2b0726393b510b7407f5eb2475006970dabe6eca9440b3fe3c663ba35a9c8f82dcf5fe00f5c8f8f9f183f194ae2a2ebd3ee6e9258f068b44288244f325bd2537b2e432dfb5846fcaaf240ff77db5c6d8cbc68fc310d81b1dd30a2aa4ab7e09ce87810b6d4ec0c702a29edeb830686cdc5728ddc2e859b7a5ff99630ef58c745654a406f5cb1e4bfeef7addea28ecd66cc"

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


def verify_proof(compressed_response: str) -> bool:
    sismo_server = require("@sismo-core/sismo-connect-server", '0.0.11')
    sismo_client = require("@sismo-core/sismo-connect-client", '0.0.11')
    pako = require("pako")
    js_base64 = require("js-base64")
    config = {"appId": _SISMO_APP_ID}
    connection = sismo_server.SismoConnect({"config": config})
    ungzip = pako.ungzip
    toUint8Array = js_base64.toUint8Array
    claims = [{ "groupId": "0xd65c6f4a9defb6ee9cc90eb344a170e5"}]
    print(toUint8Array(compressed_response))
    uncompressed_response = ungzip(toUint8Array(compressed_response))
    # response = await sismo.SismoConnectResponse(proof, 1)
    # result = await connection.verify(response)
    # # uncompressed_response = sismo_client.unCompressResponse(compressed_response)
    # uncompressed_response = eval_js('''
    #     import { ungzip } from 'pako'
    #     import { toUint8Array } from 'js-base64'
    #     ungzip(toUint8Array(data), { to: 'string' })
    # ''')
    print(uncompressed_response)
    result = eval_js(''' await connection.verify(uncompressed_response, claims) ''')
    return result


_test = verify_proof(_TEST_COMPRESSED_PROOF)
assert _test is None


def count_votes():
    pass
