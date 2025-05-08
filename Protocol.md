# RT-880 Firmware Update Protocol

This document describes the communication protocol and firmware update flow for the RT-880 radio.

## Communication Protocol

### Serial Port Configuration
- Baud Rate: 115200
- Data Bits: 8
- Stop Bits: 1
- Parity: None
- Flow Control: None

### Command Sequence

1. **Connection Command**
   ```
   [0x39, 0x33, 0x05, 0x10, 0xD3]
   ```
   - 0x39: '9'
   - 0x33: '3'
   - 0x05: Command length
   - 0x10: Command type (Connection)
   - 0xD3: Checksum

2. **Update Command**
   ```
   [0x39, 0x33, 0x05, 0x55, 0x24]
   ```
   - 0x39: '9'
   - 0x33: '3'
   - 0x05: Command length
   - 0x55: Command type (Update)
   - 0x24: Checksum

3. **End Command**
   ```
   [0x39, 0x33, 0x05, 0xEE, 0xB1]
   ```
   - 0x39: '9'
   - 0x33: '3'
   - 0x05: Command length
   - 0xEE: Command type (End)
   - 0xB1: Checksum

### Device Responses

1. **Success Response**
   ```
   [0x06]
   ```
   - 0x06: ACK (Acknowledge)

2. **Error Response**
   ```
   [0xFF]
   ```
   - 0xFF: NACK (Negative Acknowledge)

3. **Start Response**
   ```
   [0x00]
   ```
   - 0x00: Indicates device is ready to receive data

## Update Flow

1. **Preparation**
   - Connect data cable
   - Select COM port
   - Hold PTT key while powering on the radio

2. **Connection Sequence**
   - Send connection command
   - Wait for ACK response (0x06)
   - Repeat up to 3 times if no response
   - If no response after 3 attempts, display error

3. **Update Start**
   - Send update command
   - Wait for ACK response (0x06)
   - Wait for start response (0x00)

4. **Data Transfer**
   - Send 1024-byte blocks
   - Each block includes:
     - Start byte (0x57)
     - Block counter (2 bytes)
     - Data (1024 bytes)
     - Checksum
   - Wait for ACK (0x06) after each block
   - Update progress bar

5. **Completion**
   - Send end command
   - Wait for ACK response (0x06)
   - Display completion message

## Firmware Structure

The firmware is in Intel HEX format and contains:
- Vector table for ARM Cortex-M
- Application code
- Configuration data

### Firmware Characteristics
- Total size: 251904 bytes
- Base address: 0x08000000
- Initial Stack Pointer: 0x20009290
- Reset Vector: 0x08002ac0

## Error Handling

1. **Communication Errors**
   - Response timeouts
   - NACK responses
   - Serial port errors

2. **Data Errors**
   - Incorrect checksum
   - Corrupted data block
   - Out of range address

## Security Notes

1. **Firmware Verification**
   - Validate firmware checksum
   - Verify Intel HEX format
   - Check valid addresses

2. **Recovery**
   - In case of failure, radio may require reset
   - Keep backup of original firmware

## System Requirements

- Operating System: Windows/Linux
- Available serial port
- Serial port access permissions
- Sufficient disk space for firmware 