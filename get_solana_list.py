import sqlite3
import json

# Connect to the SQLite database (adjust the path to your DB file)
conn = sqlite3.connect('ussd.sqlite3')
cursor = conn.cursor()

# Function to retrieve Solana encrypted list based on thread_id (formerly phone_number)
def get_solana_list(thread_id):
    try:
        cursor.execute("SELECT solana_integer FROM solana WHERE thread_id = ?", (thread_id,))
        result = cursor.fetchone()
        
        if result:
            solana_list = json.loads(result[0])  # Safe JSON decoding
            return solana_list
        else:
            print("Thread ID not found in the database.")
            return None
    except (sqlite3.Error, json.JSONDecodeError) as e:
        print(f"Error retrieving or decoding data: {e}")
        return None
    finally:
        conn.close()

# Example usage
thread_id = input("Enter the thread ID: ")
solana_list = get_solana_list(thread_id)

if solana_list:
    # Create a dictionary with thread_id and solana_list
    output_data = {
        "thread_id": thread_id,
        "solana_list": solana_list
    }
    
    # Write to JSON file
    output_file = f"solana_data_{thread_id}.json"
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"Data has been saved to {output_file}")
    print(f"Solana list for thread ID {thread_id}: {json.dumps(solana_list, indent=2)}")