fn main() -> Result<(), Box<dyn std::error::Error>> {
    tonic_build::configure()
        .compile(
            &[
                "src/solana/corecast/corecast.proto",
                "src/solana/corecast/request.proto",
                "src/solana/corecast/stream_message.proto",
                "src/solana/dex_block_message.proto",
                "src/solana/block_message.proto",
                "src/solana/token_block_message.proto",
                "src/solana/parsed_idl_block_message.proto",
            ],
            &["src/solana"],
        )?;
    Ok(())
}
