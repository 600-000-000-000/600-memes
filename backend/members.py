import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

NOSTR_JSON = Path("/app/nostr.json")
MEMBERS_JSON = Path("/app/members.json")
AVATAR_BASE = "https://600.wtf/"


def load_members() -> tuple[set[str], dict[str, str], dict[str, str]]:
    """Returns (pubkey_set, pubkey_to_name, pubkey_to_avatar)."""
    try:
        # nostr.json: name → hex pubkey
        names_to_pk: dict[str, str] = {
            name: pk.lower()
            for name, pk in json.loads(NOSTR_JSON.read_text()).get("names", {}).items()
        }

        pubkey_to_name = {pk: name for name, pk in names_to_pk.items()}
        pubkey_to_avatar: dict[str, str] = {}

        # members.json: NIP-05 identifier + img path → avatar URL
        for member in json.loads(MEMBERS_JSON.read_text()).get("members", []):
            nostr_id = member.get("nostr", "")
            img = member.get("img", "")
            if "@" not in nostr_id or not img:
                continue
            nip05_name = nostr_id.split("@")[0]
            pk = names_to_pk.get(nip05_name)
            if pk:
                pubkey_to_avatar[pk] = AVATAR_BASE + img

        pubkeys = set(names_to_pk.values())
        logger.info("Loaded %d members (%d with avatars)", len(pubkeys), len(pubkey_to_avatar))
        return pubkeys, pubkey_to_name, pubkey_to_avatar

    except Exception as e:
        logger.error("Failed to load member data: %s", e)
        return set(), {}, {}
