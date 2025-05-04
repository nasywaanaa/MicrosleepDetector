import pandas as pd
from components.generate_data import generate_data
from mongodb_connection import get_mongo_client

def insert_dummy_to_mongodb(n=300):
    dummy_df = generate_data(n=n)

    # Pastikan format dan kolom sesuai
    expected_cols = ['nama_sopir', 'timestamp', 'armada', 'rute', 'status_alert']
    for col in expected_cols:
        if col not in dummy_df.columns:
            raise ValueError(f"Kolom '{col}' tidak ditemukan di dummy data.")
    
    dummy_df['timestamp'] = pd.to_datetime(dummy_df['timestamp'])
    records = dummy_df[expected_cols].to_dict(orient='records')

    collection = get_mongo_client()
    result = collection.insert_many(records)
    print(f"{len(result.inserted_ids)} data dummy berhasil disisipkan ke MongoDB.")

if __name__ == "__main__":
    insert_dummy_to_mongodb(n=300)
