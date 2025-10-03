use tokio::time::interval;
use tonic::metadata::MetadataValue;
use tonic::transport::Channel;

pub mod solana_corecast {
    tonic::include_proto!("solana_corecast");
}

use solana_corecast::core_cast_client::CoreCastClient;
use solana_corecast::RequestMessage;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Create a channel (no TLS for now, just plaintext connection)
    let channel = Channel::from_static("http://127.0.0.1:50051")
        .connect()
        .await?;

    let mut client = CoreCastClient::new(channel);

    // Example request
    let request = tonic::Request::new(RequestMessage {
        // fill fields according to your .proto definition
        query: "dex_trades".to_string(),
        ..Default::default()
    });

    // Example call: match the RPC methods generated from your proto
    let response = client.dex_trades(request).await?;

    println!("Got response: {:?}", response.into_inner());

    Ok(())
}