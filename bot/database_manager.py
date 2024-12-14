import sqlite3
import json
from datetime import datetime
from common.log import logger
from config import conf


class DatabaseManager:
    def __init__(self, db_path="chat_history.db"):
        self.db_path = db_path
        logger.info(f"[DB] Initializing DatabaseManager with db_path: {db_path}")
        self.init_database()

    def init_database(self):
        """Initialize database tables if they don't exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                logger.info("[DB] Creating database tables if not exist")
                
                # Create sessions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        system_prompt TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create messages table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT,
                        role TEXT,
                        content TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (session_id) REFERENCES sessions (session_id)
                    )
                ''')

                # Create indexes
                logger.info("[DB] Creating indexes if not exist")
                
                # Index for messages table on session_id for faster lookups
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_messages_session_id 
                    ON messages(session_id)
                ''')
                
                # Index for messages table on role for system message filtering
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_messages_role 
                    ON messages(role)
                ''')
                
                # Compound index for messages table on session_id and role
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_messages_session_role 
                    ON messages(session_id, role)
                ''')
                
                # Index for sessions table on updated_at for potential cleanup
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_sessions_updated_at 
                    ON sessions(updated_at)
                ''')

                conn.commit()
                logger.info("[DB] Database tables and indexes created successfully")
        except Exception as e:
            logger.error(f"[DB] Error initializing database: {str(e)}")
            raise

    def save_session(self, session):
        """Save or update a session and its messages"""
        current_time = datetime.now().isoformat()
        logger.info(f"[DB] Saving session {session.session_id} with {len(session.messages)} messages")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Save or update session
                cursor.execute('''
                    INSERT OR REPLACE INTO sessions (session_id, system_prompt, updated_at)
                    VALUES (?, ?, ?)
                ''', (session.session_id, session.system_prompt, current_time))
                
                # Get existing messages for this session
                cursor.execute('''
                    SELECT role, content FROM messages 
                    WHERE session_id = ? AND role = 'system'
                    ORDER BY created_at ASC
                ''', (session.session_id,))
                existing_system_msgs = {content for _, content in cursor.fetchall()}

                # Delete non-system messages
                cursor.execute('DELETE FROM messages WHERE session_id = ? AND role != ?', 
                             (session.session_id, 'system'))
                
                # Save all messages, avoiding duplicate system messages
                for msg in session.messages:
                    if msg['role'] == 'system':
                        if msg['content'] not in existing_system_msgs:
                            cursor.execute('''
                                INSERT INTO messages (session_id, role, content)
                                VALUES (?, ?, ?)
                            ''', (session.session_id, msg['role'], msg['content']))
                            existing_system_msgs.add(msg['content'])
                    else:
                        cursor.execute('''
                            INSERT INTO messages (session_id, role, content)
                            VALUES (?, ?, ?)
                        ''', (session.session_id, msg['role'], msg['content']))
                
                conn.commit()
                logger.info(f"[DB] Successfully saved session {session.session_id}")
        except Exception as e:
            logger.error(f"[DB] Error saving session {session.session_id}: {str(e)}")
            raise

    def load_session(self, session_id, session_cls):
        """Load a session and its messages from database"""
        logger.info(f"[DB] Loading session {session_id}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get session data
                cursor.execute('SELECT system_prompt FROM sessions WHERE session_id = ?', (session_id,))
                session_row = cursor.fetchone()
                
                if not session_row:
                    logger.info(f"[DB] Session {session_id} not found in database")
                    return None
                
                # Create new session instance
                session = session_cls(session_id, system_prompt=session_row[0])
                
                # Get all messages for this session
                cursor.execute('''
                    SELECT role, content FROM messages 
                    WHERE session_id = ? 
                    ORDER BY created_at ASC
                ''', (session_id,))
                
                messages = cursor.fetchall()
                for role, content in messages:
                    msg = {"role": role, "content": content}
                    session.messages.append(msg)
                
                logger.info(f"[DB] Successfully loaded session {session_id} with {len(messages)} messages")
                return session
        except Exception as e:
            logger.error(f"[DB] Error loading session {session_id}: {str(e)}")
            raise

    def load_all_sessions(self, session_cls):
        """Load all sessions from database"""
        logger.info("[DB] Loading all sessions from database")
        sessions = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT session_id FROM sessions')
                session_rows = cursor.fetchall()
                
                logger.info(f"[DB] Found {len(session_rows)} sessions in database")
                for (session_id,) in session_rows:
                    session = self.load_session(session_id, session_cls)
                    if session:
                        sessions[session_id] = session
                
                logger.info(f"[DB] Successfully loaded {len(sessions)} sessions")
                return sessions
        except Exception as e:
            logger.error(f"[DB] Error loading all sessions: {str(e)}")
            raise

    def delete_session(self, session_id):
        """Delete a session and its messages from database"""
        logger.info(f"[DB] Deleting session {session_id}")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM messages WHERE session_id = ?', (session_id,))
                cursor.execute('DELETE FROM sessions WHERE session_id = ?', (session_id,))
                conn.commit()
                logger.info(f"[DB] Successfully deleted session {session_id}")
        except Exception as e:
            logger.error(f"[DB] Error deleting session {session_id}: {str(e)}")
            raise

    def clear_all_sessions(self):
        """Delete all sessions and messages from database"""
        logger.info("[DB] Clearing all sessions from database")
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM messages')
                cursor.execute('DELETE FROM sessions')
                conn.commit()
                logger.info("[DB] Successfully cleared all sessions")
        except Exception as e:
            logger.error(f"[DB] Error clearing all sessions: {str(e)}")
            raise
