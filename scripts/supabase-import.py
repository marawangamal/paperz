import csv
from pathlib import Path
from typing import List, Dict
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from tqdm import tqdm

BATCH_SIZE = 100  # Number of records to insert at once

class SupabaseImporter:
    def __init__(self, venues_path: str, papers_path: str):
        # Load environment variables
        load_dotenv()
        
        # Initialize Supabase client
        url: str = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
        key: str = os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY')
        if not url or not key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env file")
        
        self.supabase: Client = create_client(url, key)
        self.venues_path = Path(venues_path)
        self.papers_path = Path(papers_path)
        
        # Verify files exist
        if not self.venues_path.exists():
            raise FileNotFoundError(f"Venues file not found: {venues_path}")
        if not self.papers_path.exists():
            raise FileNotFoundError(f"Papers file not found: {papers_path}")

    def read_csv(self, filepath: Path) -> List[Dict]:
        """Read CSV file and return list of dictionaries"""
        data = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert empty strings to None
                processed_row = {k: (v if v != '' else None) for k, v in row.items()}
                
                # Convert string lists (authors) to actual lists
                if 'authors' in processed_row and processed_row['authors']:
                    processed_row['authors'] = processed_row['authors'].split('|')
                
                # Convert year to integer if present
                if 'year' in processed_row and processed_row['year']:
                    processed_row['year'] = int(processed_row['year'])
                
                data.append(processed_row)
                
        return data

    def batch_data(self, data: List[Dict], batch_size: int) -> List[List[Dict]]:
        """Split data into batches"""
        return [data[i:i + batch_size] for i in range(0, len(data), batch_size)]

    def import_venues(self) -> Dict[str, str]:
        """Import venues data to Supabase and return mapping of (abbrev,year) to id"""
        print("Importing venues...")
        venues = self.read_csv(self.venues_path)
        venue_mapping = {}
        
        # Split into batches
        batches = self.batch_data(venues, BATCH_SIZE)
        
        with tqdm(total=len(venues), desc="Venues", unit="venue", leave=False) as pbar:
            for batch in batches:
                try:
                    # Prepare batch data
                    batch_data = [{
                        'name': venue['name'],
                        'abbrev': venue['abbrev'],
                        'year': venue['year'],
                    } for venue in batch]
                    
                    # Insert batch
                    result = self.supabase.table('venues').upsert(
                        batch_data,
                        on_conflict='abbrev,year'
                    ).execute()
                    
                    # Update mapping
                    for row in result.data:
                        key = (row['abbrev'], row['year'])
                        venue_mapping[key] = row['id']
                    
                    pbar.update(len(batch))
                    
                except Exception as e:
                    print(f"\nError importing venue batch: {str(e)}")
        
        print(f"Imported {len(venues)} venues")
        return venue_mapping

    def import_papers(self, venue_mapping: Dict[str, str]) -> None:
        """Import papers data to Supabase"""
        print("Importing papers...")
        papers = self.read_csv(self.papers_path)
        
        # Split into batches
        batches = self.batch_data(papers, BATCH_SIZE)
        
        with tqdm(total=len(papers), desc="Papers", unit="paper", leave=False) as pbar:
            for batch in batches:
                try:
                    # Prepare batch data with venue_ids
                    batch_data = []
                    seen_keys = set()  # Track unique combinations of venue_id and title
                    
                    for paper in batch:
                        venue_key = (paper['venue_abbrev'], int(paper['venue_year']))
                        venue_id = venue_mapping.get(venue_key)
                        
                        if not venue_id:
                            print(f"\nVenue not found for paper: {paper['title']}")
                            continue
                        
                        # Create a normalized title (assuming you have a function for this)
                        normalized_title = paper['title']
                        
                        # Check for duplicates within the batch
                        unique_key = (venue_id, normalized_title)
                        if unique_key in seen_keys:
                            print(f"\nDuplicate paper found: {paper['title']}")
                            continue
                        
                        seen_keys.add(unique_key)
                        batch_data.append({
                            'title': paper['title'],
                            'authors': paper['authors'],
                            'abstract': paper['abstract'],
                            'venue_id': venue_id,
                            'pdf_url': paper['pdf_url'],
                            'code_url': paper['code_url']
                        })
                    
                    # Insert batch
                    if batch_data:  # Only insert if we have valid papers
                        self.supabase.table('papers').upsert(
                            batch_data,
                            on_conflict='venue_id,normalized_title'
                        ).execute()
                    
                    pbar.update(len(batch))
                    
                except Exception as e:
                    print(f"\nError importing paper batch: {str(e)}")
            
            print(f"Imported {len(papers)} papers")

    def import_all(self) -> None:
        """Import all data to Supabase"""
        # First import venues and get mapping
        venue_mapping = self.import_venues()
        # Then import papers using venue mapping
        self.import_papers(venue_mapping)
        print("Import completed!")

if __name__ == "__main__":
    # Get path relative to the script location
    script_dir = Path(__file__).parent
    root_dir = script_dir.parent
    
    venues_path = root_dir / "dumps/icml/venues.csv"
    papers_path = root_dir / "dumps/icml/papers.csv"
    
    importer = SupabaseImporter(
        venues_path=venues_path,
        papers_path=papers_path
    )
    importer.import_all()