import csv
import sys
from spotapi import PublicPlaylist

def export_playlist(playlist_url, output_file):
    print("Fetching playlist data from Spotify...")
    extracted_tracks = []
    
    try:
        playlist = PublicPlaylist(playlist_url)
        pages = playlist.paginate_playlist()
        
        for page in pages:
            items = page.get("items", [])
            
            for item in items:
                track_data = item.get("itemV2", {}).get("data", {})
                
                if track_data.get("__typename") not in ["Track", "LocalTrack"]:
                    continue
                    
                # 1. Extract Track
                track_name = track_data.get("name", "Unknown")
                
                # 2. Extract Album
                album = track_data.get("albumOfTrack", {}).get("name", "Unknown")
                
                # 3. Extract Artist
                artists_track = track_data.get("artists", {}).get("items", [])
                if artists_track:
                    artist = artists_track[0].get("profile", {}).get("name", "Unknown")
                else:
                    artist = "Unknown"
                    
                extracted_tracks.append([artist, album, track_name])
                
    except Exception as e:
        print(f"Error processing playlist: {e}")
        return

    # Save data cleanly to CSV
    try:
        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Artist', 'Album', 'Track'])
            writer.writerows(extracted_tracks)
            
        print(f"Success: {len(extracted_tracks)} tracks exported to {output_file}")
    except Exception as e:
        print(f"Error writing to file: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python spotify_export.py <PLAYLIST_URL> <OUTPUT_CSV>")
    else:
        export_playlist(sys.argv[1], sys.argv[2])
