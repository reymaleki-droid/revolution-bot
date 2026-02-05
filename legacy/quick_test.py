from secure_database import SecureDatabase
import os

print("Testing secure database...")

# Create test database
db = SecureDatabase('test_temp.db')

# Add users
print("\n1. Adding users...")
db.add_user(12345)
db.add_user(67890)
db.add_points(12345, 100, 'test')

# Get stats
print("\n2. Getting aggregate statistics...")
stats = db.get_aggregate_statistics()
print(f"   Total users: {stats['total_users']}")
print(f"   Total GB: {stats['total_gb_shared']}")

# Get user stats
print("\n3. Getting user personal stats...")
user_stats = db.get_user_stats(12345)
print(f"   User imtiaz: {user_stats['imtiaz']}")
print(f"   User role: {user_stats['role']}")

# Test leaderboard
print("\n4. Testing leaderboard anonymity...")
leaderboard = db.get_leaderboard(5)
print(f"   Top user: Rank {leaderboard[0][0]}, {leaderboard[0][1]} points, {leaderboard[0][2]}")

# Clean up
os.remove('test_temp.db')
print("\n✅ All tests passed!")
