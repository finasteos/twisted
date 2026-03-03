"""
Centralized MLX Utility
Handles MLX availability checks and memory management (Metal cache clearing)
to resolve lint errors and maintain a clean engine footprint.
"""

import gc
import logging

logger = logging.getLogger(__name__)

def is_mlx_available() -> bool:
    """Check if MLX and relevant libraries are available, respecting thermal relief."""
    from backend.config.settings import settings
    if settings.DISABLE_LOCAL_MLX:
        return False

    try:
        import mlx.core as mx
        return True
    except ImportError:
        return False

def set_mlx_memory_limit(limit_mb: int):
    """Set MLX Metal memory limit in MB."""
    try:
        import mlx.core as mx
        limit_bytes = limit_mb * 1024 * 1024
        mx.metal.set_memory_limit(limit_bytes)
        mx.metal.set_cache_limit(limit_bytes)
        logger.info(f"MLX memory limit set to {limit_mb} MB.")
    except ImportError:
        pass
    except AttributeError:
        # Older versions of MLX might not have these methods
        pass
    except Exception as e:
        logger.warning(f"Failed to set MLX limit: {e}")

def clear_mlx_cache():
    """Clear MLX Metal cache and trigger garbage collection."""
    # Always trigger GC
    gc.collect()

    try:
        import mlx.core as mx
        mx.metal.clear_cache()
        logger.info("MLX Metal cache cleared successfully.")
    except ImportError:
        # MLX not installed, nothing to clear
        pass
    except Exception as e:
        logger.warning(f"Failed to clear MLX cache: {e}")

def cleanup_model(model=None):
    """Explicitly delete model and clear cache."""
    if model is not None:
        del model
    clear_mlx_cache()
