import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_path: str
    batch_size: int
    scryfall_timeout_seconds: int
    scryfall_update_interval_hours: int
    log_level: str

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(
            data_path=os.getenv("DATA_PATH", "/app/data"),
            batch_size=_read_int("BATCH_SIZE", 5),
            scryfall_timeout_seconds=_read_int("SCRYFALL_TIMEOUT_SECONDS", 30),
            scryfall_update_interval_hours=_read_int("SCRYFALL_UPDATE_INTERVAL_HOURS", 24),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    @property
    def data_directory(self) -> Path:
        return Path(self.data_path)


def _read_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default

    value = int(raw_value)
    if value < 1:
        raise ValueError(f"{name} must be a positive integer.")
    return value
