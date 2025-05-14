# SolText  

![SolText Logo](/assets/soltext-logo.png "Send crypto via SMS")  

### 🔗 Links  
- [GitHub Repo](https://github.com/dayosalam/ussd_llm)  
- [Twitter](https://twitter.com/soltext_)  

## 📖 Table of Contents  
- [Core Features](#core-features)  
- [Technical Implementation](#technical-implementation)  
- [Database Structure](#database-structure)  
- [Installation](#installation)  
- [Transaction Flow](#transaction-flow)  
- [Contributing](#contributing)  

---

## 💡 **Core Features**  
- **SMS/USSD Gateway**: Process crypto transactions via text messages  
- **Regex Parsing**: Extracts amounts/wallets from natural language  
- **SQLite3 Backend**: Stores user IDs and transaction history  
- **Solana Integration**: Manages on-chain operations  

---

## ⚙️ **Technical Implementation**  
### Key Components  
| File | Functionality |  
|------|--------------|  
| `llm.py` | Regex pattern matching for transaction parsing |  
| `ussd.py` | USSD/SMS gateway interface |  
| `get_solana_list.py` | Manages Solana address book in SQLite |  
| `solana_data_*.json` | User-specific transaction logs |  

### Database Schema  
```python
# ussd.sqlite3 structure:
# - users (phone_number, solana_wallet)
# - transactions (tx_hash, amount, timestamp)
# - solana_list (validated_addresses)
```


# Installation
```
git clone https://github.com/dayosalam/ussd_llm
cd ussd_llm
pip install -r requirements.txt

# Installs:
# - sqlite3
# - Solana.py
# - regex libraries
```

# Configure .env
```
SOLANA_RPC_URL=your_node_url
DATABASE_PATH=ussd.sqlite3
```


