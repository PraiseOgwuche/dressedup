from abc import ABC, abstractmethod


class StorageProvider(ABC):
    """Persists binary assets and returns a URL by which they can be fetched.

    Behind this contract so local disk now can become object storage (S3 /
    Supabase) at deploy without changing callers.
    """

    @abstractmethod
    def save(self, data: bytes, *, ext: str, subdir: str = "") -> str:
        """Store bytes and return a fetchable URL (absolute or app-relative)."""
        raise NotImplementedError
