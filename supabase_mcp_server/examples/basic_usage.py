"""
Basic usage example for Supabase MCP Server
"""

import asyncio
from src.supabase_mcp.supabase_client import SupabaseClient


async def main():
    """Example usage of Supabase client"""
    
    # Initialize client
    client = SupabaseClient()
    
    # Example 1: Query data
    print("Querying users table...")
    users = await client.query_table(
        table_name="users",
        select="id, email, created_at",
        filters={"active": True},
        limit=10
    )
    print(f"Found {len(users)} users")
    
    # Example 2: Insert data
    print("\nInserting new user...")
    new_user = await client.insert_data(
        table_name="users",
        data={
            "email": "test@example.com",
            "name": "Test User",
            "active": True
        }
    )
    print(f"Created user: {new_user}")
    
    # Example 3: Update data
    print("\nUpdating user...")
    updated_users = await client.update_data(
        table_name="users",
        data={"name": "Updated Name"},
        filters={"email": "test@example.com"}
    )
    print(f"Updated {len(updated_users)} users")
    
    # Example 4: Delete data
    print("\nDeleting user...")
    deleted_users = await client.delete_data(
        table_name="users",
        filters={"email": "test@example.com"}
    )
    print(f"Deleted {len(deleted_users)} users")


if __name__ == "__main__":
    asyncio.run(main())
