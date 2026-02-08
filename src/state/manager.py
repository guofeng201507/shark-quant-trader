"""State Manager - Persistence and disaster recovery - Tech Design v1.1 Section 11"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from ..models.domain import Portfolio, Order
from ..utils.logger import logger


class StateManager:
    """State persistence and disaster recovery"""
    
    def __init__(self, db_path: str = "data/state.db"):
        """Initialize state manager with SQLite database"""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
        logger.info(f"StateManager initialized with database: {db_path}")
    
    def _ensure_db_directory(self):
        """Create data directory if it doesn't exist"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Portfolio state table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                positions TEXT NOT NULL,
                cash REAL NOT NULL,
                nav REAL NOT NULL,
                peak_nav REAL NOT NULL,
                weights TEXT NOT NULL,
                unrealized_pnl REAL NOT NULL,
                cost_basis TEXT NOT NULL,
                target_volatility REAL NOT NULL
            )
        """)
        
        # Order history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                order_type TEXT NOT NULL,
                limit_price REAL,
                status TEXT NOT NULL
            )
        """)
        
        # Risk events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                level INTEGER NOT NULL,
                portfolio_drawdown REAL NOT NULL,
                violations TEXT NOT NULL,
                actions_taken TEXT NOT NULL
            )
        """)
        
        # System state table (for recovery)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                state_type TEXT NOT NULL,
                data TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Database schema initialized")
    
    def save_portfolio_state(self, portfolio: Portfolio) -> bool:
        """
        Save current portfolio state to database.
        
        Args:
            portfolio: Portfolio object to save
            
        Returns:
            True if save successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO portfolio_state 
                (timestamp, positions, cash, nav, peak_nav, weights, 
                 unrealized_pnl, cost_basis, target_volatility)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                json.dumps(portfolio.positions),
                portfolio.cash,
                portfolio.nav,
                portfolio.peak_nav,
                json.dumps(portfolio.weights),
                portfolio.unrealized_pnl,
                json.dumps(portfolio.cost_basis),
                portfolio.target_volatility
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Portfolio state saved: NAV={portfolio.nav:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save portfolio state: {e}")
            return False
    
    def load_latest_portfolio_state(self) -> Optional[Portfolio]:
        """
        Load most recent portfolio state from database.
        
        Returns:
            Portfolio object or None if no state found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT positions, cash, nav, peak_nav, weights, 
                       unrealized_pnl, cost_basis, target_volatility
                FROM portfolio_state
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            conn.close()
            
            if row is None:
                logger.info("No portfolio state found in database")
                return None
            
            portfolio = Portfolio(
                positions=json.loads(row[0]),
                cash=row[1],
                nav=row[2],
                peak_nav=row[3],
                weights=json.loads(row[4]),
                unrealized_pnl=row[5],
                cost_basis=json.loads(row[6]),
                target_volatility=row[7]
            )
            
            logger.info(f"Portfolio state loaded: NAV={portfolio.nav:.2f}")
            return portfolio
            
        except Exception as e:
            logger.error(f"Failed to load portfolio state: {e}")
            return None
    
    def save_order(self, order: Order) -> bool:
        """
        Save order to history.
        
        Args:
            order: Order object to save
            
        Returns:
            True if save successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO order_history 
                (timestamp, symbol, side, quantity, order_type, limit_price, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                order.timestamp.isoformat(),
                order.symbol,
                order.side,
                order.quantity,
                order.order_type,
                order.limit_price,
                order.status
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"Order saved: {order.side} {order.quantity} {order.symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save order: {e}")
            return False
    
    def load_order_history(self, days: int = 30) -> List[Dict]:
        """
        Load order history from database.
        
        Args:
            days: Number of days of history to load
            
        Returns:
            List of order dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT timestamp, symbol, side, quantity, order_type, limit_price, status
                FROM order_history
                WHERE timestamp >= datetime('now', '-' || ? || ' days')
                ORDER BY timestamp DESC
            """, (days,))
            
            orders = []
            for row in cursor.fetchall():
                orders.append({
                    "timestamp": row[0],
                    "symbol": row[1],
                    "side": row[2],
                    "quantity": row[3],
                    "order_type": row[4],
                    "limit_price": row[5],
                    "status": row[6]
                })
            
            conn.close()
            logger.info(f"Loaded {len(orders)} orders from last {days} days")
            return orders
            
        except Exception as e:
            logger.error(f"Failed to load order history: {e}")
            return []
    
    def save_risk_event(self, event_type: str, level: int, 
                       portfolio_drawdown: float, violations: List[str],
                       actions_taken: List[str]) -> bool:
        """
        Save risk event to database.
        
        Args:
            event_type: Type of risk event
            level: Risk level (0-4)
            portfolio_drawdown: Current drawdown
            violations: List of violations
            actions_taken: Actions taken in response
            
        Returns:
            True if save successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO risk_events 
                (timestamp, event_type, level, portfolio_drawdown, violations, actions_taken)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().isoformat(),
                event_type,
                level,
                portfolio_drawdown,
                json.dumps(violations),
                json.dumps(actions_taken)
            ))
            
            conn.commit()
            conn.close()
            
            logger.warning(f"Risk event saved: Level {level} - {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save risk event: {e}")
            return False
    
    def save_system_state(self, state_type: str, data: Dict) -> bool:
        """
        Save arbitrary system state for disaster recovery.
        
        Args:
            state_type: Type of state (e.g., 'config', 'runtime')
            data: State data as dictionary
            
        Returns:
            True if save successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO system_state (timestamp, state_type, data)
                VALUES (?, ?, ?)
            """, (
                datetime.now().isoformat(),
                state_type,
                json.dumps(data)
            ))
            
            conn.commit()
            conn.close()
            
            logger.debug(f"System state saved: {state_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save system state: {e}")
            return False
    
    def load_system_state(self, state_type: str) -> Optional[Dict]:
        """
        Load latest system state of given type.
        
        Args:
            state_type: Type of state to load
            
        Returns:
            State data dictionary or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT data FROM system_state
                WHERE state_type = ?
                ORDER BY timestamp DESC
                LIMIT 1
            """, (state_type,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row is None:
                return None
            
            return json.loads(row[0])
            
        except Exception as e:
            logger.error(f"Failed to load system state: {e}")
            return None
    
    def create_backup(self, backup_path: str = None) -> bool:
        """
        Create backup of entire database.
        
        Args:
            backup_path: Path for backup file (optional)
            
        Returns:
            True if backup successful
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"data/backups/state_{timestamp}.db"
        
        try:
            # Ensure backup directory exists
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Copy database
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            logger.info(f"Database backup created: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False