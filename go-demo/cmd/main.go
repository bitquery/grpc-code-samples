package main

import (
	"context"
	"crypto/tls"
	"flag"
	"fmt"
	"os"
	"os/signal"
	"syscall"
	"time"

	proto "github.com/bitquery/streaming_protobuf/v2/solana/corecast/stream"
	solana_messages "github.com/bitquery/streaming_protobuf/v2/solana/messages"
	log "github.com/inconshreveable/log15"
	_ "github.com/mostynb/go-grpc-compression/zstd" // zstd codec registration
	"github.com/mr-tron/base58"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/credentials/insecure"
	_ "google.golang.org/grpc/encoding/gzip" // gzip codec registration
	"google.golang.org/grpc/keepalive"
	"google.golang.org/grpc/metadata"

	"corecast-client-example/internal"
)

func main() {
    configPath := flag.String("config", "./configs/config.yaml", "Path to configuration file")
	flag.Parse()

	config, err := internal.LoadConfig(*configPath)
	if err != nil {
		log.Error("Failed to load config", "path", *configPath, "err", err)
		os.Exit(1)
	}

    // Debug loaded configuration (without leaking secrets)
    log.Debug(
        "config loaded",
        "path", *configPath,
        "server.address", config.Server.Address,
        "server.insecure", config.Server.Insecure,
        "server.has_auth", config.Server.Authorization != "",
        "stream.type", config.Stream.Type,
        "filters.programs", len(config.Filters.Programs),
        "filters.pools", len(config.Filters.Pools),
        "filters.tokens", len(config.Filters.Tokens),
        "filters.traders", len(config.Filters.Traders),
        "filters.senders", len(config.Filters.Senders),
        "filters.receivers", len(config.Filters.Receivers),
        "filters.addresses", len(config.Filters.Addresses),
        "filters.signers", len(config.Filters.Signers),
    )

	var ka = keepalive.ClientParameters{
		Time:                15 * time.Second,
		Timeout:             5 * time.Second,
		PermitWithoutStream: true,
	}

	ctx := context.Background()
	if config.Server.Authorization != "" {
		md := metadata.New(map[string]string{"authorization": fmt.Sprintf("Bearer %s", config.Server.Authorization)})
		ctx = metadata.NewOutgoingContext(ctx, md)
        log.Debug("authorization metadata attached")
	}

	var cr credentials.TransportCredentials
	if config.Server.Insecure {
		cr = insecure.NewCredentials()
        log.Debug("grpc transport", "mode", "insecure")
	} else {
		cr = credentials.NewTLS(&tls.Config{})
        log.Debug("grpc transport", "mode", "tls")
	}

    log.Debug("dialing grpc", "address", config.Server.Address)
    conn, err := grpc.NewClient(config.Server.Address, grpc.WithTransportCredentials(cr),
		grpc.WithInitialWindowSize(16<<20),
		grpc.WithInitialConnWindowSize(128<<20),
		grpc.WithDefaultCallOptions(
			grpc.MaxCallRecvMsgSize(64<<20),
			grpc.MaxCallSendMsgSize(64<<20),
			//grpc.UseCompressor("gzip"), // zstd or gzip
		),
		grpc.WithReadBufferSize(4<<20),
		grpc.WithWriteBufferSize(4<<20),
		grpc.WithKeepaliveParams(ka))

	if err != nil {
		log.Error("dial failed", "err", err)
		os.Exit(1)
	}
	defer func() { _ = conn.Close() }()
    log.Debug("grpc connection established")

	streamCtx, cancelStream := context.WithCancel(ctx)
	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)

	go func() {
		<-sigCh
		log.Debug("interrupt received, cancelling stream...")
		cancelStream()
	}()

	client := proto.NewCoreCastClient(conn)

	switch config.Stream.Type {
	case "dex_trades":
		req := &proto.SubscribeTradesRequest{
			Program: addrFilterFromSlice(config.Filters.Programs),
			Pool:    addrFilterFromSlice(config.Filters.Pools),
			Token:   addrFilterFromSlice(config.Filters.Tokens),
			Trader:  addrFilterFromSlice(config.Filters.Traders),
		}
		log.Info("trades subscribe", "req", req)
		strm, err := client.DexTrades(streamCtx, req)
		if err != nil {
			log.Error("trades subscribe", "err", err)
			os.Exit(1)
		}
		consumeDexTrades(strm)
	case "dex_orders":
		req := &proto.SubscribeOrdersRequest{
			Program: addrFilterFromSlice(config.Filters.Programs),
			Pool:    addrFilterFromSlice(config.Filters.Pools),
			Token:   addrFilterFromSlice(config.Filters.Tokens),
			Trader:  addrFilterFromSlice(config.Filters.Traders),
		}
        log.Info("orders subscribe", "req", req)
		strm, err := client.DexOrders(streamCtx, req)
		if err != nil {
			log.Error("orders subscribe", "err", err)
			os.Exit(1)
		}
		consumeDexOrders(strm)
	case "dex_pools":
		req := &proto.SubscribePoolsRequest{
			Program: addrFilterFromSlice(config.Filters.Programs),
			Pool:    addrFilterFromSlice(config.Filters.Pools),
			Token:   addrFilterFromSlice(config.Filters.Tokens),
		}
        log.Info("pools subscribe", "req", req)
		strm, err := client.DexPools(streamCtx, req)
		if err != nil {
			log.Error("pools subscribe", "err", err)
			os.Exit(1)
		}
		consumeDexPools(strm)
	case "transactions":
		req := &proto.SubscribeTransactionsRequest{
			Program: addrFilterFromSlice(config.Filters.Programs),
			Signer:  addrFilterFromSlice(config.Filters.Signers),
		}
        log.Info("transactions subscribe", "req", req)
		strm, err := client.Transactions(streamCtx, req)
		if err != nil {
			log.Error("transactions subscribe", "err", err)
			os.Exit(1)
		}
		consumeParsedTransactions(strm)
	case "transfers":
		req := &proto.SubscribeTransfersRequest{
			Sender:   addrFilterFromSlice(config.Filters.Senders),
			Receiver: addrFilterFromSlice(config.Filters.Receivers),
			Token:    addrFilterFromSlice(config.Filters.Tokens),
		}
        log.Info("transfers subscribe", "req", req)
		strm, err := client.Transfers(streamCtx, req)
		if err != nil {
			log.Error("transfers subscribe", "err", err)
			os.Exit(1)
		}
		consumeTransfersTx(strm)
	case "balances":
		req := &proto.SubscribeBalanceUpdateRequest{
			Address: addrFilterFromSlice(config.Filters.Addresses),
			Token:   addrFilterFromSlice(config.Filters.Tokens),
		}
        log.Info("balances subscribe", "req", req)
		strm, err := client.Balances(streamCtx, req)
		if err != nil {
			log.Error("balances subscribe", "err", err)
			os.Exit(1)
		}
		consumeBalancesTx(strm)
	default:
		log.Error("unknown stream type", "type", config.Stream.Type, "supported", "dex_trades|dex_orders|dex_pools|transactions|transfers|balances")
		os.Exit(1)
	}
}

