import json

import pytest
from sovrin.agent.faber import FaberAgent, AVAILABLE_CLAIMS_LIST, CLAIMS_LIST
from sovrin.client.wallet.helper import createAvailClaimListMsg, createClaimsMsg
from sovrin.test.cli.helper import getFileLines


FABER_ENDPOINT_PORT = 1212


def prompt_is(prompt):
    def x(cli):
        assert cli.currPromptText == prompt
    return x


@pytest.yield_fixture(scope="module")
def faberCLI(CliBuilder):
    yield from CliBuilder("faber")


@pytest.yield_fixture(scope="module")
def acmeCLI(CliBuilder):
    yield from CliBuilder("acme")


@pytest.fixture(scope="module")
def poolNodesStarted(be, do, poolCLI):
    be(poolCLI)

    do('new node all',                  within=6,
                                        expect=['Alpha now connected to Beta',
                                                'Alpha now connected to Gamma',
                                                'Alpha now connected to Delta',
                                                'Beta now connected to Alpha',
                                                'Beta now connected to Gamma',
                                                'Beta now connected to Delta',
                                                'Gamma now connected to Alpha',
                                                'Gamma now connected to Beta',
                                                'Gamma now connected to Delta',
                                                'Delta now connected to Alpha',
                                                'Delta now connected to Beta',
                                                'Delta now connected to Gamma'])
    return poolCLI


@pytest.fixture(scope="module")
def faberCli(be, do, faberCLI):
    be(faberCLI)

    do('prompt FABER',                  expect=prompt_is('FABER'))

    do('new keyring Faber',             expect=['New keyring Faber created',
                                                'Active keyring set to "Faber"'
                                                ])
    seed = 'Faber000000000000000000000000000'
    idr = '3W2465HP3OUPGkiNlTMl2iZ+NiMZegfUFIsl8378KH4='

    do('new key with seed ' + seed,expect=['Key created in keyring Faber',
                                           'Identifier for key is ' + idr,
                                           'Current identifier set to ' + idr])
    return faberCLI


@pytest.fixture(scope="module")
def acmeCli(be, do, acmeCLI):
    be(acmeCLI)

    do('prompt Acme',                  expect=prompt_is('Acme'))

    do('new keyring Acme',             expect=['New keyring Acme created',
                                                'Active keyring set to "Acme"'
                                                ])
    seed = 'Acme0000000000000000000000000000'
    idr = 'YSTHvR/sxdu41ig9mcqMq/DI5USQMVU4kpa6anJhot4='

    do('new key with seed ' + seed, expect=['Key created in keyring Acme',
                                           'Identifier for key is ' + idr,
                                           'Current identifier set to ' +
                                           idr])
    return acmeCLI


@pytest.fixture(scope="module")
def philCli(be, do, philCLI):
    be(philCLI)
    do('prompt Phil',                   expect=prompt_is('Phil'))

    do('new keyring Phil',              expect=['New keyring Phil created',
                                                'Active keyring set to "Phil"'])

    mapper = {
        'seed': '11111111111111111111111111111111',
        'idr': 'SAdaWX5yGhVuLgeZ3lzAxTJNxufq8c3UYlCGjsUyFd0='}
    do('new key with seed {seed}',      expect=['Key created in keyring Phil',
                                                'Identifier for key is {idr}',
                                                'Current identifier set to '
                                                '{idr}'],
       mapper=mapper)

    return philCLI


@pytest.fixture(scope="module")
def faberAddedByPhil(be, do, poolNodesStarted, philCli, connectedToTest,
                     nymAddedOut, faberMap):
    be(philCli)
    do('connect test',                  within=3,
                                        expect=connectedToTest, mapper=faberMap)

    do('send NYM dest={target} role=SPONSOR',
                                        within=3,
                                        expect=nymAddedOut, mapper=faberMap)
    return philCli


@pytest.fixture(scope="module")
def acmeAddedByPhil(be, do, poolNodesStarted, philCli, connectedToTest,
                     nymAddedOut, acmeMap):
    be(philCli)
    do('connect test',                  within=3,
                                        expect=connectedToTest, mapper=acmeMap)

    do('send NYM dest={target} role=SPONSOR',
                                        within=2,
                                        expect=nymAddedOut, mapper=acmeMap)
    return philCli


