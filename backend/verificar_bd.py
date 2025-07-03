import sqlite3

conn = sqlite3.connect('devoluciones.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM devoluciones')
cantidad = cursor.fetchone()[0]

print(f'Cantidad de devoluciones registradas: {cantidad}')

conn.close()
