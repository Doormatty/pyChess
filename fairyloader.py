from bs4 import BeautifulSoup
import requests
import ujson

webpage=requests.get('https://en.wikipedia.org/wiki/List_of_fairy_chess_pieces')

# Parse HTML
soup = BeautifulSoup(webpage.text, 'html.parser')

# Find the table containing fairy chess pieces
table = soup.find('table', {'class': 'wikitable'})
rows = table.find_all('tr')

# Extract the relevant data from the table: Name and Parlett column
chess_pieces = []

for row in rows[1:]:  # skip header row
    cols = row.find_all('td')
    if len(cols) > 5:
        name = cols[0].get_text(strip=True)
        bcps = cols[1].get_text(strip=True)
        parlett = cols[2].get_text(strip=True)
        betza = cols[3].get_text(strip=True)
        notes = cols[5].get_text(strip=True)
        chess_pieces.append({'name': name, 'bcps': bcps, 'parlett': parlett, 'betza': betza, 'notes': notes})

ujson.dump(chess_pieces, open('tests/chess_pieces.json', 'w'))