@pytest.fixture(scope="module")
def aliceCli(be, do, aliceCLI, newKeyringOut, aliceMap):
    be(aliceCLI)

    do('prompt ALICE', expect=prompt_is('ALICE'))

    do('new keyring Alice',             expect=newKeyringOut, mapper=aliceMap)
    return aliceCLI


def testNotConnected(be, do, aliceCli, notConnectedStatus):
    be(aliceCli)
    do('status',                        expect=notConnectedStatus)


def testShowInviteNotExists(be, do, aliceCli, fileNotExists, faberMap):
    be(aliceCli)
    do('show {invite-not-exists}',      expect=fileNotExists, mapper=faberMap)


def testShowFaberInvite(be, do, aliceCli, faberMap):
    be(aliceCli)
    inviteContents = getFileLines(faberMap.get("invite"))

    do('show {invite}',                 expect=inviteContents,
                                        mapper=faberMap)


def testLoadInviteNotExists(be, do, aliceCli, fileNotExists, faberMap):
    be(aliceCli)
    do('load {invite-not-exists}',      expect=fileNotExists, mapper=faberMap)


@pytest.fixture(scope="module")
def faberInviteLoadedByAlice(be, do, aliceCli, loadInviteOut, faberMap):
    be(aliceCli)
    do('load {invite}',                 expect=loadInviteOut, mapper=faberMap)
    return aliceCli


def testLoadFaberInvite(faberInviteLoadedByAlice):
    pass


def testShowLinkNotExists(be, do, aliceCli, linkNotExists, faberMap):
    be(aliceCli)
    do('show link {inviter-not-exists}',
                                        expect=linkNotExists,
                                        mapper=faberMap)


def testShowFaberLink(be, do, aliceCli, faberInviteLoadedByAlice,
                       showUnSyncedLinkOut, faberMap):
    be(aliceCli)
    do('show link {inviter}',           expect=showUnSyncedLinkOut,
                                        mapper=faberMap)


def testSyncLinkNotExists(be, do, aliceCli, linkNotExists, faberMap):
    be(aliceCli)
    do('sync {inviter-not-exists}',     expect=linkNotExists, mapper=faberMap)


def testSyncFaberWhenNotConnected(be, do, aliceCli, faberMap,
                                        faberInviteLoadedByAlice,
                                        syncWhenNotConnected):
    be(aliceCli)
    do('sync {inviter}',                expect=syncWhenNotConnected,
                                        mapper=faberMap)


def testAcceptUnSyncedFaberInviteWhenNotConnected(be, do,
                                             faberInviteLoadedByAlice,
                                             acceptUnSyncedWhenNotConnected,
                                             faberMap):
    aliceCli = faberInviteLoadedByAlice
    be(aliceCli)
    do('accept invitation from {inviter}',
                                        expect=acceptUnSyncedWhenNotConnected,
                                        mapper=faberMap)


def testAcceptUnSyncedFaberInvite(be, do, faberInviteLoadedByAlice,
                                  acceptUnSyncedWithoutEndpointWhenConnected,
                                  faberMap, connectedToTest,
                                  poolNodesStarted):
    aliceCli = faberInviteLoadedByAlice
    be(aliceCli)
    if not aliceCli ._isConnectedToAnyEnv():
        do('connect test',              within=3,
                                        expect=connectedToTest,
                                        mapper=faberMap)

    do('accept invitation from {inviter}',
                                        within=3,
                                        expect=acceptUnSyncedWithoutEndpointWhenConnected,
                                        mapper=faberMap)


@pytest.fixture(scope="module")
def faberInviteSyncedWithoutEndpoint(be, do, aliceCli, faberMap,
                                     faberInviteLoadedByAlice, poolNodesStarted,
                                     connectedToTest,
                                     syncLinkOutWithoutEndpoint):
    be(aliceCli)
    if not aliceCli._isConnectedToAnyEnv():
        do('connect test',              within=3,
                                        expect=connectedToTest,
                                        mapper=faberMap)

    do('sync {inviter}',                within=2,
                                        expect=syncLinkOutWithoutEndpoint,
                                        mapper=faberMap)
    return aliceCli


def testSyncFaberInviteWithoutEndpoint(faberInviteSyncedWithoutEndpoint):
    pass


