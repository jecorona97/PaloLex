import sqlite3
import json
from typing import Dict, Optional, List, Any
from datetime import datetime
from models import UserProfile, ChatSession, FormInfo
import logging

logger = logging.getLogger(__name__)

class UserStorage:
    def __init__(self, db_path: str = "user_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                personal_info TEXT,
                preferences TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                form_url TEXT,
                form_info TEXT,
                missing_fields TEXT,
                collected_data TEXT,
                status TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        # Create form_fields table for learning
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS form_fields (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                field_label TEXT,
                field_type TEXT,
                field_value TEXT,
                confidence REAL,
                usage_count INTEGER DEFAULT 1,
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by user_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, personal_info, preferences, created_at, updated_at
            FROM users WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return UserProfile(
                user_id=row[0],
                personal_info=json.loads(row[1]) if row[1] else {},
                preferences=json.loads(row[2]) if row[2] else {},
                created_at=datetime.fromisoformat(row[3]),
                updated_at=datetime.fromisoformat(row[4])
            )
        return None
    
    def save_user_profile(self, profile: UserProfile) -> bool:
        """Save or update user profile"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            profile.updated_at = datetime.now()
            
            cursor.execute("""
                INSERT OR REPLACE INTO users 
                (user_id, personal_info, preferences, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                profile.user_id,
                json.dumps(profile.personal_info),
                json.dumps(profile.preferences),
                profile.created_at.isoformat(),
                profile.updated_at.isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving user profile: {e}")
            return False
    
    def update_user_info(self, user_id: str, field_name: str, value: str) -> bool:
        """Update specific user information"""
        profile = self.get_user_profile(user_id)
        if not profile:
            profile = UserProfile(user_id=user_id)
        
        profile.personal_info[field_name] = value
        return self.save_user_profile(profile)
    
    def get_user_field_value(self, user_id: str, field_label: str, field_type: str) -> Optional[str]:
        """Get user's preferred value for a specific field"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # First check exact label match
        cursor.execute("""
            SELECT field_value, confidence 
            FROM form_fields 
            WHERE user_id = ? AND field_label = ?
            ORDER BY confidence DESC, usage_count DESC
            LIMIT 1
        """, (user_id, field_label))
        
        row = cursor.fetchone()
        if row:
            conn.close()
            return row[0]
        
        # Then check by field type and similar labels
        cursor.execute("""
            SELECT field_value, confidence 
            FROM form_fields 
            WHERE user_id = ? AND field_type = ?
            AND (field_label LIKE ? OR field_label LIKE ?)
            ORDER BY confidence DESC, usage_count DESC
            LIMIT 1
        """, (user_id, field_type, f"%{field_label}%", f"%{field_label.lower()}%"))
        
        row = cursor.fetchone()
        conn.close()
        
        return row[0] if row else None
    
    def save_field_value(self, user_id: str, field_label: str, field_type: str, 
                        field_value: str, confidence: float = 0.8) -> bool:
        """Save or update a field value for the user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if field already exists
            cursor.execute("""
                SELECT id, usage_count FROM form_fields 
                WHERE user_id = ? AND field_label = ? AND field_type = ?
            """, (user_id, field_label, field_type))
            
            row = cursor.fetchone()
            now = datetime.now().isoformat()
            
            if row:
                # Update existing field
                cursor.execute("""
                    UPDATE form_fields 
                    SET field_value = ?, confidence = ?, usage_count = usage_count + 1, updated_at = ?
                    WHERE id = ?
                """, (field_value, confidence, now, row[0]))
            else:
                # Insert new field
                cursor.execute("""
                    INSERT INTO form_fields 
                    (user_id, field_label, field_type, field_value, confidence, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, field_label, field_type, field_value, confidence, now, now))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving field value: {e}")
            return False
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get chat session by session_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT session_id, user_id, form_url, form_info, missing_fields, 
                   collected_data, status, created_at, updated_at
            FROM sessions WHERE session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            form_info = None
            if row[3]:
                form_info_dict = json.loads(row[3])
                form_info = FormInfo(**form_info_dict)
            
            return ChatSession(
                session_id=row[0],
                user_id=row[1],
                form_url=row[2],
                form_info=form_info,
                missing_fields=json.loads(row[4]) if row[4] else [],
                collected_data=json.loads(row[5]) if row[5] else {},
                status=row[6],
                created_at=datetime.fromisoformat(row[7]),
                updated_at=datetime.fromisoformat(row[8])
            )
        return None
    
    def save_session(self, session: ChatSession) -> bool:
        """Save or update chat session"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            session.updated_at = datetime.now()
            
            form_info_json = None
            if session.form_info:
                form_info_json = json.dumps(session.form_info.dict())
            
            cursor.execute("""
                INSERT OR REPLACE INTO sessions 
                (session_id, user_id, form_url, form_info, missing_fields, 
                 collected_data, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session.session_id,
                session.user_id,
                session.form_url,
                form_info_json,
                json.dumps(session.missing_fields),
                json.dumps(session.collected_data),
                session.status,
                session.created_at.isoformat(),
                session.updated_at.isoformat()
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            return False
    
    def get_similar_fields(self, user_id: str, field_label: str, limit: int = 5) -> List[Dict]:
        """Get similar fields for suggestions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT field_label, field_type, field_value, confidence, usage_count
            FROM form_fields 
            WHERE user_id = ? AND field_label LIKE ?
            ORDER BY confidence DESC, usage_count DESC
            LIMIT ?
        """, (user_id, f"%{field_label}%", limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'label': row[0],
                'type': row[1],
                'value': row[2],
                'confidence': row[3],
                'usage_count': row[4]
            }
            for row in rows
        ]
    
    def get_user_stats(self, user_id: str) -> Dict:
        """Get user statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get total forms filled
        cursor.execute("""
            SELECT COUNT(*) FROM sessions 
            WHERE user_id = ? AND status = 'completed'
        """, (user_id,))
        forms_filled = cursor.fetchone()[0]
        
        # Get total fields learned
        cursor.execute("""
            SELECT COUNT(*) FROM form_fields 
            WHERE user_id = ?
        """, (user_id,))
        fields_learned = cursor.fetchone()[0]
        
        # Get most recent activity
        cursor.execute("""
            SELECT MAX(updated_at) FROM sessions 
            WHERE user_id = ?
        """, (user_id,))
        last_activity = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'forms_filled': forms_filled,
            'fields_learned': fields_learned,
            'last_activity': last_activity
        }