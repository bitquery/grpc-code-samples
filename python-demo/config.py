"""
Configuration management for the CoreCast client.
"""
import yaml
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class ServerConfig:
    """Server configuration."""
    address: str
    authorization: str
    insecure: bool


@dataclass
class StreamConfig:
    """Stream configuration."""
    type: str


@dataclass
class FiltersConfig:
    """Filters configuration."""
    programs: List[str]
    pools: List[str]
    tokens: List[str]
    traders: List[str]
    senders: List[str]
    receivers: List[str]
    addresses: List[str]
    signers: List[str]


@dataclass
class Config:
    """Main configuration class."""
    server: ServerConfig
    stream: StreamConfig
    filters: FiltersConfig


def load_config(config_path: str) -> Config:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Config object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
        ValueError: If config structure is invalid
    """
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_file, 'r') as f:
        data = yaml.safe_load(f)
    
    # Validate required sections
    if 'server' not in data:
        raise ValueError("Missing 'server' section in config")
    if 'stream' not in data:
        raise ValueError("Missing 'stream' section in config")
    if 'filters' not in data:
        raise ValueError("Missing 'filters' section in config")
    
    # Create server config
    server_data = data['server']
    server_config = ServerConfig(
        address=server_data.get('address', ''),
        authorization=server_data.get('authorization', ''),
        insecure=server_data.get('insecure', False)
    )
    
    # Create stream config
    stream_data = data['stream']
    stream_config = StreamConfig(
        type=stream_data.get('type', '')
    )
    
    # Create filters config
    filters_data = data['filters']
    filters_config = FiltersConfig(
        programs=filters_data.get('programs', []),
        pools=filters_data.get('pools', []),
        tokens=filters_data.get('tokens', []),
        traders=filters_data.get('traders', []),
        senders=filters_data.get('senders', []),
        receivers=filters_data.get('receivers', []),
        addresses=filters_data.get('addresses', []),
        signers=filters_data.get('signers', [])
    )
    
    return Config(
        server=server_config,
        stream=stream_config,
        filters=filters_config
    )
