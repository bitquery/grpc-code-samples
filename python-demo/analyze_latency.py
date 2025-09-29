#!/usr/bin/env python3
"""
Analyze latency by comparing received timestamps with block times.
Only uses FIRST occurrence of each unique slot.
"""
import re
import sys
import requests
import time
from datetime import datetime
from collections import OrderedDict

# API endpoint
SOLANA_RPC = "https://api.mainnet-beta.solana.com"

# Rate limiting (reduced for speed)
RATE_LIMIT_DELAY = 1.0  # ~6-7 requests per second, well within limits

# Limit number of UNIQUE SLOTS to analyze
MAX_SLOTS = 500

# Solscan API token (optional)
SOLSCAN_TOKEN = None


def parse_log_file(filename):
    """
    Parse log file and extract FIRST occurrence of each unique slot.
    
    Returns:
        OrderedDict: {slot: first_timestamp_str}
    """
    slot_first_occurrence = OrderedDict()
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith('Block Slot:'):
            slot_match = re.search(r'Block Slot:\s*(\d+)', line)
            if slot_match:
                slot = int(slot_match.group(1))
                
                # Only store if this is the FIRST time we see this slot
                if slot not in slot_first_occurrence:
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        timestamp_match = re.search(r'Received Timestamp:\s*(.+)', next_line)
                        if timestamp_match:
                            received_timestamp = timestamp_match.group(1)
                            slot_first_occurrence[slot] = received_timestamp
        
        i += 1
    
    return slot_first_occurrence