func addrFilterFromSlice(addresses []string) *proto.AddressFilter {
	if len(addresses) == 0 {
		return nil
	}
	return &proto.AddressFilter{Addresses: addresses}
}

func consumeDexTrades(strm proto.CoreCast_DexTradesClient) {
	log.Info("Streaming dex trades. Press Ctrl+C to stop.")
	for {
		msg, err := strm.Recv()
		if err != nil {
			log.Debug("stream end", "err", err)
			return
		}

		var acc *solana_messages.Account
		if msg.Trade.Buy != nil {
			acc = msg.Trade.Buy.Account
		} else {
			acc = msg.Trade.Sell.Account
		}

		market := ""
		if msg.Trade.Market != nil {
			market = base58.Encode(msg.Trade.Market.MarketAddress)
		}
		log.Info(
			"Swap",
			"Slot", msg.Block.Slot,
			"Success", msg.Transaction.Status.Success,
			"Signature", base58.Encode(msg.Transaction.Signature),
			"Sell", base58.Encode(msg.Trade.Sell.Currency.MintAddress),
			"Buy", base58.Encode(msg.Trade.Buy.Currency.MintAddress),
			"SellAmount", msg.Trade.Sell.Amount,
			"BuyAmount", msg.Trade.Buy.Amount,
			"Account", base58.Encode(acc.Address),
			"Pool", market,
			"Program", base58.Encode(msg.Trade.Dex.ProgramAddress),
		)
	}
}

