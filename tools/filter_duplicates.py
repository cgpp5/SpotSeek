import csv
import os
import sys
import unicodedata

def normalize(text):
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    return text.lower().replace(" ", "")

def filter_and_prepare(input_csv, music_dir, output_csv):
    print(f"Scanning audio files in: {music_dir}...")
    
    local_files = []
    extensions = ('.mp3', '.flac', '.m4a', '.wav', '.ogg', '.aac', '.wma')
    
    for root, _, files in os.walk(music_dir):
        for file in files:
            if file.lower().endswith(extensions):
                local_files.append(normalize(file))
                
    print(f"Indexed {len(local_files)} local tracks.")
    print("Comparing with exported playlist...")
    
    missing_tracks = []
    try:
        with open(input_csv, mode='r', encoding='utf-8') as f_in:
            reader = csv.DictReader(f_in)
            for row in reader:
                artist = row.get('Artist', '')
                track = row.get('Track', '')
                album = row.get('Album', '')
                
                track_norm = normalize(track)
                artist_norm = normalize(artist)
                
                found = False
                for local_file in local_files:
                    if track_norm in local_file and artist_norm in local_file:
                        found = True
                        break
                        
                if not found:
                    missing_tracks.append([artist, track, album])
                    
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
        
    try:
        with open(output_csv, mode='w', newline='', encoding='utf-8') as f_out:
            writer = csv.writer(f_out)
            # Cabeceras estándar que slsk-batchdl reconoce nativamente
            writer.writerow(['Artist Name', 'Track Name', 'Album'])
            writer.writerows(missing_tracks)
                
        print(f"Done. {len(missing_tracks)} tracks missing and ready for download.")
        print(f"Download list saved to: {output_csv}")
    except Exception as e:
        print(f"Error writing output file: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python filter_duplicates.py <INPUT_CSV> <MUSIC_DIR> <OUTPUT_CSV>")
    else:
        filter_and_prepare(sys.argv[1], sys.argv[2], sys.argv[3])