def get_block_time_from_rpc(slot):
    """Fetch block time from Solana RPC."""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getBlockTime",
            "params": [slot]
        }
        
        response = requests.post(SOLANA_RPC, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            block_time = data.get('result')
            if block_time:
                # Convert Unix timestamp to UTC datetime
                from datetime import timezone
                return slot, datetime.fromtimestamp(block_time, tz=timezone.utc).replace(tzinfo=None), None
            else:
                error = data.get('error', {}).get('message', 'Unknown error')
                return slot, None, f"RPC error: {error}"
        else:
            return slot, None, f"HTTP {response.status_code}"
            
    except Exception as e:
        return slot, None, f"Error: {str(e)}"


def parse_timestamp(timestamp_str):
    """Parse ISO timestamp string to datetime (assumes UTC)."""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        # If timezone-naive, assume it's UTC
        return dt.replace(tzinfo=None)
    except:
        return datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")


def analyze_latency(log_file):
    """Main analysis function."""
    print("=" * 80)
    print("LATENCY ANALYSIS: First Trade Per Slot")
    print("=" * 80)
    print()
    
    # Parse log file - get FIRST occurrence of each slot
    print(f"Parsing log file: {log_file}")
    print("Extracting FIRST occurrence of each unique slot...")
    slot_first_occurrence = parse_log_file(log_file)
    
    if not slot_first_occurrence:
        print("ERROR: No data found in log file!")
        return
    
    print(f"Found {len(slot_first_occurrence)} unique slots")
    
    # Limit to first MAX_SLOTS
    if len(slot_first_occurrence) > MAX_SLOTS:
        slots_to_check = list(slot_first_occurrence.keys())[:MAX_SLOTS]
        limited_data = OrderedDict((k, slot_first_occurrence[k]) for k in slots_to_check)
        slot_first_occurrence = limited_data
        print(f"Limiting to first {MAX_SLOTS} unique slots")
    
    print()
    print(f"Unique slots to check: {len(slot_first_occurrence)}")
    print()
    
    # Fetch block times
    print("Fetching block times from Solana RPC...")
    print()
    
    slot_to_blocktime = {}
    failed_slots = {}
    
    for idx, slot in enumerate(slot_first_occurrence.keys(), 1):
        print(f"  [{idx}/{len(slot_first_occurrence)}] Fetching slot {slot}...", end=' ')
        sys.stdout.flush()
        
        slot_ret, block_time, error = get_block_time_from_rpc(slot)
        
        if block_time:
            slot_to_blocktime[slot] = block_time
            print(f"OK - {block_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
        else:
            failed_slots[slot] = error
            print(f"FAILED - {error}")
        
        if idx < len(slot_first_occurrence):
            time.sleep(RATE_LIMIT_DELAY)
    
    print()
    print(f"Successfully fetched {len(slot_to_blocktime)}/{len(slot_first_occurrence)} block times")
    
    if failed_slots:
        print(f"Failed slots: {len(failed_slots)}")
    
    if not slot_to_blocktime:
        print("\nERROR: No block times could be fetched!")
        return
    
    print()
    
    # Compare timestamps - ONE comparison per slot
    print("=" * 80)
    print("COMPARISON RESULTS")
    print("=" * 80)
    print()
    
    same_second_count = 0
    total_comparisons = 0
    latencies = []
    results = []
    
    for slot, received_timestamp_str in slot_first_occurrence.items():
        if slot not in slot_to_blocktime:
            continue
        
        block_time = slot_to_blocktime[slot]
        received_time = parse_timestamp(received_timestamp_str)
        
        # Calculate latency
        latency_ms = (received_time - block_time).total_seconds() * 1000
        latencies.append(latency_ms)
        
        # Check if same second
        block_second = block_time.replace(microsecond=0)
        received_second = received_time.replace(microsecond=0)
        same_second = (block_second == received_second)
        
        if same_second:
            same_second_count += 1
        
        total_comparisons += 1
        
        results.append({
            'slot': slot,
            'block_time': block_time,
            'received_time': received_time,
            'latency_ms': latency_ms,
            'same_second': same_second
        })
    
    # Print sample comparisons
    print("Sample Comparisons (first 10):")
    print()
    for i, result in enumerate(results[:10], 1):
        status = "SAME SECOND" if result['same_second'] else "DIFFERENT"
        print(f"{i}. Slot: {result['slot']}")
        print(f"   Block Time:    {result['block_time'].strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"   Received Time: {result['received_time'].strftime('%Y-%m-%d %H:%M:%S.%f')} UTC")
        print(f"   Latency:       {result['latency_ms']:.0f}ms")
        print(f"   Status:        {status}")
        print()
    
    # Statistics
    print("=" * 80)
    print("STATISTICS")
    print("=" * 80)
    print()
    
    if total_comparisons > 0:
        percentage = (same_second_count / total_comparisons) * 100
        
        print(f"Total unique slots analyzed:    {total_comparisons}")
        print(f"Slots with SAME second:         {same_second_count} ({percentage:.2f}%)")
        print(f"Slots with DIFFERENT second:    {total_comparisons - same_second_count} ({100-percentage:.2f}%)")
        print()
        
        if latencies:
            print("Latency Statistics:")
            print(f"  Min:     {min(latencies):.0f}ms")
            print(f"  Max:     {max(latencies):.0f}ms")
            print(f"  Average: {sum(latencies)/len(latencies):.0f}ms")
            
            sorted_lat = sorted(latencies)
            median_idx = len(sorted_lat) // 2
            p95_idx = int(len(sorted_lat) * 0.95)
            p99_idx = int(len(sorted_lat) * 0.99)
            
            print(f"  Median:  {sorted_lat[median_idx]:.0f}ms")
            print(f"  P95:     {sorted_lat[p95_idx]:.0f}ms")
            print(f"  P99:     {sorted_lat[p99_idx]:.0f}ms")
            print()
            
            # Latency distribution
            print("Latency Distribution:")
            ranges = [
                (0, 500, "< 500ms (sub-second)"),
                (500, 1000, "500-1000ms"),
                (1000, 2000, "1-2 seconds"),
                (2000, 5000, "2-5 seconds"),
                (5000, float('inf'), "> 5 seconds")
            ]
            
            for min_val, max_val, label in ranges:
                count = sum(1 for lat in latencies if min_val <= lat < max_val)
                pct = (count / len(latencies)) * 100
                bar = "#" * int(pct / 2)
                print(f"  {label:25s} {count:4d} ({pct:5.1f}%) {bar}")
            
            print()
            
            # Count how many are within 1 second
            within_1sec = sum(1 for lat in latencies if lat < 1000)
            within_1sec_pct = (within_1sec / len(latencies)) * 100
            print(f"Slots received within 1 second:  {within_1sec} ({within_1sec_pct:.1f}%)")
    
    print()
    print("=" * 80)
    print(f"ANALYSIS COMPLETE")
    print(f"Analyzed FIRST occurrence of {total_comparisons} unique slots")
    print(f"Same-second match rate: {percentage:.2f}%")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 analyze_latency.py <log_file>")
        print()
        print("Example:")
        print("  python3 analyze_latency.py run.log")
        print()
        print("Note: Analyzes FIRST occurrence of each unique slot (max 500 slots)")
        sys.exit(1)
    
    log_file = sys.argv[1]
    
    try:
        analyze_latency(log_file)
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)