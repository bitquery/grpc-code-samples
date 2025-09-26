#!/usr/bin/env python3
"""
Main entry point for the CoreCast Python client.
"""
import argparse
import sys
import logging
from pathlib import Path

from config import load_config
from client import CoreCastClient, signal_handler


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='CoreCast Python Client')
    parser.add_argument(
        '--config', 
        default='./configs/dex_trades.yaml',
        help='Path to configuration file (default: ./configs/dex_trades.yaml)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set the logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Debug loaded configuration (without leaking secrets)
        logger.debug(
            f"Config loaded: "
            f"path={args.config}, "
            f"server.address={config.server.address}, "
            f"server.insecure={config.server.insecure}, "
            f"server.has_auth={bool(config.server.authorization)}, "
            f"stream.type={config.stream.type}, "
            f"filters.programs={len(config.filters.programs)}, "
            f"filters.pools={len(config.filters.pools)}, "
            f"filters.tokens={len(config.filters.tokens)}, "
            f"filters.traders={len(config.filters.traders)}, "
            f"filters.senders={len(config.filters.senders)}, "
            f"filters.receivers={len(config.filters.receivers)}, "
            f"filters.addresses={len(config.filters.addresses)}, "
            f"filters.signers={len(config.filters.signers)}"
        )
        
        # Create client
        client = CoreCastClient(config)
        
        # Set up signal handling
        with signal_handler() as interrupted:
            try:
                # Connect to server
                client.connect()
                
                # Start streaming based on configuration
                stream_type = config.stream.type
                if stream_type == "dex_trades":
                    client.stream_dex_trades()
                elif stream_type == "dex_orders":
                    client.stream_dex_orders()
                elif stream_type == "dex_pools":
                    client.stream_dex_pools()
                elif stream_type == "transactions":
                    client.stream_transactions()
                elif stream_type == "transfers":
                    client.stream_transfers()
                elif stream_type == "balances":
                    client.stream_balances()
                else:
                    logger.error(
                        f"Unknown stream type: {stream_type}. "
                        f"Supported types: dex_trades|dex_orders|dex_pools|transactions|transfers|balances"
                    )
                    sys.exit(1)
                    
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                sys.exit(1)
            finally:
                client.close()
                
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
