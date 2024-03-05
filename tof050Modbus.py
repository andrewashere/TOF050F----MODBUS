import serial
import time

# Constants
ToF050_TX_data_packet_size = 8
ToF050_RX_data_packet_size = 10

ToF050_slave_default_ID = 0x01

# Registers dictionary
registers = {
    "special" : 0x0001,
    "slave_id" : 0x0002,
    "baud_rate" : 0x0003,
    "range_precision" : 0x0004,
    "output_control" : 0x0005,
    "load_calibration" : 0x0006,
    "offset_correction" : 0x0007,
    "xtalk_correction" : 0x0008,
    "i2c_enable" : 0x0009,
    "measurement" : 0x0010,
    "offset_calibration" : 0x0020,
    "xtalk_calibration" : 0x0021,
}

# Modbus function codes
MODBUS_READ_HOLDING_REGISTERS = 0x03
MODBUS_WRITE_HOLDING_REGISTERS = 0x06

def generate_CRC16(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, 'little')

def modbus_tx(serial_port, slave_id, function_code, register, value):
    payload = bytearray([slave_id, function_code]) + register.to_bytes(2, 'big') + value.to_bytes(2, 'big')
    crc = generate_CRC16(payload)
    serial_port.write(payload + crc)
    time.sleep(0.1)  # Increased delay for device response

def modbus_rx(serial_port, expected_length):
    time.sleep(0.5)  # Give some time for the response to be fully received
    if serial_port.in_waiting > 0:
        return serial_port.read(expected_length)
    return None

def interpret_response(response):
    # Check if response length matches expected
    if len(response) != ToF050_RX_data_packet_size:
        print("Invalid response length.")
        return
    # Extract measurement from response (assuming measurement is at byte 3 and 4)
    measurement = int.from_bytes(response[3:5], byteorder='big')
    print(f"Measurement: {measurement} mm")

# Initialize serial port
ser = serial.Serial('/dev/ttyAMA0', 115200, timeout=2)

try:
    while True: 
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        # Send Modbus request
        modbus_tx(ser, ToF050_slave_default_ID, MODBUS_READ_HOLDING_REGISTERS, registers["measurement"], 1)

        # Receive Modbus response
        response = modbus_rx(ser, ToF050_RX_data_packet_size)
        if response:
            interpret_response(response)
        else:
            print("No response received.")
        time.sleep(1)  # Delay between measurements
except KeyboardInterrupt:
    print("\nProgram terminated by user.")
finally:
    ser.close()
    print("Serial port closed.")
