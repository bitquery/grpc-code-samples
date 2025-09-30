#!/usr/bin/env python3
"""
Analyze latency by comparing received timestamps with block times.
Only uses FIRST occurrence of each unique slot.
Minimal output - errors and final stats only.
"""
import re
import sys
import requests
import time
from datetime import datetime, timezone
from collections import OrderedDict

# API endpoint
SOLANA_RPC = "https://api.mainnet-beta.solana.com"

# Rate limiting
RATE_LIMIT_DELAY = 1.0

# Limit number of UNIQUE SLOTS to analyze
MAX_SLOTS = 500


def parse_log_file(filename):
    """Parse log file and extract FIRST occurrence of each unique slot."""
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
                
                if slot not in slot_first_occurrence:
                    timestamp_str = None
                    timestamp_ns = None
                    
                    j = i + 1
                    while j < len(lines) and j < i + 5:
                        next_line = lines[j].strip()
                        
                        ns_match = re.search(r'Received Timestamp \(ns\):\s*(\d+)', next_line)
                        if ns_match:
                            timestamp_ns = int(ns_match.group(1))
                        
                        ts_match = re.search(r'Received Timestamp:\s*(.+)', next_line)
                        if ts_match and not next_line.startswith('Received Timestamp (ns)'):
                            timestamp_str = ts_match.group(1)
                        
                        j += 1
                    
                    if timestamp_str or timestamp_ns:
                        slot_first_occurrence[slot] = (timestamp_str, timestamp_ns)
        
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
                block_time_ns = int(block_time * 1_000_000_000)
                dt = datetime.fromtimestamp(block_time, tz=timezone.utc).replace(tzinfo=None)
                return slot, dt, block_time_ns, None
            else:
                error = data.get('error', {}).get('message', 'Unknown error')
                return slot, None, None, f"RPC error: {error}"
        else:
            return slot, None, None, f"HTTP {response.status_code}"
            
    except Exception as e:
        return slot, None, None, f"Error: {str(e)}"


def parse_timestamp(timestamp_str, timestamp_ns):
    """Parse timestamp to nanoseconds."""
    if timestamp_ns:
        dt = datetime.fromtimestamp(timestamp_ns / 1_000_000_000, tz=timezone.utc).replace(tzinfo=None)
        return dt, timestamp_ns
    elif timestamp_str:
        try:
            dt = datetime.fromisoformat(timestamp_str)
            dt = dt.replace(tzinfo=None)
        except:
            dt = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%f")
        
        ts_ns = int(dt.timestamp() * 1_000_000_000)
        return dt, ts_ns
    else:
        raise ValueError("No timestamp data available")


def analyze_latency(log_file):
    """Main analysis function - minimal output."""
    print("Analyzing latency data...")
    
    # Parse log file
    slot_first_occurrence = parse_log_file(log_file)
    
    if not slot_first_occurrence:
        print("ERROR: No data found in log file!")
        return
    
    # Limit to first MAX_SLOTS
    if len(slot_first_occurrence) > MAX_SLOTS:
        slots_to_check = list(slot_first_occurrence.keys())[:MAX_SLOTS]
        limited_data = OrderedDict((k, slot_first_occurrence[k]) for k in slots_to_check)
        slot_first_occurrence = limited_data
    
    # Fetch block times (silent unless errors)
    slot_to_blocktime = {}
    failed_slots = {}
    
    for slot in slot_first_occurrence.keys():
        slot_ret, block_time_dt, block_time_ns, error = get_block_time_from_rpc(slot)
        
        if block_time_dt:
            slot_to_blocktime[slot] = (block_time_dt, block_time_ns)
        else:
            failed_slots[slot] = error
            print(f"ERROR: Failed to fetch slot {slot} - {error}")
        
        time.sleep(RATE_LIMIT_DELAY)
    
    if not slot_to_blocktime:
        print("\nERROR: No block times could be fetched!")
        return
    
    # Compare timestamps
    same_second_count = 0
    total_comparisons = 0
    latencies_ms = []
    latencies_ns = []
    
    for slot, (timestamp_str, timestamp_ns) in slot_first_occurrence.items():
        if slot not in slot_to_blocktime:
            continue
        
        block_time_dt, block_time_ns = slot_to_blocktime[slot]
        received_time_dt, received_time_ns = parse_timestamp(timestamp_str, timestamp_ns)
        
        latency_ns = received_time_ns - block_time_ns
        latency_ms = latency_ns / 1_000_000.0
        
        latencies_ns.append(latency_ns)
        latencies_ms.append(latency_ms)
        
        block_second = block_time_dt.replace(microsecond=0)
        received_second = received_time_dt.replace(microsecond=0)
        same_second = (block_second == received_second)
        
        if same_second:
            same_second_count += 1
        
        total_comparisons += 1
    
    # Print final statistics
    print("\n" + "=" * 80)
    print("LATENCY ANALYSIS RESULTS")
    print("=" * 80)
    
    if total_comparisons > 0:
        percentage = (same_second_count / total_comparisons) * 100
        
        print(f"\nTotal unique slots analyzed:    {total_comparisons}")
        if failed_slots:
            print(f"Failed slots:                   {len(failed_slots)}")
        print(f"Slots with SAME second:         {same_second_count} ({percentage:.1f}%)")
        print(f"Slots with DIFFERENT second:    {total_comparisons - same_second_count} ({100-percentage:.1f}%)")
        
        if latencies_ms:
            print("\nLatency Statistics (Milliseconds):")
            print(f"  Min:     {min(latencies_ms):.0f}ms")
            print(f"  Max:     {max(latencies_ms):.0f}ms")
            print(f"  Average: {sum(latencies_ms)/len(latencies_ms):.0f}ms")
            
            sorted_lat = sorted(latencies_ms)
            median_idx = len(sorted_lat) // 2
            p95_idx = int(len(sorted_lat) * 0.95)
            p99_idx = int(len(sorted_lat) * 0.99)
            
            print(f"  Median:  {sorted_lat[median_idx]:.0f}ms")
            print(f"  P95:     {sorted_lat[p95_idx]:.0f}ms")
            print(f"  P99:     {sorted_lat[p99_idx]:.0f}ms")
            
            # Cumulative distribution
            within_100ms = sum(1 for lat in latencies_ns if lat < 100_000_000)
            within_500ms = sum(1 for lat in latencies_ns if lat < 500_000_000)
            within_1sec = sum(1 for lat in latencies_ns if lat < 1_000_000_000)
            within_2sec = sum(1 for lat in latencies_ns if lat < 2_000_000_000)
            
            within_100ms_pct = (within_100ms / len(latencies_ns)) * 100
            within_500ms_pct = (within_500ms / len(latencies_ns)) * 100
            within_1sec_pct = (within_1sec / len(latencies_ns)) * 100
            within_2sec_pct = (within_2sec / len(latencies_ns)) * 100
            
            print("\nCumulative Distribution:")
            print(f"  Within 100ms:  {within_100ms:4d} ({within_100ms_pct:5.1f}%)")
            print(f"  Within 500ms:  {within_500ms:4d} ({within_500ms_pct:5.1f}%)")
            print(f"  Within 1 sec:  {within_1sec:4d} ({within_1sec_pct:5.1f}%)")
            print(f"  Within 2 sec:  {within_2sec:4d} ({within_2sec_pct:5.1f}%)")
    
    print("\n" + "=" * 80)
    print(f"Analysis complete: {total_comparisons} slots, avg latency {sum(latencies_ms)/len(latencies_ms):.0f}ms")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 analyze_latency.py <log_file>")
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