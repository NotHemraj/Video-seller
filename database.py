"""
Database module for the Telegram bot.
Handles storage and retrieval of videos and user data.
"""

import json
import os
from typing import Dict, List, Any, Optional

class Database:
    def __init__(self, database_file: str):
        self.database_file = database_file
        self.data = {
            "videos": {},
            "users": {}
        }
        self.load_database()
    
    def load_database(self) -> None:
        """Load database from file if it exists."""
        if os.path.exists(self.database_file):
            try:
                with open(self.database_file, 'r') as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                print("Error loading database, creating new one")
                self.save_database()
        else:
            self.save_database()
    
    def save_database(self) -> None:
        """Save database to file."""
        with open(self.database_file, 'w') as f:
            json.dump(self.data, f, indent=4)
    
    # Video methods
    def add_video(self, video_data: Dict[str, Any]) -> str:
        """Add a new video to the database."""
        # Validate required fields
        required_fields = ["title", "description", "price"]
        for field in required_fields:
            if field not in video_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate price is a positive integer
        try:
            price = int(video_data["price"])
            if price <= 0:
                raise ValueError("Price must be a positive number")
            video_data["price"] = price
        except (ValueError, TypeError):
            raise ValueError("Price must be a valid number")
        
        # Find the highest existing video ID number and increment by 1
        highest_id = 0
        for existing_id in self.data['videos'].keys():
            if existing_id.startswith('video_'):
                try:
                    id_num = int(existing_id.split('_')[1])
                    highest_id = max(highest_id, id_num)
                except (ValueError, IndexError):
                    pass
        
        # Generate a new unique ID that won't be reused even after deletions
        video_id = video_data.get("id", f"video_{highest_id + 1}")
        video_data["id"] = video_id
        self.data["videos"][video_id] = video_data
        self.save_database()
        return video_id
    
    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get video by ID."""
        return self.data["videos"].get(video_id)
    
    def get_all_videos(self) -> Dict[str, Dict[str, Any]]:
        """Get all videos."""
        return self.data["videos"]
    
    def update_video(self, video_id: str, video_data: Dict[str, Any]) -> bool:
        """Update video data."""
        if video_id in self.data["videos"]:
            video_data["id"] = video_id  # Ensure ID remains the same
            self.data["videos"][video_id] = video_data
            self.save_database()
            return True
        return False
    
    def remove_video(self, video_id: str) -> bool:
        """Remove video by ID."""
        if video_id in self.data["videos"]:
            del self.data["videos"][video_id]
            self.save_database()
            return True
        return False
    
    # User methods
    def add_user(self, user_id: int, username: str, is_admin: bool = False) -> None:
        """Add a new user or update existing user."""
        if str(user_id) not in self.data["users"]:
            self.data["users"][str(user_id)] = {
                "user_id": user_id,
                "username": username,
                "is_admin": is_admin,
                "purchases": []
            }
            self.save_database()
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        return self.data["users"].get(str(user_id))
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin."""
        user = self.get_user(user_id)
        return user is not None and user.get("is_admin", False)
    
    def add_purchase(self, user_id: int, video_id: str, price: int) -> bool:
        """Add a purchase record for a user."""
        user = self.get_user(user_id)
        if user:
            import time
            purchase = {
                "video_id": video_id,
                "purchase_date": int(time.time()),
                "price_paid": price
            }
            user["purchases"].append(purchase)
            self.save_database()
            return True
        return False
    
    def get_user_purchases(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all purchases for a user."""
        user = self.get_user(user_id)
        if user:
            return user.get("purchases", [])
        return []
    
    def has_purchased(self, user_id: int, video_id: str) -> bool:
        """Check if user has purchased a specific video."""
        purchases = self.get_user_purchases(user_id)
        return any(p["video_id"] == video_id for p in purchases)