def testShowSyncedFaberInvite(be, do, faberInviteSyncedWithoutEndpoint, faberMap,
                         linkNotYetSynced, showSyncedLinkWithoutEndpointOut):
    aliceCLI = faberInviteSyncedWithoutEndpoint

    be(aliceCLI)

    do('show link {inviter}',           expect=showSyncedLinkWithoutEndpointOut,
                                        not_expect=linkNotYetSynced,
                                        mapper=faberMap)


@pytest.fixture(scope="module")
def faberWithEndpointAdded(be, do, faberAddedByPhil, faberMap, attrAddedOut,
                           faberIsRunning):
    philCli = faberAddedByPhil
    be(philCli)
    # I had to give two open/close curly braces in raw data
    # to avoid issue in mapping
    do('send ATTRIB dest={target} raw={endpointAttr}',
    # do('send ATTRIB dest={target} raw={{"endpoint": "127.0.0.1:1212"}}',
                                        within=3,
                                        expect=attrAddedOut,
                                        mapper=faberMap)
    return philCli


def testEndpointAddedForFaber(faberWithEndpointAdded):
    pass


@pytest.fixture(scope="module")
def faberInviteSyncedWithEndpoint(be, do, faberMap,
                                  faberInviteSyncedWithoutEndpoint,
                                  faberWithEndpointAdded,
                                  syncLinkOutWithEndpoint,
                                  poolNodesStarted):
    aliceCLI = faberInviteSyncedWithoutEndpoint
    be(aliceCLI)

    do('sync {inviter}',                within=2,
                                        expect=syncLinkOutWithEndpoint,
                                        mapper=faberMap)
    return aliceCLI


def testSyncFaberInvite(faberInviteSyncedWithEndpoint):
    pass


def testShowSyncedFaberInviteWithEndpoint(be, do, faberInviteSyncedWithEndpoint,
                                     showSyncedLinkWithEndpointOut, faberMap):
    aliceCLI = faberInviteSyncedWithEndpoint
    be(aliceCLI)
    do('show link {inviter}',           expect=showSyncedLinkWithEndpointOut,
                                        mapper=faberMap)


def testAcceptNotExistsLink(be, do, aliceCli, linkNotExists, faberMap):
    be(aliceCli)
    do('accept invitation from {inviter-not-exists}',
                                        expect=linkNotExists, mapper=faberMap)


def getSignedRespMsg(msg, signer):
    signature = signer.sign(msg)
    msg["signature"] = signature
    return msg


def testAcceptInvitationResponseWithInvalidSig(faberInviteSyncedWithEndpoint,
                                 faberCli):
    aliceCli = faberInviteSyncedWithEndpoint
    aliceSigner = aliceCli.activeWallet._getIdData(
        aliceCli.activeWallet.defaultId).signer
    msg = createAvailClaimListMsg(faberCli.activeWallet.defaultId,
                                  AVAILABLE_CLAIMS_LIST)
    acceptInviteResp = getSignedRespMsg(msg, aliceSigner)
    aliceCli._handleAcceptInviteResponse(acceptInviteResp)

    assert "Signature rejected" in aliceCli.lastCmdOutput


@pytest.fixture(scope="module")
def aliceAcceptedFaberInvitation(be, do, aliceCli, faberMap, faberCli,
                                 faberLinkAdded,
                                 faberInviteSyncedWithEndpoint):
    be(aliceCli)
    do("accept invitation from {inviter}",
                                within=3,
                                mapper=faberMap,
                                expect=[
                                    "Signature accepted.",
                                    "Trust established.",
                                    "Identifier created in Sovrin.",
                                    "Available claims: Transcript"
                                    "Synchronizing...",
                                    # Once faber starts writing identifier
                                    # to Sovrin, need to uncomment below line
                                    # "Confirmed identifier written to Sovrin."
                                ])
    return aliceCli


def testAliceAcceptFaberInvitation(aliceAcceptedFaberInvitation):
    pass


def testShowFaberLinkAfterInviteAccept(be, do, faberMap, showAcceptedLinkOut,
                                  aliceAcceptedFaberInvitation):
    aliceCli = aliceAcceptedFaberInvitation
    be(aliceCli)

    do("show link {inviter}",           expect=showAcceptedLinkOut,
                                        not_expect="Link (not yet accepted)",
                                        mapper=faberMap)