func consumeDexOrders(strm proto.CoreCast_DexOrdersClient) {
	log.Info("Streaming dex orders. Press Ctrl+C to stop.")
	for {
		msg, err := strm.Recv()
		if err != nil {
			log.Debug("stream end", "err", err)
			return
		}

		order := msg.Order.Order
		log.Info(
			"Order",
			"OrderId", base58.Encode(order.OrderId),
			"BuySide", order.BuySide,
			"LimitPrice", order.LimitPrice,
			"LimitAmount", order.LimitAmount,
			"Account", base58.Encode(order.Account),
			"Pool", base58.Encode(msg.Order.Market.MarketAddress),
			"Program", base58.Encode(msg.Order.Dex.ProgramAddress),
			"BaseMint", base58.Encode(msg.Order.Market.BaseCurrency.MintAddress),
			"QuoteMint", base58.Encode(msg.Order.Market.QuoteCurrency.MintAddress),
		)
	}
}

func consumeDexPools(strm proto.CoreCast_DexPoolsClient) {
	log.Info("Streaming dex pool events. Press Ctrl+C to stop.")
	for {
		msg, err := strm.Recv()
		if err != nil {
			log.Debug("stream end", "err", err)
			return
		}

		evt := msg.PoolEvent
		log.Info(
			"PoolEvent",
			"BaseChange", evt.BaseCurrency.ChangeAmount,
			"QuoteChange", evt.QuoteCurrency.ChangeAmount,
			"Program", base58.Encode(msg.PoolEvent.Dex.ProgramAddress),
			"BaseMint", base58.Encode(evt.Market.BaseCurrency.MintAddress),
			"QuoteMint", base58.Encode(evt.Market.QuoteCurrency.MintAddress),
			"Pool", base58.Encode(evt.Market.MarketAddress),
		)
	}
}

func consumeParsedTransactions(strm proto.CoreCast_TransactionsClient) {
	log.Info("Streaming parsed transactions. Press Ctrl+C to stop.")
	for {
		msg, err := strm.Recv()
		if err != nil {
			log.Debug("stream end", "err", err)
			return
		}

		signerCount := 0
		if msg.Transaction.Header != nil {
			for _, acc := range msg.Transaction.Header.Accounts {
				if acc != nil && acc.IsSigner {
					signerCount++
				}
			}
		}
		status := false
		if msg.Transaction.Status != nil {
			status = msg.Transaction.Status.Success
		}
		log.Info(
			"ParsedTransaction",
			"Slot", msg.Block.Slot,
			"Signature", base58.Encode(msg.Transaction.Signature),
			"Instructions", len(msg.Transaction.ParsedIdlInstructions),
			"Signers", signerCount,
			"Signer", base58.Encode(msg.Transaction.Header.Signer),
			"Status", status,
		)
	}
}

func consumeTransfersTx(strm proto.CoreCast_TransfersClient) {
	log.Info("Streaming tx transfers. Press Ctrl+C to stop.")
	for {
		msg, err := strm.Recv()
		if err != nil {
			log.Debug("stream end", "err", err)
			return
		}

		t := msg.Transfer

		log.Info(
			"Transfer",
			"Slot", msg.Block.Slot,
			"TxIndex", msg.Transaction.Index,
			"Sign", base58.Encode(msg.Transaction.Signature),
			"Mint", base58.Encode(t.Currency.MintAddress),
			"Sender", base58.Encode(t.Sender.Address),
			"Receiver", base58.Encode(t.Receiver.Address),
			"Amount", t.Amount,
			"InstructionIndex", t.InstructionIndex,
		)
	}
}

func consumeBalancesTx(strm proto.CoreCast_BalancesClient) {
	log.Info("Streaming tx balances. Press Ctrl+C to stop.")
	for {
		msg, err := strm.Recv()
		if err != nil {
			log.Debug("stream end", "err", err)
			return
		}

		b := msg.BalanceUpdate

		var address string
		idx := b.BalanceUpdate.AccountIndex
		if acc := msg.Transaction.Header.Accounts[idx]; acc != nil && acc.Address != nil {
			address = base58.Encode(acc.Address)
		}

		log.Info(
			"BalanceUpdate",
			"Slot", msg.Block.Slot,
			"TxIndex", msg.Transaction.Index,
			"Sign", base58.Encode(msg.Transaction.Signature),
			"Address", address,
			"Mint", base58.Encode(b.Currency.MintAddress),
			"Pre", b.BalanceUpdate.PreBalance,
			"Post", b.BalanceUpdate.PostBalance,
		)
	}
}
