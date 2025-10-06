use serde::{Deserialize, Serialize};
use std::fs;
use tonic::metadata::MetadataValue;
use tonic::transport::Channel;

pub mod solana_corecast {
    tonic::include_proto!("solana_corecast");
}

pub mod solana_messages {
    tonic::include_proto!("solana_messages");
}

use solana_corecast::core_cast_client::CoreCastClient;
use solana_corecast::{
    SubscribeTradesRequest, SubscribeOrdersRequest, SubscribePoolsRequest,
    SubscribeTransactionsRequest, SubscribeTransfersRequest, SubscribeBalanceUpdateRequest,
    AddressFilter
};

#[derive(Debug, Deserialize, Serialize)]
struct Config {
    server: ServerConfig,
    stream: StreamConfig,
    filters: FiltersConfig,
}

#[derive(Debug, Deserialize, Serialize)]
struct ServerConfig {
    address: String,
    authorization: String,
    insecure: bool,
}

#[derive(Debug, Deserialize, Serialize)]
struct StreamConfig {
    #[serde(rename = "type")]
    stream_type: String,
}

#[derive(Debug, Deserialize, Serialize)]
struct FiltersConfig {
    programs: Option<Vec<String>>,
    pools: Option<Vec<String>>,
    tokens: Option<Vec<String>>,
    traders: Option<Vec<String>>,
    senders: Option<Vec<String>>,
    receivers: Option<Vec<String>>,
    addresses: Option<Vec<String>>,
    signers: Option<Vec<String>>,
}

fn load_config() -> Result<Config, Box<dyn std::error::Error>> {
    let config_content = fs::read_to_string("src/config.yaml")?;
    let config: Config = serde_yaml::from_str(&config_content)?;
    Ok(config)
}

fn create_address_filter(addresses: Option<Vec<String>>) -> Option<AddressFilter> {
    addresses.map(|addrs| AddressFilter { addresses: addrs })
}

fn add_auth_header<T>(mut request: tonic::Request<T>, config: &Config) -> Result<tonic::Request<T>, Box<dyn std::error::Error>> {
    if !config.server.authorization.is_empty() {
        let auth_value = MetadataValue::try_from(format!("Bearer {}", config.server.authorization))?;
        request.metadata_mut().insert("authorization", auth_value);
    }
    Ok(request)
}

async fn stream_dex_trades(client: &mut CoreCastClient<Channel>, config: &Config) -> Result<(), Box<dyn std::error::Error>> {
    println!("Subscribing to DEX trades...");
    
    let request = SubscribeTradesRequest {
        program: create_address_filter(config.filters.programs.clone()),
        pool: create_address_filter(config.filters.pools.clone()),
        token: create_address_filter(config.filters.tokens.clone()),
        trader: create_address_filter(config.filters.traders.clone()),
    };
    
    let grpc_request = add_auth_header(tonic::Request::new(request), config)?;
    let mut stream = client.dex_trades(grpc_request).await?.into_inner();
    
    println!("Streaming DEX trades. Processing first message...");
    
    while let Some(message) = stream.message().await? {
        println!("Received DEX trade message:");
        println!("  Block Slot: {:?}", message.block.map(|b| b.slot));
        println!("  Transaction Index: {:?}", message.transaction.as_ref().map(|t| t.index));
        if let Some(trade) = &message.trade {
            println!("  Trade Program: {:?}", trade.dex.as_ref().map(|d| &d.program_address));
            println!("  Trade Market: {:?}", trade.market.as_ref().map(|m| &m.market_address));
        }
        println!("First message processed. Exiting.");
        break;
    }
    
    Ok(())
}

async fn stream_dex_orders(client: &mut CoreCastClient<Channel>, config: &Config) -> Result<(), Box<dyn std::error::Error>> {
    println!("Subscribing to DEX orders...");
    
    let request = SubscribeOrdersRequest {
        program: create_address_filter(config.filters.programs.clone()),
        pool: create_address_filter(config.filters.pools.clone()),
        token: create_address_filter(config.filters.tokens.clone()),
        trader: create_address_filter(config.filters.traders.clone()),
    };
    
    let grpc_request = add_auth_header(tonic::Request::new(request), config)?;
    let mut stream = client.dex_orders(grpc_request).await?.into_inner();
    
    println!("Streaming DEX orders. Processing first message...");
    
    while let Some(message) = stream.message().await? {
        println!("Received DEX order message:");
        println!("  Block Slot: {:?}", message.block.map(|b| b.slot));
        println!("  Transaction Index: {:?}", message.transaction.as_ref().map(|t| t.index));
        println!("  Order Program: {:?}", message.order.as_ref().map(|o| o.dex.as_ref().map(|d| &d.program_address)));
        println!("First message processed. Exiting.");
        break;
    }
    
    Ok(())
}

