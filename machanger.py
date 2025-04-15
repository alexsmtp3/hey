#!/usr/bin/env python3
import subprocess
import re
import os
import argparse
import json
import random

# Configuration file to store original MAC
CONFIG_FILE = os.path.expanduser('~/.mac_changer_config.json')

def get_current_mac(interface):
    """Get the current MAC address of the specified interface."""
    try:
        ifconfig_output = subprocess.check_output(["ifconfig", interface]).decode('utf-8')
        mac_address_search = re.search(r'ether\s+([0-9a-fA-F:]{17})', ifconfig_output)
        
        if mac_address_search:
            return mac_address_search.group(1)
        else:
            print(f"[!] Could not read MAC address for {interface}")
            return None
    except subprocess.CalledProcessError:
        print(f"[!] Error running ifconfig for {interface}")
        return None

def set_mac_address(interface, new_mac):
    """Change the MAC address of the specified interface."""
    print(f"[*] Changing MAC address for {interface} to {new_mac}")
    
    try:
        # Disable the interface
        subprocess.call(["ifconfig", interface, "down"])
        
        # Change the MAC
        subprocess.call(["ifconfig", interface, "hw", "ether", new_mac])
        
        # Enable the interface
        subprocess.call(["ifconfig", interface, "up"])
        
        # Verify the change
        current_mac = get_current_mac(interface)
        if current_mac == new_mac:
            print(f"[+] MAC address was successfully changed to {new_mac}")
            return True
        else:
            print(f"[!] Failed to change MAC address to {new_mac}")
            return False
    except Exception as e:
        print(f"[!] Error changing MAC address: {e}")
        return False

def save_original_mac(interface, mac):
    """Save the original MAC address to config file."""
    config = {}
    
    # Load existing config if it exists
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    
    # Save or update the MAC for this interface
    if interface not in config:
        config[interface] = mac
        print(f"[*] Original MAC address for {interface} saved: {mac}")
    
    # Write back to config file
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def get_original_mac(interface):
    """Get the original MAC address from config file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config.get(interface)
    return None

def generate_random_mac():
    """Generate a random MAC address."""
    # First byte should have the locally administered bit set (bit 1)
    # and the multicast bit unset (bit 0)
    first_byte = random.randint(0, 255) & 0xFE | 0x02
    mac = [first_byte]
    
    # Generate the rest of the MAC address
    for _ in range(5):
        mac.append(random.randint(0, 255))
        
    # Format as a proper MAC address
    return ':'.join(f"{b:02x}" for b in mac)

def main():
    parser = argparse.ArgumentParser(description='Change MAC address with option to restore original')
    parser.add_argument('interface', help='Network interface to change MAC address for')
    parser.add_argument('--mac', help='New MAC address (if not specified, a random one will be generated)')
    parser.add_argument('--restore', action='store_true', help='Restore original MAC address')
    parser.add_argument('--show', action='store_true', help='Show current and original MAC address')
    
    args = parser.parse_args()
    
    current_mac = get_current_mac(args.interface)
    if not current_mac:
        print(f"[!] Could not get current MAC address for {args.interface}")
        return
    
    # Save original MAC if we haven't seen this interface before
    original_mac = get_original_mac(args.interface)
    if not original_mac:
        save_original_mac(args.interface, current_mac)
        original_mac = current_mac
    
    if args.show:
        print(f"Current MAC for {args.interface}: {current_mac}")
        print(f"Original MAC for {args.interface}: {original_mac}")
        return
        
    if args.restore:
        print(f"[*] Restoring original MAC address for {args.interface}")
        set_mac_address(args.interface, original_mac)
        return
    
    # Change MAC address
    new_mac = args.mac if args.mac else generate_random_mac()
    set_mac_address(args.interface, new_mac)

if __name__ == "__main__":
    main()
