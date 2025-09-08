import re
from collections import defaultdict

def parse_nation_balances(filename):
    nation_balances = defaultdict(float)
    
    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
        
        nation_pattern = re.compile(r'This land belongs to nation ([^:]+)')
        balance_pattern = re.compile(r'Balance: \$([\d,]+\.\d{2})')
        
        entries = content.split('----------------------------------------')
        
        for entry in entries:
            nation_match = nation_pattern.search(entry)
            balance_match = balance_pattern.search(entry)
            
            if nation_match and balance_match:
                nation = nation_match.group(1).strip()
                balance = float(balance_match.group(1).replace(',', ''))
                
                nation_balances[nation] += balance
    
    return nation_balances


input_filename = 'markers.txt'
output_filename = 'balance.txt'

nation_wealth = parse_nation_balances(input_filename)


with open(output_filename, 'w', encoding='utf-8') as output_file:
    for nation, total_balance in nation_wealth.items():
        output_file.write(f"{nation}: ${total_balance:,.2f}\n")

print(f"Results saved to {output_filename}")
