import asyncio
from bleak import BleakClient, BleakScanner
from Crypto.Cipher import AES

# -----------------------------
# Replace with your Mi Band 10 MAC and key
# -----------------------------
BAND_MAC = "04:34:C3:2F:57:5B"  # Your band MAC
AUTH_KEY = bytes.fromhex("00112233445566778899AABBCCDDEEFF")  # 16-byte key

# -----------------------------
# GATT UUIDs
# -----------------------------
AUTH_SERVICE = "0000fee1-0000-1000-8000-00805f9b34fb"
AUTH_CHAR = "00000009-0000-3512-2118-0009af100700"
HR_MEASURE = "00002a37-0000-1000-8000-00805f9b34fb"
HR_CONTROL = "00002a39-0000-1000-8000-00805f9b34fb"

# -----------------------------
# Callbacks
# -----------------------------
def handle_hr(sender, data):
    if len(data) > 1:
        print("❤️ Heart Rate:", data[1], "BPM")

def handle_auth(sender, data):
    print("Auth Response:", data)
    # Step 2-3 of authentication (AES encryption) goes here

# -----------------------------
# Main async function
# -----------------------------
async def main():
    print("Scanning for Mi Band 10...")
    devices = await BleakScanner.discover()
    for d in devices:
        if "Band" in str(d.name):
            print("Found:", d)
            global BAND_MAC
            BAND_MAC = d.address

    async with BleakClient(BAND_MAC) as client:
        print("Connected:", client.is_connected)

        # Enable auth notifications
        await client.start_notify(AUTH_CHAR, handle_auth)

        # Step 1: send key
        await client.write_gatt_char(AUTH_CHAR, b'\x01\x08' + AUTH_KEY)

        # Step 2: request challenge (band sends random)
        await client.write_gatt_char(AUTH_CHAR, b'\x02\x08')

        # Step 3: normally encrypt challenge and send back (AES-128 ECB)
        # handle in handle_auth() callback

        # ---- Heart Rate ----
        await client.start_notify(HR_MEASURE, handle_hr)

        # Start HR measurement
        await client.write_gatt_char(HR_CONTROL, b'\x15\x02\x01')

        print("Reading HR in real-time...")
        await asyncio.sleep(60)  # listen for 1 minute

        # Stop HR notifications
        if client.is_connected:
            await client.stop_notify(HR_MEASURE)

asyncio.run(main())