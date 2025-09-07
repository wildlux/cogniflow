#!/usr/bin/env python3
"""
Cache Manager - Sistema di cache intelligente
Gestisce cache per impostazioni, risultati AI, e altri dati
"""

import os
import time
import threading
import hashlib
import json
from typing import Any, Dict, Optional, Callable
from datetime import datetime, timedelta
from collections import OrderedDict

import logging
logger = logging.getLogger(__name__)


class CacheEntry:
    """Rappresenta una entry della cache."""

    def __init__(self, key: str, value: Any, ttl: int = 300):
        self.key = key
        self.value = value
        self.timestamp = time.time()
        self.ttl = ttl
        self.access_count = 0
        self.last_access = time.time()

    def is_expired(self) -> bool:
        """Verifica se l'entry è scaduta."""
        return time.time() - self.timestamp > self.ttl

    def is_stale(self, max_age: int = 3600) -> bool:
        """Verifica se l'entry è vecchia (non acceduta recentemente)."""
        return time.time() - self.last_access > max_age

    def access(self):
        """Registra un accesso all'entry."""
        self.access_count += 1
        self.last_access = time.time()

    def get_age(self) -> float:
        """Restituisce l'età dell'entry in secondi."""
        return time.time() - self.timestamp

    def _is_json_serializable(self, obj) -> bool:
        """Verifica se un oggetto è serializzabile in JSON."""
        try:
            json.dumps(obj, default=str)
            return True
        except (TypeError, ValueError):
            return False

    def get_metadata(self) -> Dict[str, Any]:
        """Restituisce i metadati dell'entry."""
        return {
            "key": self.key,
            "timestamp": datetime.fromtimestamp(self.timestamp),
            "ttl": self.ttl,
            "access_count": self.access_count,
            "last_access": datetime.fromtimestamp(self.last_access),
            "age_seconds": self.get_age(),
            "size_bytes": len(json.dumps(self.value, default=str).encode()) if self.value and self._is_json_serializable(self.value) else 0
        }


class LRUCache:
    """Cache con algoritmo LRU (Least Recently Used)."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Ottiene un valore dalla cache."""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if not entry.is_expired():
                    entry.access()
                    self.cache.move_to_end(key)  # Sposta alla fine (più recente)
                    self.hits += 1
                    return entry.value
                else:
                    # Entry scaduta, rimuovila
                    del self.cache[key]

            self.misses += 1
            return None

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Inserisce un valore nella cache."""
        with self.lock:
            if ttl is None:
                ttl = self.default_ttl

            entry = CacheEntry(key, value, ttl)

            if key in self.cache:
                # Aggiorna entry esistente
                self.cache[key] = entry
                self.cache.move_to_end(key)
            else:
                # Aggiungi nuova entry
                if len(self.cache) >= self.max_size:
                    # Rimuovi l'entry meno recentemente usata
                    removed_key, _ = self.cache.popitem(last=False)
                    logger.debug("Cache LRU removed: {removed_key}")

                self.cache[key] = entry
                self.cache.move_to_end(key)

    def remove(self, key: str) -> bool:
        """Rimuove un valore dalla cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self) -> None:
        """Svuota completamente la cache."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def cleanup_expired(self) -> int:
        """Rimuove tutte le entry scadute."""
        with self.lock:
            expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
            for key in expired_keys:
                del self.cache[key]
            return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche della cache."""
        with self.lock:
            total_entries = len(self.cache)
            total_accesses = self.hits + self.misses
            hit_rate = self.hits / total_accesses if total_accesses > 0 else 0

            return {
                "total_entries": total_entries,
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate,
                "utilization_percent": (total_entries / self.max_size) * 100
            }

    def get_all_entries(self) -> Dict[str, Dict[str, Any]]:
        """Restituisce tutte le entry con i loro metadati."""
        with self.lock:
            return {k: v.get_metadata() for k, v in self.cache.items()}


