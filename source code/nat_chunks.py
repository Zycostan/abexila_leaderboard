import re
from collections import defaultdict

def parse_nation_chunks(filename):
    nation_chunks = defaultdict(int)
    
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()

        nation_pattern = re.compile(r'This land belongs to nation ([^:]+)')
        chunks_pattern = re.compile(r'Chunks: (\d+)')
        
        entries = content.split('----------------------------------------')
        
        for entry in entries:
            nation_match = nation_pattern.search(entry)
            chunks_match = chunks_pattern.search(entry)
            
            if nation_match and chunks_match:
                nation = nation_match.group(1).strip()
                chunks = int(chunks_match.group(1))
                
                nation_chunks[nation] += chunks
    
    return nation_chunks


input_filename = 'markers.txt'
output_filename = 'chunks.txt'

nation_chunks = parse_nation_chunks(input_filename)

with open(output_filename, 'w', encoding='utf-8') as output_file:
    for nation, total_chunks in nation_chunks.items():
        output_file.write(f"{nation}: {total_chunks} chunks\n")

print(f"Results saved to {output_filename}")
