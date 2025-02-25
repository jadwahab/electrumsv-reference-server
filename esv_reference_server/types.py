from __future__ import annotations
import dataclasses
import struct
import typing
from typing import Any, Literal, NamedTuple, Optional, TypedDict, Union

from aiohttp import web
from bitcoinx import hash_to_hex_str

from .constants import AccountMessageKind, OutboundDataFlag

if typing.TYPE_CHECKING:
    from .msg_box.models import MsgBox
    from .msg_box.types import MessageRow


# TODO Ideally these media types would be constants from some standard library.
AccountWebsocketMediaType = Union[Literal["application/json"], Literal["application/octet-stream"]]

@dataclasses.dataclass
class AccountWebsocketState:
    ws_id: str
    websocket: web.WebSocketResponse
    account_id: int
    accept_type: AccountWebsocketMediaType

    spent_output_registrations: set[Outpoint] = dataclasses.field(default_factory=set)


class HeadersWSClient(NamedTuple):
    ws_id: str
    websocket: web.WebSocketResponse


class MsgBoxWSClient(NamedTuple):
    ws_id: str
    websocket: web.WebSocketResponse
    messagebox_id: int


class Route(NamedTuple):
    aiohttp_route_def: web.RouteDef
    auth_required: bool


class WebsocketError(TypedDict):
    reason: str
    status_code: int


class EndpointInfo(NamedTuple):
    http_method: str
    url: str
    auth_required: bool


class Header(TypedDict):
    hash: str
    version: int
    prevBlockHash: str
    merkleRoot: str
    creationTimestamp: int
    difficultyTarget: int
    nonce: int
    transactionCount: int
    work: int


class NotificationJsonData(TypedDict):
    sequence: int
    received: str
    content_type: str
    channel_id: str

class HeaderSVTip(TypedDict):
    header: Header
    state: str
    chainWork: int
    height: int


class GeneralNotification(TypedDict):
    message_type: str
    result: Union[NotificationJsonData, str]


class AccountMessage(NamedTuple):
    account_id: int
    message_kind: AccountMessageKind
    message: Any



outpoint_struct = struct.Struct(">32sI")
output_spend_struct = struct.Struct(">32sI32sI32s")
tip_filter_registration_struct = struct.Struct(">32sI")
tip_filter_list_struct = struct.Struct(">32sII")


class Outpoint(NamedTuple):
    tx_hash: bytes
    output_index: int

class OutputSpend(NamedTuple):
    out_tx_hash: bytes
    out_index: int
    in_tx_hash: bytes
    in_index: int
    block_hash: Optional[bytes]

    def __repr__(self) -> str:
        return f'OutputSpend("{hash_to_hex_str(self.out_tx_hash)}", {self.out_index}, ' \
            f'"{hash_to_hex_str(self.in_tx_hash)}", {self.in_index}, ' + \
            (f'"{hash_to_hex_str(self.block_hash)}"' if self.block_hash else 'None') +')'

class TipFilterRegistrationEntry(NamedTuple):
    pushdata_hash: bytes
    duration_seconds: int

class TipFilterListEntry(NamedTuple):
    pushdata_hash: bytes
    date_created: int
    duration_seconds: int

    def __repr__(self) -> str:
        return f"TipFilterListEntry({self.pushdata_hash.hex()}, {self.date_created}, " \
            f"{self.duration_seconds})"

class AccountIndexerMetadata(NamedTuple):
    account_id: int
    tip_filter_callback_url: Optional[str]
    tip_filter_callback_token: Optional[str]


class TipFilterNotificationMatch(TypedDict):
    pushDataHashHex: str
    transactionId: str
    transactionIndex: int
    flags: int


class TipFilterNotificationEntry(TypedDict):
    accountId: int
    matches: list[TipFilterNotificationMatch]


class TipFilterNotificationBatch(TypedDict):
    blockId: Optional[str]
    entries: list[TipFilterNotificationEntry]


# This matches the structure of the same name in ElectrumSV.
class TipFilterPushDataMatchesData(TypedDict):
    blockId: Optional[str]
    matches: list[TipFilterNotificationMatch]


class OutboundDataRow(NamedTuple):
    outbound_data_id: Optional[int]
    account_id: int
    outbound_data: bytes
    outbound_data_hash: bytes
    outbound_data_flags: OutboundDataFlag
    content_type: str
    date_created: int


class OutboundDataCreatedRow(NamedTuple):
    outbound_data_id: int
    account_id: int
    outbound_data_hash: bytes


class OutboundDataPendingRow(NamedTuple):
    outbound_data_id: int
    account_id: int
    outbound_data: bytes
    outbound_data_flags: OutboundDataFlag
    content_type: str
    date_created: int
    tip_filter_callback_url: Optional[str]
    tip_filter_callback_token: Optional[str]


class OutboundDataLogRow(NamedTuple):
    account_id: int
    outbound_data_id: Optional[int]
    # We need this for when and if the `outbound_data` row is pruned.
    outbound_data_flags: OutboundDataFlag
    response_status_code: Optional[int]
    response_reason: Optional[str]
    date_created: int
