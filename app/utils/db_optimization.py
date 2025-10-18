"""
Утилиты для оптимизации производительности БД.
"""

from typing import List, Dict, Any
import asyncio
from datetime import datetime, UTC, timedelta

from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.database import get_session
from app.models.user import User
from app.models.conversation import Conversation


class DatabaseOptimizer:
    """Утилиты для мониторинга и оптимизации БД."""

    @staticmethod
    async def analyze_query_performance() -> Dict[str, Any]:
        """Анализ производительности запросов."""
        try:
            async with get_session() as session:
                # Получение статистики по индексам
                index_stats_query = text("""
                    SELECT 
                        schemaname,
                        tablename,
                        indexname,
                        idx_scan,
                        idx_tup_read,
                        idx_tup_fetch
                    FROM pg_stat_user_indexes 
                    WHERE schemaname = 'public'
                    ORDER BY idx_scan DESC
                """)

                result = await session.execute(index_stats_query)
                index_stats = result.fetchall()

                # Получение статистики по таблицам
                table_stats_query = text("""
                    SELECT 
                        schemaname,
                        relname as tablename,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch,
                        n_tup_ins,
                        n_tup_upd,
                        n_tup_del
                    FROM pg_stat_user_tables 
                    WHERE schemaname = 'public'
                """)

                result = await session.execute(table_stats_query)
                table_stats = result.fetchall()

                # Поиск медленных запросов (требует pg_stat_statements)
                slow_queries = []
                try:
                    slow_query = text("""
                        SELECT 
                            query,
                            calls,
                            total_exec_time,
                            mean_exec_time,
                            rows
                        FROM pg_stat_statements 
                        WHERE query LIKE '%conversations%' OR query LIKE '%users%'
                        ORDER BY mean_exec_time DESC
                        LIMIT 10
                    """)

                    result = await session.execute(slow_query)
                    slow_queries = result.fetchall()

                except Exception:
                    logger.warning(
                        "pg_stat_statements not available for slow query analysis"
                    )

                return {
                    "index_usage": [dict(row._mapping) for row in index_stats],
                    "table_stats": [dict(row._mapping) for row in table_stats],
                    "slow_queries": [dict(row._mapping) for row in slow_queries],
                    "analysis_time": datetime.now(UTC).isoformat(),
                }

        except Exception as e:
            logger.error(f"Failed to analyze query performance: {e}")
            return {"error": str(e)}

    @staticmethod
    async def check_missing_indexes() -> List[Dict[str, Any]]:
        """Проверка на отсутствующие индексы."""
        suggestions = []

        try:
            async with get_session() as session:
                # Проверка на таблицы без индексов на внешние ключи
                fk_check_query = text("""
                    SELECT 
                        t.table_name,
                        c.column_name,
                        c.data_type
                    FROM information_schema.table_constraints t
                    JOIN information_schema.constraint_column_usage ccu 
                        ON t.constraint_name = ccu.constraint_name
                    JOIN information_schema.columns c 
                        ON t.table_name = c.table_name 
                        AND ccu.column_name = c.column_name
                    WHERE t.constraint_type = 'FOREIGN KEY'
                        AND t.table_schema = 'public'
                        AND NOT EXISTS (
                            SELECT 1 FROM pg_indexes 
                            WHERE tablename = t.table_name 
                            AND indexdef LIKE '%' || c.column_name || '%'
                        )
                """)

                result = await session.execute(fk_check_query)
                missing_fk_indexes = result.fetchall()

                for row in missing_fk_indexes:
                    suggestions.append(
                        {
                            "type": "missing_foreign_key_index",
                            "table": row.table_name,
                            "column": row.column_name,
                            "suggestion": f"CREATE INDEX idx_{row.table_name}_{row.column_name} ON {row.table_name} ({row.column_name})",
                            "priority": "high",
                        }
                    )

                # Проверка на часто используемые WHERE условия без индексов
                frequent_where_conditions = [
                    ("users", "is_active", "boolean"),
                    ("users", "is_premium", "boolean"),
                    ("users", "last_message_date", "date"),
                    ("conversations", "status", "varchar"),
                    ("conversations", "ai_model", "varchar"),
                ]

                for table, column, data_type in frequent_where_conditions:
                    # Проверяем, есть ли индекс на этом столбце
                    index_check_query = text("""
                        SELECT COUNT(*) as index_count
                        FROM pg_indexes 
                        WHERE tablename = :table 
                        AND (indexdef LIKE '%' || :column || '%')
                    """)

                    result = await session.execute(
                        index_check_query, {"table": table, "column": column}
                    )
                    index_count = result.scalar()

                    if index_count == 0:
                        suggestions.append(
                            {
                                "type": "missing_where_condition_index",
                                "table": table,
                                "column": column,
                                "suggestion": f"CREATE INDEX idx_{table}_{column} ON {table} ({column})",
                                "priority": "medium",
                            }
                        )

                return suggestions

        except Exception as e:
            logger.error(f"Failed to check missing indexes: {e}")
            return [{"error": str(e)}]

    @staticmethod
    async def optimize_table_maintenance() -> Dict[str, Any]:
        """Выполнение обслуживания таблиц."""
        maintenance_results = {}

        try:
            async with get_session() as session:
                # Получение размеров таблиц
                table_sizes_query = text("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = 'public'
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                """)

                result = await session.execute(table_sizes_query)
                table_sizes = result.fetchall()

                maintenance_results["table_sizes"] = [
                    dict(row._mapping) for row in table_sizes
                ]

                # Проверка на необходимость VACUUM
                vacuum_stats_query = text("""
                    SELECT 
                        schemaname,
                        tablename,
                        n_dead_tup,
                        n_live_tup,
                        CASE 
                            WHEN n_live_tup = 0 THEN 0
                            ELSE (n_dead_tup::float / n_live_tup::float) * 100
                        END as dead_tuple_percent,
                        last_vacuum,
                        last_autovacuum,
                        last_analyze,
                        last_autoanalyze
                    FROM pg_stat_user_tables 
                    WHERE schemaname = 'public'
                    ORDER BY n_dead_tup DESC
                """)

                result = await session.execute(vacuum_stats_query)
                vacuum_stats = result.fetchall()

                maintenance_results["vacuum_stats"] = [
                    dict(row._mapping) for row in vacuum_stats
                ]

                # Рекомендации по обслуживанию
                recommendations = []

                for row in vacuum_stats:
                    dead_percent = row.dead_tuple_percent or 0

                    if dead_percent > 20:
                        recommendations.append(
                            {
                                "type": "vacuum_needed",
                                "table": row.tablename,
                                "dead_tuple_percent": dead_percent,
                                "recommendation": f"VACUUM ANALYZE {row.tablename};",
                                "priority": "high" if dead_percent > 50 else "medium",
                            }
                        )

                    # Проверка давности последнего ANALYZE
                    if row.last_analyze and row.last_autoanalyze:
                        last_analyze = max(row.last_analyze, row.last_autoanalyze)
                        days_since_analyze = (
                            datetime.now(UTC) - last_analyze.replace(tzinfo=UTC)
                        ).days

                        if days_since_analyze > 7:
                            recommendations.append(
                                {
                                    "type": "analyze_needed",
                                    "table": row.tablename,
                                    "days_since_analyze": days_since_analyze,
                                    "recommendation": f"ANALYZE {row.tablename};",
                                    "priority": "low",
                                }
                            )

                maintenance_results["recommendations"] = recommendations

                return maintenance_results

        except Exception as e:
            logger.error(f"Failed to analyze table maintenance: {e}")
            return {"error": str(e)}

    @staticmethod
    async def generate_optimization_report() -> Dict[str, Any]:
        """Генерация полного отчета по оптимизации."""
        logger.info("Generating database optimization report...")

        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "performance_analysis": await DatabaseOptimizer.analyze_query_performance(),
            "missing_indexes": await DatabaseOptimizer.check_missing_indexes(),
            "maintenance_analysis": await DatabaseOptimizer.optimize_table_maintenance(),
        }

        # Подсчет общих рекомендаций
        total_recommendations = 0
        high_priority = 0

        for section in ["missing_indexes", "maintenance_analysis"]:
            if section in report and "recommendations" in report[section]:
                recommendations = report[section]["recommendations"]
                total_recommendations += len(recommendations)
                high_priority += sum(
                    1 for r in recommendations if r.get("priority") == "high"
                )

        if "missing_indexes" in report:
            missing_indexes = report["missing_indexes"]
            if not isinstance(missing_indexes, dict) or "error" not in missing_indexes:
                total_recommendations += len(missing_indexes)
                high_priority += sum(
                    1 for idx in missing_indexes if idx.get("priority") == "high"
                )

        report["summary"] = {
            "total_recommendations": total_recommendations,
            "high_priority_count": high_priority,
            "status": "needs_attention" if high_priority > 0 else "good",
        }

        logger.info(
            f"Optimization report generated: {total_recommendations} recommendations, {high_priority} high priority"
        )

        return report
