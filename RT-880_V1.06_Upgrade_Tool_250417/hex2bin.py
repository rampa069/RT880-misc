import sys
from firmware_data import FIRMWARE_HEX

def char_to_int(word):
    """Convert a hex character to its integer value"""
    num = ord(word)
    if 47 < num < 58:  # 0-9
        return num - 48
    if 64 < num < 71:  # A-F
        return num - 55
    if 96 < num < 103:  # a-f
        return num - 87
    raise ValueError(f"Invalid hex character: {word}")

def process_hex_data(hex_data):
    """Process hex data and return binary data"""
    binary_data = bytearray(251904)  # Same size as in updater
    write_step = 0
    base_address = 0
    
    print(f"Hex data length: {len(hex_data)}")
    print(f"First 100 characters of hex data: {hex_data[:100]}")
    
    # Split the data into blocks by colon
    blocks = hex_data.split(':')
    print(f"Number of blocks found: {len(blocks)}")
    
    for block in blocks:
        if not block:  # Skip empty blocks
            continue
            
        try:
            if len(block) < 10:  # Minimum valid block length (1 byte length + 2 byte addr + 1 byte type + 1 byte data + 1 byte checksum)
                continue
                
            # Get length (first byte)
            length = char_to_int(block[0]) << 4
            length += char_to_int(block[1])
            
            # Get address (next two bytes)
            addr = char_to_int(block[2]) << 12
            addr += char_to_int(block[3]) << 8
            addr += char_to_int(block[4]) << 4
            addr += char_to_int(block[5])
            
            # Get record type
            record_type = char_to_int(block[6]) << 4
            record_type += char_to_int(block[7])
            
            # Calculate final address based on base address
            final_addr = addr - 0x2800
            if write_step > 0:
                final_addr = final_addr - (write_step - 1) * 0x10000
            
            if record_type == 0:  # Data record
                print(f"\nData block - Length: {length}, Address: 0x{addr:04X}, Final Address: 0x{final_addr:04X}")
                print(f"Raw data: {block[8:8+length*2]}")
                
                # Process data bytes
                for i in range(length):
                    if 8 + i * 2 + 1 >= len(block):
                        print(f"Warning: Block data truncated at byte {i}")
                        break
                    
                    byte = char_to_int(block[8 + i * 2]) << 4
                    byte += char_to_int(block[8 + i * 2 + 1])
                    
                    if 0 <= final_addr + i < len(binary_data):
                        binary_data[final_addr + i] = byte
                        print(f"  Byte {i}: 0x{byte:02X} at address 0x{final_addr + i:04X}")
                    else:
                        print(f"Warning: Address 0x{final_addr + i:04X} out of range")
                
            elif record_type == 1:  # End of file record
                print("\nEnd of file record found")
                break
                
            elif record_type == 4:  # Extended linear address record
                if length != 2:
                    print(f"Warning: Extended address record with unexpected length {length}")
                    continue
                    
                base_address = char_to_int(block[8]) << 12
                base_address += char_to_int(block[9]) << 8
                base_address += char_to_int(block[10]) << 4
                base_address += char_to_int(block[11])
                write_step += 1
                print(f"\nExtended linear address record - New base address: 0x{base_address:04X}, Write step: {write_step}")
            
            else:
                print(f"Warning: Unknown record type {record_type:02X}")
                
        except Exception as e:
            print(f"\nError processing block: {e}")
            print(f"Problematic block: {block[:20]}...")
            continue
            
    # Print some statistics
    non_zero = sum(1 for b in binary_data if b != 0)
    print(f"\nBinary data statistics:")
    print(f"Total bytes: {len(binary_data)}")
    print(f"Non-zero bytes: {non_zero}")
    print(f"Zero bytes: {len(binary_data) - non_zero}")
    
    # Print first 32 bytes of binary data
    print("\nFirst 32 bytes of binary data:")
    for i in range(0, 32, 16):
        hex_line = ' '.join(f"{b:02X}" for b in binary_data[i:i+16])
        print(f"0x{i:04X}: {hex_line}")
    
    # Print some non-zero sections
    print("\nSome non-zero sections:")
    for i in range(0, len(binary_data), 0x1000):
        section = binary_data[i:i+0x1000]
        if any(b != 0 for b in section):
            print(f"\nSection at 0x{i:04X}:")
            for j in range(0, len(section), 16):
                if any(b != 0 for b in section[j:j+16]):
                    hex_line = ' '.join(f"{b:02X}" for b in section[j:j+16])
                    print(f"0x{i+j:04X}: {hex_line}")
    
    return binary_data

def main():
    try:
        print("Processing firmware hex data...")
        binary_data = process_hex_data(FIRMWARE_HEX)
        
        print("\nWriting binary file...")
        with open("firmware.bin", "wb") as f:
            f.write(binary_data)
            
        print("Successfully created firmware.bin")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 