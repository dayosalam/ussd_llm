import sqlite3

# Connect to the SQLite database (adjust the path to your DB file)
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Function to retrieve Solana encrypted list based on phone number
def get_solana_list(phone_number):
    try:
        # Query the database for the Solana list associated with the phone number
        cursor.execute("SELECT solana_list FROM users WHERE phone_number = ?", (phone_number,))
        result = cursor.fetchone()  # Fetch the first result
        
        # If result exists, return the Solana list (make sure it is a list of integers)
        if result:
            solana_list = eval(result[0])  # Convert string to list
            return solana_list
        else:
            print("Phone number not found in the database.")
            return None
    except sqlite3.Error as e:
        print(f"Error retrieving data: {e}")
        return None
    finally:
        conn.close()  # Close the connection when done

# Example usage
phone_number = input("Enter the phone number: ")
solana_list = get_solana_list(phone_number)

if solana_list:
    print(f"Solana list for phone number {phone_number}: {solana_list}")