class PersistentCache:
    """Cache persistente su disco."""

    def __init__(self, cache_dir: str = "cache", max_size: int = 1000):
        self.cache_dir = cache_dir
        self.max_size = max_size
        self.memory_cache = LRUCache(max_size)

        # Crea directory cache se non esiste
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)

    def get(self, key: str) -> Optional[Any]:
        """Ottiene un valore dalla cache (prima memoria, poi disco)."""
        # Prima prova dalla cache in memoria
        value = self.memory_cache.get(key)
        if value is not None:
            return value

        # Se non in memoria, prova dal disco
        cache_file = self._get_cache_file_path(key)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                    entry = CacheEntry(data['key'], data['value'], data['ttl'])
                    entry.timestamp = data['timestamp']
                    entry.access_count = data['access_count']
                    entry.last_access = data['last_access']

                if not entry.is_expired():
                    # Rimetti in memoria
                    self.memory_cache.put(key, entry.value, entry.ttl)
                    return entry.value
                else:
                    # File scaduto, rimuovilo
                    os.remove(cache_file)
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning("Error loading cache file {cache_file} (possibly old pickle format): {e}")
                # Rimuovi file corrotto o vecchio formato
                try:
                    os.remove(cache_file)
                except OSError:
                    pass
            except Exception:
                logger.warning("Error loading cache file {cache_file}: {e}")
                # Rimuovi file corrotto
                try:
                    os.remove(cache_file)
                except OSError:
                    pass

        return None

    def put(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Salva un valore nella cache (memoria e disco)."""
        # Salva in memoria
        self.memory_cache.put(key, value, ttl)

        # Salva su disco
        cache_file = self._get_cache_file_path(key)
        try:
            entry = CacheEntry(key, value, ttl or 300)
            data = {
                'key': entry.key,
                'value': entry.value,
                'timestamp': entry.timestamp,
                'ttl': entry.ttl,
                'access_count': entry.access_count,
                'last_access': entry.last_access
            }
            with open(cache_file, 'w') as f:
                json.dump(data, f, default=str)
        except (TypeError, ValueError) as e:
            logger.warning("Cannot serialize value for cache file {cache_file}: {e}")
        except Exception:
            logger.warning("Error saving cache file {cache_file}: {e}")

    def remove(self, key: str) -> bool:
        """Rimuove un valore dalla cache."""
        # Rimuovi da memoria
        memory_removed = self.memory_cache.remove(key)

        # Rimuovi da disco
        cache_file = self._get_cache_file_path(key)
        disk_removed = False
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                disk_removed = True
            except Exception:
                logger.warning("Error removing cache file {cache_file}: {e}")

        return memory_removed or disk_removed

    def clear(self) -> None:
        """Svuota completamente la cache."""
        # Svuota memoria
        self.memory_cache.clear()

        # Svuota disco
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    os.remove(os.path.join(self.cache_dir, filename))
        except Exception:
            logger.warning("Error clearing disk cache: {e}")

    def cleanup_expired(self) -> int:
        """Pulisce file di cache scaduti dal disco."""
        cleaned = 0
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    filepath = os.path.join(self.cache_dir, filename)
                    try:
                        with open(filepath, 'r') as f:
                            data = json.load(f)
                            entry = CacheEntry(data['key'], data['value'], data['ttl'])
                            entry.timestamp = data['timestamp']
                            entry.access_count = data['access_count']
                            entry.last_access = data['last_access']

                        if entry.is_expired():
                            os.remove(filepath)
                            cleaned += 1
                    except Exception:
                        # File corrotto, rimuovilo
                        try:
                            os.remove(filepath)
                            cleaned += 1
                        except OSError:
                            pass
        except Exception:
            logger.warning("Error during cache cleanup: {e}")

        # Anche cleanup della memoria
        cleaned += self.memory_cache.cleanup_expired()

        return cleaned

    def _get_cache_file_path(self, key: str) -> str:
        """Genera il path del file di cache per una chiave."""
        # Usa hash della chiave per il nome del file
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, "{key_hash}.cache")

    def get_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche complete della cache."""
        memory_stats = self.memory_cache.get_stats()

        # Conta file su disco
        disk_files = 0
        disk_size = 0
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    disk_files += 1
                    filepath = os.path.join(self.cache_dir, filename)
                    disk_size += os.path.getsize(filepath)
        except OSError:
            pass

        return {
            **memory_stats,
            "disk_files": disk_files,
            "disk_size_bytes": disk_size,
            "disk_size_mb": disk_size / (1024 * 1024)
        }


class CacheManager:
    """Gestore centralizzato delle cache."""

    def __init__(self):
        self.caches: Dict[str, LRUCache] = {}
        self.persistent_cache = PersistentCache()
        self.lock = threading.Lock()

        # Cache dedicate per tipo di dato
        self._setup_caches()

    def _setup_caches(self):
        """Imposta le cache dedicate."""
        # Cache per impostazioni (TTL lungo)
        self.caches["settings"] = LRUCache(max_size=500, default_ttl=3600)  # 1 ora

        # Cache per risultati AI (TTL medio)
        self.caches["ai_results"] = LRUCache(max_size=200, default_ttl=1800)  # 30 minuti

        # Cache per modelli caricati (TTL lungo)
        self.caches["models"] = LRUCache(max_size=50, default_ttl=7200)  # 2 ore

        # Cache per risultati TTS (TTL breve)
        self.caches["tts_results"] = LRUCache(max_size=100, default_ttl=600)  # 10 minuti

    def get_cache(self, cache_name: str) -> LRUCache:
        """Ottiene una cache specifica."""
        with self.lock:
            if cache_name not in self.caches:
                # Crea cache generica se non esiste
                self.caches[cache_name] = LRUCache()
            return self.caches[cache_name]

    def get_settings_cache(self) -> LRUCache:
        """Cache dedicata per le impostazioni."""
        return self.get_cache("settings")

    def get_ai_cache(self) -> LRUCache:
        """Cache dedicata per i risultati AI."""
        return self.get_cache("ai_results")

    def get_model_cache(self) -> LRUCache:
        """Cache dedicata per i modelli."""
        return self.get_cache("models")

    def get_tts_cache(self) -> LRUCache:
        """Cache dedicata per i risultati TTS."""
        return self.get_cache("tts_results")

    def get_persistent_cache(self) -> PersistentCache:
        """Cache persistente su disco."""
        return self.persistent_cache

    def clear_all_caches(self) -> None:
        """Svuota tutte le cache."""
        with self.lock:
            for cache in self.caches.values():
                cache.clear()
            self.persistent_cache.clear()

    def cleanup_all_caches(self) -> Dict[str, int]:
        """Pulisce tutte le cache scadute."""
        result = {}

        with self.lock:
            for name, cache in self.caches.items():
                result["{name}_expired"] = cache.cleanup_expired()

        result["persistent_expired"] = self.persistent_cache.cleanup_expired()

        return result

    def get_all_stats(self) -> Dict[str, Any]:
        """Restituisce statistiche di tutte le cache."""
        stats = {}

        with self.lock:
            for name, cache in self.caches.items():
                stats[name] = cache.get_stats()

        stats["persistent"] = self.persistent_cache.get_stats()

        return stats

    def start_cleanup_thread(self, interval: int = 3600):
        """Avvia un thread per la pulizia periodica delle cache."""
        def cleanup_worker():
            while True:
                time.sleep(interval)
                try:
                    cleaned = self.cleanup_all_caches()
                    total_cleaned = sum(cleaned.values())
                    if total_cleaned > 0:
                        logger.info("Cache cleanup: removed {total_cleaned} expired entries")
                except Exception:
                    logger.error("Error during cache cleanup: {e}")

        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        logger.info("Cache cleanup thread started with {interval}s interval")


# Istanza globale del cache manager
cache_manager = CacheManager()


def get_cache_manager() -> CacheManager:
    """Restituisce l'istanza globale del cache manager."""
    return cache_manager


def cached(ttl: int = 300, cache_name: str = "default"):
    """
    Decoratore per caching automatico delle funzioni.

    Args:
        ttl: Time To Live in secondi
        cache_name: Nome della cache da usare
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Crea chiave cache basata su funzione e argomenti
            key_data = {
                "func": func.__name__,
                "args": args,
                "kwargs": kwargs
            }
            key = hashlib.md5(str(key_data).encode()).hexdigest()

            # Prova a ottenere dalla cache
            cache = cache_manager.get_cache(cache_name)
            result = cache.get(key)
            if result is not None:
                return result

            # Esegui funzione e salva in cache
            result = func(*args, **kwargs)
            cache.put(key, result, ttl)
            return result

        return wrapper
    return decorator
