import json
import os
import threading
from pathlib import Path


SYNC_STATE_PATH = Path(os.getenv("SYNC_STATE_PATH", "media/sync_state.json"))

_lock = threading.Lock()


def _empty_state():
    return {
        "messages": {},
        "discord_index": {}
    }


def _key(chat_id, message_id):
    return f"{chat_id}:{message_id}"


def load_state():
    with _lock:
        if not SYNC_STATE_PATH.exists():
            return _empty_state()

        try:
            with SYNC_STATE_PATH.open("r", encoding="utf-8") as state_file:
                state = json.load(state_file)
        except Exception as e:
            print("SYNC STORE READ ERROR:", e)
            return _empty_state()

        if "messages" not in state:
            state["messages"] = {}

        if "discord_index" not in state:
            state["discord_index"] = {}

        return state


def save_state(state):
    with _lock:
        try:
            SYNC_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = SYNC_STATE_PATH.with_suffix(".tmp")

            with tmp_path.open("w", encoding="utf-8") as state_file:
                json.dump(
                    state,
                    state_file,
                    ensure_ascii=False,
                    indent=2
                )

            tmp_path.replace(SYNC_STATE_PATH)

        except Exception as e:
            print("SYNC STORE WRITE ERROR:", e)


def get_message_record(chat_id, message_id):
    state = load_state()
    return state["messages"].get(_key(chat_id, message_id))


def save_message_record(record):
    state = load_state()
    telegram_key = _key(
        record["telegram_chat_id"],
        record["telegram_message_id"]
    )

    state["messages"][telegram_key] = record

    discord_message_id = record.get("discord_message_id")
    if discord_message_id:
        state["discord_index"][str(discord_message_id)] = telegram_key

    save_state(state)


def get_message_record_by_discord(discord_message_id):
    state = load_state()
    telegram_key = state["discord_index"].get(str(discord_message_id))

    if not telegram_key:
        return None

    return state["messages"].get(telegram_key)


def mark_message_deleted(chat_id, message_id, deleted_at=None):
    state = load_state()
    record = state["messages"].get(_key(chat_id, message_id))

    if not record:
        return None

    record["deleted"] = True
    record["deleted_at"] = deleted_at
    save_state(state)
    return record
