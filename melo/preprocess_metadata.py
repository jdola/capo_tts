from melo.text.symbols import symbols
from melo.text.cleaner import language_module_map, clean_text
import pandas as pd
import sys

def check_valid_transcript(audio_info):
    if len(audio_info[2]) < 2:
        print(f"transcript too short: {audio_info[2]}")
        return False
    norm_text, phones, tones, word2ph = clean_text(audio_info[3], audio_info[2])
    for ph in phones:
        if ph not in symbols:
            print(f"Invalid phone: {ph} in text {audio_info[3]}")
            return False
    return True

def pronunciate_transcript(audio_info):
    norm_text, phones, tones, word2ph = clean_text(audio_info[3], audio_info[2])
    return norm_text, phones, tones, word2ph

def clean_metadata_transcript(metadata_path):
    pdf = pd.read_csv(metadata_path, sep='|', header=None)
    pdf_valid = pdf[pdf.apply(check_valid_transcript, axis =1)]
    pdf_valid.to_csv(metadata_path.replace('.csv','_valid.csv'), sep='|', header=None, index=None)


def main():
    if len(sys.argv) < 2:
        print("Usage: python preprocess_metadata.py <metadata_path>")
        return

    metadata_path = sys.argv[1]
    clean_metadata_transcript(metadata_path)

if __name__ == "__main__":
    main()