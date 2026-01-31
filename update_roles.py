import sqlite3

# Update role from انقلابی to میهن‌پرست
conn = sqlite3.connect('secure_bot.db')
cursor = conn.cursor()

# First check what roles exist
cursor.execute("SELECT DISTINCT role FROM users")
roles = cursor.fetchall()
print(f'Current roles in database: {roles}')

# Update the role
cursor.execute("UPDATE users SET role = ? WHERE role = ?", ('میهن‌پرست', 'انقلابی'))
conn.commit()

print(f'Updated {cursor.rowcount} user records')

# Check again
cursor.execute("SELECT DISTINCT role FROM users")
roles = cursor.fetchall()
print(f'Roles after update: {roles}')

conn.close()
print('Done!')
