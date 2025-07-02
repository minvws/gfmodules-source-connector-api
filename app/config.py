import configparser
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, ValidationError

_PATH = "app.conf"
_CONFIG = None


class LogLevel(str, Enum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"
    critical = "critical"


class ConfigApp(BaseModel):
    loglevel: LogLevel = Field(default=LogLevel.info)


class ConfigUvicorn(BaseModel):
    swagger_enabled: bool = Field(default=False)
    docs_url: str = Field(default="/docs")
    redoc_url: str = Field(default="/redoc")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8520, gt=0, lt=65535)
    reload: bool = Field(default=True)
    reload_delay: float = Field(default=1)
    reload_dirs: list[str] = Field(default=["app"])
    use_ssl: bool = Field(default=False)
    ssl_base_dir: str | None = Field(default=None)
    ssl_cert_file: str | None = Field(default=None)
    ssl_key_file: str | None = Field(default=None)


class ConfigRateLimiter(BaseModel):
    enabled: bool = Field(default=False)
    redis_host: str | None = Field(default=None)
    redis_port: int | None = Field(default=None, ge=0, lt=65535)
    redis_db: int = Field(default=0, ge=0)
    default_reqs: int = Field(default=100, gt=0)
    default_window: int = Field(default=60, gt=0)


class ConfigTelemetry(BaseModel):
    enabled: bool = Field(default=False)
    endpoint: str | None = Field(default=None)
    service_name: str | None = Field(default=None)
    tracer_name: str | None = Field(default=None)


class ConfigStats(BaseModel):
    enabled: bool = Field(default=False)
    host: str | None = Field(default=None)
    port: int | None = Field(default=None, gt=0, lt=65535)
    module_name: str | None = Field(default=None)


class ConfigPluginZorgAB(BaseModel):
    enabled: bool = Field(default=False)
    api_url: str | None = Field(default=None, description="Base URL for the Zorg AB API")
    mtls_cert: str | None = Field(default=None, description="Path to the mTLS certificate file")
    mtls_key: str | None = Field(default=None, description="Path to the mTLS key file")
    mtls_ca: str | None = Field(default=None, description="Path to the mTLS CA file")


class ConfigPluginKvk(BaseModel):
    enabled: bool = Field(default=False)
    api_url: str | None = Field(default=None, description="Base URL for the KVK API")
    api_key: str | None = Field(default=None, description="API key for the KVK API")


class Config(BaseModel):
    app: ConfigApp
    ratelimit: ConfigRateLimiter
    uvicorn: ConfigUvicorn
    telemetry: ConfigTelemetry
    stats: ConfigStats
    plugin_zorgab: ConfigPluginZorgAB
    plugin_kvk: ConfigPluginKvk


def read_ini_file(path: str) -> Any:
    ini_data = configparser.ConfigParser()
    ini_data.read(path)

    ret = {}
    for section in ini_data.sections():
        ret[section] = dict(ini_data[section])

    return ret


def reset_config() -> None:
    global _CONFIG
    _CONFIG = None


def set_config(config: Config) -> None:
    global _CONFIG
    _CONFIG = config


def get_config(path: str | None = None) -> Config:
    global _CONFIG
    global _PATH

    if _CONFIG is not None:
        return _CONFIG

    if path is None:
        path = _PATH

    # To be inline with other python code, we use INI-type files for configuration. Since this isn't
    # a standard format for pydantic, we need to do some manual parsing first.
    ini_data = read_ini_file(path)

    try:
        _CONFIG = Config(**ini_data)
    except ValidationError as e:
        raise e

    return _CONFIG
