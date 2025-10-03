# CoreCast gRPC client example 

## Installation

Retrieving protobuf:

```bash
go get github.com/bitquery/streaming_protobuf/v2@d62b715655afbe3068876c908e5378ef2e088ece
```

```bash
go mod tidy
```

## Building

```bash
go build -o bin/corecast-client-example ./cmd
```

## Running

### Using default configuration (configs/config.yaml):
```bash
go run ./cmd
```

## Filters

⚠️ **Important**: At least one filter must be specified for each stream type. Subscriptions without filters will be rejected.

### Filter Logic
```
(program IN filter.programs) AND (pool IN filter.pools) AND (token IN filter.tokens)
```

## Configuration

All parameters are loaded from YAML configuration file located in the `configs/` directory.

### Available Configurations

- `configs/config.yaml` - Single unified config. Set `stream.type` to one of: `dex_trades`, `dex_orders`, `dex_pools`, `transactions`, `transfers`, `balances`, and fill `filters` accordingly.

### Configuration Format

All configuration files follow this structure:

```yaml
server:
  address: "corecast.bitquery.io"
  insecure: false            
  authorization: "<token>"  

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
