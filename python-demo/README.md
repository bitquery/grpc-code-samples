# CoreCast Python Client

A Python gRPC client for streaming Solana blockchain data from Bitquery's CoreCast service.

## Installation

Install dependencies:
```bash
pip install -r requirements.txt
```

## Authentication

The application requires a Bitquery CoreCast authorization token.

### Set your token directly in the YAML config

Edit the desired config in `configs/*.yaml` and set `server.authorization` to your token (it starts with `ory_at_...`). Example:

```yaml
server:
  address: "corecast.bitquery.io"
  insecure: false
  authorization: "ory_at_your_actual_token_here"
```

Notes:
- Your token will be sent as `authorization: Bearer <token>` metadata.
- Do not commit real tokens to version control.

## Run

### Using default configuration (dex_trades):
```bash
python3 main.py
```

### Using specific configuration:
```bash
python3 main.py --config ./configs/dex_trades.yaml
python3 main.py --config ./configs/transactions.yaml
```

### Filters

⚠️ **Important**: At least one filter must be specified for each stream type. Subscriptions without filters will be rejected.

#### Filter logic:
```
(program IN filter.programs) AND (pool IN filter.pools) AND (token IN filter.tokens)
```

## Configuration

All parameters are loaded from YAML configuration files located in the `configs/` directory.

### Available configurations:

- `configs/dex_trades.yaml` - DEX trades **filters**: *program, token, pool, trader*
- `configs/dex_orders.yaml` - DEX orders **filters**: *program, token, pool, trader*
- `configs/dex_pools.yaml` - DEX pools **filters**: *program, token, pool*
- `configs/transfers.yaml` - Transfers **filters**: *sender, receiver, token*
- `configs/balances.yaml` - Balance updates **filters**: *address, token*
- `configs/transactions.yaml` - Parsed transactions **filters**: *signer*

## Configuration format

All configuration files follow this structure:

```yaml
server:
  address: "corecast.bitquery.io"
  insecure: false            # if false, TLS will be used
  authorization: "ory_at_..."  # your CoreCast token; sent as metadata 'authorization'

stream:
  type: "dex_trades"  # or dex_orders, dex_pools, transactions, transfers, balances
  
filters:
  # DEX filters (for dex_trades, dex_orders, dex_pools), Transaction
  programs:
    - "9xQeWvG816bUx9EPjHmaT23yvVM2ZWbrrpZb9PusVFin"
  pools:
    - "Hf6c2L9H8iQy2f5uF5eBkQK2A2c6R7FZ8pCkU9D1ABCD"
  tokens:
    - "So11111111111111111111111111111111111111112"  # SOL
  traders: # not for dex_pools
    - "7GJz9X7b1G9Nf1d5uQq2Z3B4nPq6F8d9LmNoPQrsTUV"
    
  # Transfer filters (for transfers)
  senders:
    - "DSqMPMsMAbEJVNuPKv1ZFdzt6YvJaDPDddfeW7ajtqds"
  receivers:
    - "ReceiverAddressHere..."
    
  # Balance filters (for balances)
  addresses:
    - "DSqMPMsMAbEJVNuPKv1ZFdzt6YvJaDPDddfeW7ajtqds"
    
  # Transaction filters (for transactions)
  signers:
    - "ETcW7iuVraMKLMJayNCCsr9bLvKrJPDczy1CMVMPmXTc"
```

## Examples

### DEX Trades with multiple programs:
```yaml
# configs/dex_trades.yaml
filters:
  programs:
    - "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"  # Prism AMM
    - "SoLFiHG9TfgtdUXUjWAxi3LtvYuFyDLVhBWxdMZxyCe"  # SolFi
  tokens:
    - "So11111111111111111111111111111111111111112"  # SOL
```

### Transfers from specific sender:
```yaml  
# configs/transfers.yaml
filters:
  senders:
    - "DSqMPMsMAbEJVNuPKv1ZFdzt6YvJaDPDddfeW7ajtqds"
  tokens:
    - "So11111111111111111111111111111111111111112"  # SOL
    - "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
```

### Balance updates for specific address:
```yaml
# configs/balances.yaml  
filters:
  addresses:
    - "DSqMPMsMAbEJVNuPKv1ZFdzt6YvJaDPDddfeW7ajtqds"
  tokens:
    - "So11111111111111111111111111111111111111112"  # SOL
```

### Transactions from specific signer:
```yaml
# configs/transactions.yaml
filters:
  signers:
    - "ETcW7iuVraMKLMJayNCCsr9bLvKrJPDczy1CMVMPmXTc"
```

## Additional Options

### Log Level
```bash
python main.py --log-level DEBUG
```

Available log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`

## Programmatic Usage

```python
from config import load_config
from client import CoreCastClient

# Load configuration
config = load_config('configs/dex_trades.yaml')

# Create and connect client
client = CoreCastClient(config)
client.connect()

# Stream data
client.stream_dex_trades()

# Close connection
client.close()
```

## Debugging Utilities

The project includes utility functions for debugging protobuf messages:

### `protobuf_utils.py`

Contains helper functions for working with protobuf messages:

- `print_protobuf_message(msg, indent=0, encoding="base58")` - Pretty print any protobuf message
- `format_protobuf_message(msg, encoding="base58")` - Format message as string instead of printing
- `get_protobuf_field_value(msg, field_path)` - Extract specific field values using dot notation
- `extract_bytes_fields(msg, encoding="base58")` - Extract all bytes fields as a dictionary

### Usage Example

```python
from protobuf_utils import print_protobuf_message

# In your message handler
def on_message_received(message):
    print("Received message:")
    print_protobuf_message(message)
    
    # Or with hex encoding
    print_protobuf_message(message, encoding="hex")
```

### Example Script

Run the example script to see usage patterns:
```bash
python3 example_protobuf_debug.py
```

## Requirements

- Python 3.7+
- gRPC Python libraries
- PyYAML for configuration
- base58 for address encoding
- bitquery-pb2-kafka-package for Solana protobuf definitions
