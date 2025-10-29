# CoreCast - Smart Solana gRPC Streams Examples

This repository contains quick start code examples for Bitquery's CoreCast Smart Solana gRPC streams in multiple programming languages (JavaScript, Python, Go, and Rust).

## What are Bitquery Smart gRPC Streams?

Bitquery Smart gRPC Streams provide low-latency, context-aware, topic-wise event delivery from the Solana blockchain. Unlike raw gRPC streams, Smart Streams enrich and filter events so your application receives only the data it needs (trades, balances, token context, program metadata). The data is sent in **protobuf format** with publicly available schemas for easy parsing.

### Key Benefits

- **Low latency**: Stream RPCs for near real-time delivery
- **Strong typing**: Protobuf contracts for stable schemas and efficient encoding
- **Context-aware filtering**: Server-side filtering to reduce bandwidth and speed up processing
- **Multiple topics**: Subscribe only to what you need

## Available Stream Topics

Bitquery exposes multiple topics for targeted subscriptions:

- **transactions**: Finalized transactions with instructions, logs, and status
- **transfers**: All token transfers with token context
- **dex_trades**: DEX trade/swaps across supported protocols
- **dex_orders**: Order lifecycle updates where applicable
- **dex_pools**: Pool creation/updates and liquidity changes
- **balances**: Balance updates for tracked accounts and mints

## Quick Start

Each language folder contains a complete example with configuration:

- **JavaScript**: `js-demo/` - Node.js implementation
- **Python**: `python-demo/` - Python implementation
- **Go**: `go-demo/` - Go implementation
- **Rust**: `rust-demo/` - Rust implementation

### Prerequisites

1. **Get your API token**: Generate one at [Bitquery Account](https://account.bitquery.io/user/api_v2/access_tokens?utm_source=github&utm_medium=readme&utm_campaign=grpc_samples)
2. **Configure authentication**: Add your token to the `config.yaml` file in each demo
3. **Install dependencies**: Follow the README in each language-specific folder

### Basic Configuration

```yaml
server:
  address: "corecast.bitquery.io"
  authorization: "<your_api_token>"
  insecure: false

stream:
  type: "transfers" # or: transactions, dex_trades, dex_orders, dex_pools, balances

filters:
  signers:
    - "7epLWkFd7xo18k4a4ySmN2UiiAFELDTV2ZNYAedCNh" # example address
```

## Documentation

### Core Documentation

- **[Introduction to gRPC Streams](https://docs.bitquery.io/docs/grpc/solana/introduction/?utm_source=github&utm_medium=readme&utm_campaign=grpc_samples)** - Overview of Smart gRPC Streams and their benefits
- **[Authentication](https://docs.bitquery.io/docs/grpc/solana/authorisation/?utm_source=github&utm_medium=readme&utm_campaign=grpc_samples)** - How to authenticate with Bitquery gRPC streams
- **[Stream Topics](https://docs.bitquery.io/docs/category/topics/?utm_source=github&utm_medium=readme&utm_campaign=grpc_samples)** - Detailed documentation for each stream topic
- **[Best Practices](https://docs.bitquery.io/docs/grpc/solana/best_practices/?utm_source=github&utm_medium=readme&utm_campaign=grpc_samples)** - Production-ready implementation guidelines

### Advanced Topics

- **[Examples](https://docs.bitquery.io/docs/category/examples/?utm_source=github&utm_medium=readme&utm_campaign=grpc_samples)** - Real-world use cases including Pump.fun and copy trading bots
- **[Live Reload Configuration](https://docs.bitquery.io/docs/grpc/solana/live-reload/?utm_source=github&utm_medium=readme&utm_campaign=grpc_samples)** - Dynamic configuration updates
- **[Error Handling](https://docs.bitquery.io/docs/grpc/solana/errors/?utm_source=github&utm_medium=readme&utm_campaign=grpc_samples)** - Comprehensive error handling strategies

### Authentication Setup

- **[Get API Token](https://account.bitquery.io/user/api_v2/access_tokens?utm_source=github&utm_medium=readme&utm_campaign=grpc_samples)** - Generate your authentication token
- **[Token Generation Guide](https://docs.bitquery.io/docs/authorisation/how-to-generate/?utm_source=github&utm_medium=readme&utm_campaign=grpc_samples)** - Step-by-step instructions for creating tokens

## Schema and Packages

The protobuf schemas are available as installable packages:

- **Python**: `pip install bitquery-corecast-proto`
- **Node.js**: `npm install bitquery-corecast-proto`

## Getting Started

1. Clone this repository
2. Choose your preferred language (JavaScript, Python, Go, or Rust)
3. Follow the README in the respective language folder
4. Configure your API token in `config.yaml`
5. Run the example and start streaming Solana data!

## Support

- **Documentation**: [Bitquery Docs](https://docs.bitquery.io/?utm_source=github&utm_medium=readme&utm_campaign=grpc_samples)
- **Community**: Join our [Telegram](https://t.me/bitquery) or follow us on [Twitter](https://twitter.com/bitquery)
- **Issues**: Report issues on our [GitHub](https://github.com/bitquery)

## License

This project is licensed under the MIT License.