def testShowClaimNotExists(be, do, faberMap, showClaimNotFoundOut,
                                   aliceAcceptedFaberInvitation):
    aliceCli = aliceAcceptedFaberInvitation
    be(aliceCli)

    do("show claim claim-to-show-not-exists",
                                        expect=showClaimNotFoundOut,
                                        mapper=faberMap)


def testShowTranscriptClaim(be, do, transcriptClaimMap, showClaimOut,
                                   aliceAcceptedFaberInvitation):
    aliceCli = aliceAcceptedFaberInvitation
    be(aliceCli)

    do("show claim {name}",
                                        expect=showClaimOut,
                                        mapper=transcriptClaimMap)


def testReqClaimNotExists(be, do, faberMap, showClaimNotFoundOut,
                                   aliceAcceptedFaberInvitation):
    aliceCli = aliceAcceptedFaberInvitation
    be(aliceCli)

    do("request claim claim-to-req-not-exists",
                                        expect=showClaimNotFoundOut,
                                        mapper=faberMap)


def testReqTranscriptClaim(be, do, transcriptClaimMap, reqClaimOut,
                                   aliceAcceptedFaberInvitation):
    aliceCli = aliceAcceptedFaberInvitation
    be(aliceCli)

    do("request claim {name}",
                                        expect=reqClaimOut,
                                        mapper=transcriptClaimMap)


def testReqClaimResponseWithInvalidSig(faberInviteSyncedWithEndpoint,
                                 faberCli):
    aliceCli = faberInviteSyncedWithEndpoint
    aliceSigner = aliceCli.activeWallet._getIdData(
        aliceCli.activeWallet.defaultId).signer

    msg = createClaimsMsg(faberCli.activeWallet.defaultId, CLAIMS_LIST)
    reqClaimResp = getSignedRespMsg(msg, aliceSigner)
    aliceCli._handleReqClaimResponse(reqClaimResp)
    assert "Signature rejected" in aliceCli.lastCmdOutput


@pytest.fixture(scope="module")
def aliceRequestedFaberTranscriptClaim(be, do, faberCli, faberLinkAdded,
                                       aliceAcceptedFaberInvitation):
    aliceCli = aliceAcceptedFaberInvitation
    be(aliceCli)
    do("request claim Transcript",      within=3,
                                        expect=[
                                            "Signature accepted.",
                                            "Received Transcript."])
    return aliceCli


def testAliceReqClaim(aliceRequestedFaberTranscriptClaim):
    pass


def testShowFaberClaimPostReqClaim(be, do, aliceRequestedFaberTranscriptClaim,
                                   transcriptClaimValueMap, rcvdClaimOut):
    aliceCli = aliceRequestedFaberTranscriptClaim
    be(aliceCli)

    do("show claim {name}",
                                        expect=rcvdClaimOut,
                                        mapper=transcriptClaimValueMap)


def testShowAcmeInvite(be, do, aliceCli, acmeMap):
    be(aliceCli)
    inviteContents = getFileLines(acmeMap.get("invite"))

    do('show {invite}',                 expect=inviteContents,
                                        mapper=acmeMap)


@pytest.fixture(scope="module")
def acmeInviteLoadedByAlice(be, do, aliceCli, loadInviteOut, acmeMap):
    be(aliceCli)
    do('load {invite}',                 expect=loadInviteOut, mapper=acmeMap)
    return aliceCli


def testLoadAcmeInvite(acmeInviteLoadedByAlice):
    pass


def testShowAcmeLink(be, do, aliceCli, acmeInviteLoadedByAlice,
                       showUnSyncedLinkOut, showLinkWithClaimReqOut, acmeMap):
    showUnSyncedLinkWithClaimReqs = \
        showUnSyncedLinkOut + showLinkWithClaimReqOut
    be(aliceCli)
    do('show link {inviter}',           expect=showUnSyncedLinkWithClaimReqs,
                                        mapper=acmeMap)


@pytest.fixture(scope="module")
def acmeAddedByPhil(be, do, poolNodesStarted, philCli, connectedToTest,
                     nymAddedOut, acmeMap):
    be(philCli)
    if not philCli._isConnectedToAnyEnv():
        do('connect test',              within=3,
                                        expect=connectedToTest, mapper=acmeMap)

    do('send NYM dest={target} role=SPONSOR',
                                        within=3,
                                        expect=nymAddedOut, mapper=acmeMap)
    return philCli


