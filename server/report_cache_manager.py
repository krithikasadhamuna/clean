"""
Report Cache Manager
Manages caching of generated reports to reduce costs and improve performance
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class ReportCacheManager:
    """Manages report caching in database"""
    
    def __init__(self, db_path: str = "soc_database.db"):
        self.db_path = db_path
        self._initialize_cache_table()
    
    def _initialize_cache_table(self):
        """Create report_cache table if it doesn't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS report_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_type TEXT NOT NULL,
                    report_data TEXT NOT NULL,
                    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,
                    UNIQUE(report_type)
                )
            ''')
            
            # Create index for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_report_cache_type 
                ON report_cache(report_type)
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Report cache table initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize report cache table: {e}")
    
    def get_cached_report(self, report_type: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached report from database
        
        Args:
            report_type: Type of report ('risk_assessment', 'security_posture', 'compliance_dashboard')
        
        Returns:
            Cached report dict or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT report_data, generated_at, metadata
                FROM report_cache
                WHERE report_type = ?
                ORDER BY generated_at DESC
                LIMIT 1
            ''', (report_type,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                report_data = json.loads(row['report_data'])
                generated_at = row['generated_at']
                metadata = json.loads(row['metadata']) if row['metadata'] else {}
                
                logger.info(f"Retrieved cached {report_type} report from {generated_at}")
                
                return {
                    'report': report_data,
                    'generated_at': generated_at,
                    'metadata': metadata,
                    'cached': True
                }
            
            logger.info(f"No cached {report_type} report found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve cached report: {e}")
            return None
    
    def save_report(self, report_type: str, report_data: Dict[str, Any], 
                   metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save report to cache
        
        Args:
            report_type: Type of report ('risk_assessment', 'security_posture', 'compliance_dashboard')
            report_data: Report data to cache
            metadata: Optional metadata about the report
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            report_json = json.dumps(report_data)
            metadata_json = json.dumps(metadata) if metadata else None
            
            # Use REPLACE to update existing cache or insert new
            cursor.execute('''
                INSERT OR REPLACE INTO report_cache (report_type, report_data, generated_at, metadata)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?)
            ''', (report_type, report_json, metadata_json))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Successfully cached {report_type} report")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save report to cache: {e}")
            return False
    
    def clear_cache(self, report_type: Optional[str] = None) -> bool:
        """
        Clear cached reports
        
        Args:
            report_type: Specific report type to clear, or None to clear all
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if report_type:
                cursor.execute('DELETE FROM report_cache WHERE report_type = ?', (report_type,))
                logger.info(f"Cleared cache for {report_type}")
            else:
                cursor.execute('DELETE FROM report_cache')
                logger.info("Cleared all cached reports")
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached reports"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT report_type, generated_at
                FROM report_cache
                ORDER BY generated_at DESC
            ''')
            
            cached_reports = []
            for row in cursor.fetchall():
                cached_reports.append({
                    'type': row['report_type'],
                    'generated_at': row['generated_at']
                })
            
            conn.close()
            
            return {
                'total_cached_reports': len(cached_reports),
                'reports': cached_reports
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return {'total_cached_reports': 0, 'reports': []}


# Global instance
_report_cache_manager = None

def get_report_cache_manager(db_path: str = "soc_database.db") -> ReportCacheManager:
    """Get singleton instance of ReportCacheManager"""
    global _report_cache_manager
    if _report_cache_manager is None:
        _report_cache_manager = ReportCacheManager(db_path)
    return _report_cache_manager


