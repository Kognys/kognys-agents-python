# kognys/services/blockchain_client.py
import os
from web3 import Web3

# --- Configuration ---
BNB_TESTNET_RPC_URL = "https://data-seed-prebsc-1-s1.binance.org:8545/"
CONTRACT_ADDRESS = os.getenv("MEMBASE_CONTRACT_ADDRESS")
SENDER_ADDRESS = os.getenv("MEMBASE_ACCOUNT")
PRIVATE_KEY = os.getenv("MEMBASE_SECRET_KEY")

# A minimal ABI for a function that stores a hash.
MINIMAL_CONTRACT_ABI = [
    {
        "constant": False,
        "inputs": [
            {
                "name": "dataHash",
                "type": "bytes32"
            }
        ],
        "name": "storeHash",
        "outputs": [],
        "payable": False,
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

def publish_hash_on_chain(data_hash: str) -> str | None:
    """
    Sends a real transaction to a smart contract on the BNB Testnet to store a hash.
    """
    if not all([CONTRACT_ADDRESS, SENDER_ADDRESS, PRIVATE_KEY]):
        print("--- BLOCKCHAIN CLIENT: ERROR - Missing contract or wallet environment variables. ---")
        return None

    try:
        # 1. Connect to the BNB Testnet
        w3 = Web3(Web3.HTTPProvider(BNB_TESTNET_RPC_URL))
        if not w3.is_connected():
            print("--- BLOCKCHAIN CLIENT: ERROR - Could not connect to BNB Testnet RPC. ---")
            return None

        # 2. Load the smart contract
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=MINIMAL_CONTRACT_ABI)

        # 3. Build the transaction
        hash_bytes = bytes.fromhex(data_hash)
        
        tx = contract.functions.storeHash(hash_bytes).build_transaction({
            'chainId': 97, # BNB Testnet Chain ID
            'from': SENDER_ADDRESS,
            'nonce': w3.eth.get_transaction_count(SENDER_ADDRESS),
            'gas': 200000,
            'gasPrice': w3.to_wei('10', 'gwei')
        })

        # 4. Sign the transaction
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)

        # 5. Send the transaction
        print("--- BLOCKCHAIN CLIENT: Sending transaction to BNB Testnet... ---")
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # 6. Wait for the transaction receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        tx_hash_hex = tx_hash.hex()
        print(f"--- BLOCKCHAIN CLIENT: Transaction successful! Tx Hash: {tx_hash_hex} ---")
        return tx_hash_hex

    except Exception as e:
        print(f"--- BLOCKCHAIN CLIENT: Error sending transaction: {e} ---")
        return None