async fn stream_dex_pools(client: &mut CoreCastClient<Channel>, config: &Config) -> Result<(), Box<dyn std::error::Error>> {
    println!("Subscribing to DEX pools...");
    
    let request = SubscribePoolsRequest {
        program: create_address_filter(config.filters.programs.clone()),
        pool: create_address_filter(config.filters.pools.clone()),
        token: create_address_filter(config.filters.tokens.clone()),
    };
    
    let grpc_request = add_auth_header(tonic::Request::new(request), config)?;
    let mut stream = client.dex_pools(grpc_request).await?.into_inner();
    
    println!("Streaming DEX pools. Processing first message...");
    
    while let Some(message) = stream.message().await? {
        println!("Received DEX pool message:");
        println!("  Block Slot: {:?}", message.block.map(|b| b.slot));
        println!("  Transaction Index: {:?}", message.transaction.as_ref().map(|t| t.index));
        println!("  Pool Event Program: {:?}", message.pool_event.as_ref().map(|p| p.dex.as_ref().map(|d| &d.program_address)));
        println!("First message processed. Exiting.");
        break;
    }
    
    Ok(())
}

async fn stream_transactions(client: &mut CoreCastClient<Channel>, config: &Config) -> Result<(), Box<dyn std::error::Error>> {
    println!("Subscribing to transactions...");
    
    let request = SubscribeTransactionsRequest {
        program: create_address_filter(config.filters.programs.clone()),
        signer: create_address_filter(config.filters.signers.clone()),
    };
    
    let grpc_request = add_auth_header(tonic::Request::new(request), config)?;
    let mut stream = client.transactions(grpc_request).await?.into_inner();
    
    println!("Streaming transactions. Processing first message...");
    
    while let Some(message) = stream.message().await? {
        println!("Received transaction message:");
        println!("  Block Slot: {:?}", message.block.map(|b| b.slot));
        println!("  Transaction Signature: {:?}", message.transaction.map(|t| t.signature));
        println!("First message processed. Exiting.");
        break;
    }
    
    Ok(())
}

async fn stream_transfers(client: &mut CoreCastClient<Channel>, config: &Config) -> Result<(), Box<dyn std::error::Error>> {
    println!("Subscribing to transfers...");
    
    let request = SubscribeTransfersRequest {
        sender: create_address_filter(config.filters.senders.clone()),
        receiver: create_address_filter(config.filters.receivers.clone()),
        token: create_address_filter(config.filters.tokens.clone()),
    };
    
    let grpc_request = add_auth_header(tonic::Request::new(request), config)?;
    let mut stream = client.transfers(grpc_request).await?.into_inner();
    
    println!("Streaming transfers. Processing first message...");
    
    while let Some(message) = stream.message().await? {
        println!("Received transfer message:");
        println!("  Block Slot: {:?}", message.block.map(|b| b.slot));
        println!("  Transaction Index: {:?}", message.transaction.as_ref().map(|t| t.index));
        println!("  Transfer Sender: {:?}", message.transfer.map(|t| t.sender));
        println!("First message processed. Exiting.");
        break;
    }
    
    Ok(())
}

async fn stream_balances(client: &mut CoreCastClient<Channel>, config: &Config) -> Result<(), Box<dyn std::error::Error>> {
    println!("Subscribing to balances...");
    
    let request = SubscribeBalanceUpdateRequest {
        address: create_address_filter(config.filters.addresses.clone()),
        token: create_address_filter(config.filters.tokens.clone()),
    };
    
    let grpc_request = add_auth_header(tonic::Request::new(request), config)?;
    let mut stream = client.balances(grpc_request).await?.into_inner();
    
    println!("Streaming balances. Processing first message...");
    
    while let Some(message) = stream.message().await? {
        println!("Received balance message:");
        println!("  Block Slot: {:?}", message.block.map(|b| b.slot));
        println!("  Transaction Index: {:?}", message.transaction.as_ref().map(|t| t.index));
        println!("  Balance Address: {:?}", message.balance_update.as_ref().map(|b| b.balance_update.as_ref().map(|bu| &bu.account_index)));
        println!("First message processed. Exiting.");
        break;
    }
    
    Ok(())
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load configuration from YAML file
    let config = load_config()?;
    println!("Loaded config:");
    println!("  Server: {} (insecure: {})", config.server.address, config.server.insecure);
    println!("  Stream type: {}", config.stream.stream_type);
    println!("  Has authorization: {}", !config.server.authorization.is_empty());

    // Build server URL based on config
    let protocol = if config.server.insecure { "http" } else { "https" };
    let server_url = format!("{}://{}", protocol, config.server.address);
    println!("Connecting to: {}", server_url);

    // Create channel with options for better performance (similar to Python client)
    let channel = Channel::from_shared(server_url)?
        .initial_stream_window_size(Some(16 * 1024 * 1024))  // 16MB
        .initial_connection_window_size(Some(128 * 1024 * 1024))  // 128MB
        .keep_alive_timeout(std::time::Duration::from_secs(5))
        .keep_alive_while_idle(true)
        .connect()
        .await?;

    let mut client = CoreCastClient::new(channel);

    // Start streaming based on configuration
    match config.stream.stream_type.as_str() {
        "dex_trades" => stream_dex_trades(&mut client, &config).await?,
        "dex_orders" => stream_dex_orders(&mut client, &config).await?,
        "dex_pools" => stream_dex_pools(&mut client, &config).await?,
        "transactions" => stream_transactions(&mut client, &config).await?,
        "transfers" => stream_transfers(&mut client, &config).await?,
        "balances" => stream_balances(&mut client, &config).await?,
        _ => {
            eprintln!("Unknown stream type: {}. Supported types: dex_trades|dex_orders|dex_pools|transactions|transfers|balances", 
                     config.stream.stream_type);
            std::process::exit(1);
        }
    }

    Ok(())
}