def getAcmeAcceptInviteRespMsg():
    return """{
                "type":"AVAIL_CLAIM_LIST",
                "identifier": "<identifier>",
                "availableClaimsList": [ {
                    "name": "Job-Certificate",
                    "version": "1.2",
                    "claimDefSeqNo":"<claimDefSeqNo>",
                    "definition": {
                        "attributes": {
                            "employee_name": "string",
                            "employee_status": "string",
                            "experience": "string",
                            "salary_bracket": "string"
                        }
                    }
                } ]
              }"""


@pytest.fixture(scope="module")
def aliceAcceptedAcmeJobInvitation(aliceCli, be, do,
                                   aliceRequestedFaberTranscriptClaim,
                                   acmeInviteLoadedByAlice, acmeLinkAdded,
                                   acmeMap, acmeAddedByPhil, acmeCli):
    be(aliceCli)
    do("accept invitation "
       "from {inviter}", within=3,
                         expect=["Invitation not yet verified.",
                                 "Starting communication with {inviter}"
                                 "Signature accepted.",
                                 "Trust established.",
                                 "Identifier created in Sovrin.",
                                 "Available claims: {claims}"
                                 "Synchronizing...",
                                 # Once acme starts writing identifier
                                 # to Sovrin, need to uncomment below line
                                 # "Confirmed identifier written to Sovrin."
                                 ],
                         mapper=acmeMap)
    return aliceCli


def testAliceAcceptedAcmeJobInvitation(aliceAcceptedAcmeJobInvitation):
    pass


def testShowAcmeLinkAfterInviteAccept(be, do, acmeMap,
                                      aliceAcceptedAcmeJobInvitation,
                                      showAcceptedLinkWithClaimReqsOut):
    aliceCli = aliceAcceptedAcmeJobInvitation
    be(aliceCli)

    do("show link {inviter}",           expect=showAcceptedLinkWithClaimReqsOut,
                                        not_expect="Link (not yet accepted)",
                                        mapper=acmeMap)


def testShowClaimReqNotExists(be, do, acmeMap, claimReqNotExists,
                              aliceAcceptedAcmeJobInvitation):
    aliceCli = aliceAcceptedAcmeJobInvitation
    be(aliceCli)
    do("show claim request claim-req-to-show-not-exists",
                                        expect=claimReqNotExists,
                                        mapper=acmeMap)


def testShowJobApplicationClaimReq(be, do, acmeMap, showJobAppClaimReqOut,
                                   jobApplicationClaimReqMap,
                                   transcriptClaimAttrValueMap,
                                   aliceAcceptedAcmeJobInvitation):
    aliceCli = aliceAcceptedAcmeJobInvitation
    be(aliceCli)

    mapping = {
        "set-attr-first_name": "",
        "set-attr-last_name": "",
        "set-attr-phone_number": ""
    }
    mapping.update(acmeMap)
    mapping.update(jobApplicationClaimReqMap)
    mapping.update(transcriptClaimAttrValueMap)
    do("show claim request {claim-req-to-show}",
                                        expect=showJobAppClaimReqOut,
                                        mapper=mapping)


def testSetAttrWithoutContext(be, do, faberCli):
    be(faberCli)
    do("set first_name to Alice",       expect=[
                                            "No context, "
                                            "use below command to "
                                            "set the context"])


def testShowJobApplicationClaimReqAfterSetAttr(be, do, acmeMap,
                                               showJobAppClaimReqOut,
                                               jobApplicationClaimReqMap,
                                               transcriptClaimAttrValueMap,
                                               aliceAcceptedAcmeJobInvitation):
    aliceCli = aliceAcceptedAcmeJobInvitation
    be(aliceCli)

    mapping = {
        "set-attr-first_name": "",
        "set-attr-last_name": "",
        "set-attr-phone_number": ""
    }
    mapping.update(acmeMap)
    mapping.update(jobApplicationClaimReqMap)
    mapping.update(transcriptClaimAttrValueMap)
    do("show claim request {claim-req-to-show}",
                                        expect=showJobAppClaimReqOut,
                                        mapper=mapping)
    do("set first_name to Alice")
    mapping.update({
        "set-attr-first_name": "Alice"
    })
    do("show claim request {claim-req-to-show}",
                                        expect=showJobAppClaimReqOut,
                                        mapper=mapping)
