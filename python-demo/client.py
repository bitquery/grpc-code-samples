"""
CoreCast gRPC client for streaming Solana blockchain data.
"""
import grpc
import ssl
import signal
import sys
import logging
import base58
from typing import Optional, List
from contextlib import contextmanager

from bitquery_corecast_proto import corecast_pb2_grpc, corecast_pb2, request_pb2
from config import Config, load_config
from protobuf_utils import print_protobuf_message


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CoreCastClient:
    """CoreCast gRPC client for streaming Solana data."""
    
    def __init__(self, config: Config):
        self.config = config
        self.channel: Optional[grpc.Channel] = None
        self.client: Optional[corecast_pb2_grpc.CoreCastStub] = None
        
    def connect(self) -> None:
        """Establish gRPC connection to CoreCast server."""
        # Create credentials
        if self.config.server.insecure:
            credentials = grpc.insecure_channel_credentials()
            logger.debug("Using insecure gRPC transport")
        else:
            credentials = grpc.ssl_channel_credentials()
            logger.debug("Using TLS gRPC transport")
        
        # Create channel options
        options = [
            ('grpc.initial_window_size', 16 * 1024 * 1024),  # 16MB
            ('grpc.initial_conn_window_size', 128 * 1024 * 1024),  # 128MB
            ('grpc.max_receive_message_length', 64 * 1024 * 1024),  # 64MB
            ('grpc.max_send_message_length', 64 * 1024 * 1024),  # 64MB
            ('grpc.keepalive_time_ms', 15000),  # 15 seconds
            ('grpc.keepalive_timeout_ms', 5000),  # 5 seconds
            ('grpc.keepalive_permit_without_calls', True),
            ('grpc.http2.max_pings_without_data', 0),
            ('grpc.http2.min_time_between_pings_ms', 10000),
            ('grpc.http2.min_ping_interval_without_data_ms', 300000),
        ]
        
        logger.debug(f"Connecting to gRPC server: {self.config.server.address}")
        
        # Create channel
        self.channel = grpc.secure_channel(
            self.config.server.address,
            credentials,
            options=options
        )
        
        # Create client stub
        self.client = corecast_pb2_grpc.CoreCastStub(self.channel)
        logger.debug("gRPC connection established")
    
    def close(self) -> None:
        """Close the gRPC connection."""
        if self.channel:
            self.channel.close()
            logger.debug("gRPC connection closed")
    
    def _create_metadata(self) -> List[tuple]:
        """Create metadata for gRPC calls."""
        metadata = []
        if self.config.server.authorization:
            metadata.append(('authorization', f'Bearer {self.config.server.authorization}'))
            logger.debug("Authorization metadata attached")
        else:
            logger.warning("No authorization token provided - connection may fail")
        return metadata
    
    def _addr_filter_from_slice(self, addresses: List[str]) -> Optional[request_pb2.AddressFilter]:
        """Create AddressFilter from list of addresses."""
        if not addresses:
            return None
        return request_pb2.AddressFilter(addresses=addresses)
    
    def stream_dex_trades(self):
        """Stream DEX trades."""
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        req = request_pb2.SubscribeTradesRequest(
            program=self._addr_filter_from_slice(self.config.filters.programs),
            pool=self._addr_filter_from_slice(self.config.filters.pools),
            token=self._addr_filter_from_slice(self.config.filters.tokens),
            trader=self._addr_filter_from_slice(self.config.filters.traders)
        )
        
        logger.info(f"Subscribing to DEX trades: {req}")
        metadata = self._create_metadata()
        
        try:
            stream = self.client.DexTrades(req, metadata=metadata)
            self._consume_dex_trades(stream)
        except grpc.RpcError as e:
            logger.error(f"DEX trades subscription failed: {e}")
            raise
    
    def stream_dex_orders(self):
        """Stream DEX orders."""
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        req = request_pb2.SubscribeOrdersRequest(
            program=self._addr_filter_from_slice(self.config.filters.programs),
            pool=self._addr_filter_from_slice(self.config.filters.pools),
            token=self._addr_filter_from_slice(self.config.filters.tokens),
            trader=self._addr_filter_from_slice(self.config.filters.traders)
        )
        
        logger.info(f"Subscribing to DEX orders: {req}")
        metadata = self._create_metadata()
        
        try:
            stream = self.client.DexOrders(req, metadata=metadata)
            self._consume_dex_orders(stream)
        except grpc.RpcError as e:
            logger.error(f"DEX orders subscription failed: {e}")
            raise
    
    def stream_dex_pools(self):
        """Stream DEX pool events."""
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        req = request_pb2.SubscribePoolsRequest(
            program=self._addr_filter_from_slice(self.config.filters.programs),
            pool=self._addr_filter_from_slice(self.config.filters.pools),
            token=self._addr_filter_from_slice(self.config.filters.tokens)
        )
        
        logger.info(f"Subscribing to DEX pools: {req}")
        metadata = self._create_metadata()
        
        try:
            stream = self.client.DexPools(req, metadata=metadata)
            self._consume_dex_pools(stream)
        except grpc.RpcError as e:
            logger.error(f"DEX pools subscription failed: {e}")
            raise
    
    def stream_transactions(self):
        """Stream parsed transactions."""
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        req = request_pb2.SubscribeTransactionsRequest(
            program=self._addr_filter_from_slice(self.config.filters.programs),
            signer=self._addr_filter_from_slice(self.config.filters.signers)
        )
        
        logger.info(f"Subscribing to transactions: {req}")
        metadata = self._create_metadata()
        
        try:
            stream = self.client.Transactions(req, metadata=metadata)
            self._consume_parsed_transactions(stream)
        except grpc.RpcError as e:
            logger.error(f"Transactions subscription failed: {e}")
            raise
    
    def stream_transfers(self):
        """Stream transfers."""
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        req = request_pb2.SubscribeTransfersRequest(
            sender=self._addr_filter_from_slice(self.config.filters.senders),
            receiver=self._addr_filter_from_slice(self.config.filters.receivers),
            token=self._addr_filter_from_slice(self.config.filters.tokens)
        )
        
        logger.info(f"Subscribing to transfers: {req}")
        metadata = self._create_metadata()
        
        try:
            stream = self.client.Transfers(req, metadata=metadata)
            self._consume_transfers_tx(stream)
        except grpc.RpcError as e:
            logger.error(f"Transfers subscription failed: {e}")
            raise
    
    def stream_balances(self):
        """Stream balance updates."""
        if not self.client:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        req = request_pb2.SubscribeBalanceUpdateRequest(
            address=self._addr_filter_from_slice(self.config.filters.addresses),
            token=self._addr_filter_from_slice(self.config.filters.tokens)
        )
        
        logger.info(f"Subscribing to balances: {req}")
        metadata = self._create_metadata()
        
        try:
            stream = self.client.Balances(req, metadata=metadata)
            self._consume_balances_tx(stream)
        except grpc.RpcError as e:
            logger.error(f"Balances subscription failed: {e}")
            raise
    
    def _consume_dex_trades(self, stream):
        """Consume DEX trades stream."""
        logger.info("Streaming DEX trades. Press Ctrl+C to stop.")
        try:
            for msg in stream:
                try:
                    # Extract trade information
                    logger.debug(f"Received message: {msg}")

                    print_protobuf_message(msg)                    
                except Exception as e:
                    logger.error(f"Error processing trade: {e}")
                    logger.debug(f"Message data: {msg}")
        except KeyboardInterrupt:
            logger.info("Stream interrupted by user")
            raise
        except grpc.RpcError as e:
            logger.debug(f"Stream ended: {e}")
    
    def _consume_dex_orders(self, stream):
        """Consume DEX orders stream."""
        logger.info("Streaming DEX orders. Press Ctrl+C to stop.")
        try:
            for msg in stream:
                print_protobuf_message(msg)
        except KeyboardInterrupt:
            logger.info("Stream interrupted by user")
            raise
        except grpc.RpcError as e:
            logger.debug(f"Stream ended: {e}")
    
    def _consume_dex_pools(self, stream):
        """Consume DEX pool events stream."""
        logger.info("Streaming DEX pool events. Press Ctrl+C to stop.")
        try:
            for msg in stream:
                evt = msg.pool_event
                print_protobuf_message(msg)
        except KeyboardInterrupt:
            logger.info("Stream interrupted by user")
            raise
                           
        except grpc.RpcError as e:
            logger.debug(f"Stream ended: {e}")
    
    def _consume_parsed_transactions(self, stream):
        """Consume parsed transactions stream."""
        logger.info("Streaming parsed transactions. Press Ctrl+C to stop.")
        try:
            for msg in stream:
                print_protobuf_message(msg)
        except KeyboardInterrupt:
            logger.info("Stream interrupted by user")
            raise
        except grpc.RpcError as e:
            logger.debug(f"Stream ended: {e}")
    
    def _consume_transfers_tx(self, stream):
        """Consume transfers stream."""
        logger.info("Streaming transfers. Press Ctrl+C to stop.")
        try:
            for msg in stream:
                print_protobuf_message(msg)
        except KeyboardInterrupt:
            logger.info("Stream interrupted by user")
            raise
        except grpc.RpcError as e:
            logger.debug(f"Stream ended: {e}")
    
    def _consume_balances_tx(self, stream):
        """Consume balance updates stream."""
        logger.info("Streaming balance updates. Press Ctrl+C to stop.")
        try:
            for msg in stream:
                print_protobuf_message(msg)
        except KeyboardInterrupt:
            logger.info("Stream interrupted by user")
            raise
        except grpc.RpcError as e:
            logger.debug(f"Stream ended: {e}")


@contextmanager
def signal_handler():
    """Context manager for handling interrupt signals."""
    interrupted = False
    
    def signal_handler_func(signum, frame):
        nonlocal interrupted
        interrupted = True
        logger.info("Interrupt received, stopping stream...")
        raise KeyboardInterrupt()
    
    # Set up signal handlers
    original_sigint = signal.signal(signal.SIGINT, signal_handler_func)
    original_sigterm = signal.signal(signal.SIGTERM, signal_handler_func)
    
    try:
        yield interrupted
    finally:
        # Restore original signal handlers
        signal.signal(signal.SIGINT, original_sigint)
        signal.signal(signal.SIGTERM, original_sigterm)
