"""Integration tests for BaseRedisRepository.

Tests cover all list operations and key management with real Redis
via testcontainers. Each test runs against a clean database —
flushdb is called after every test.
"""

from src.infrastructure.db.redis.repository import BaseRedisRepository


class TestBaseRedisRepositoryLpush:
    """Tests for BaseRedisRepository._lpush()."""

    async def test_lpush_returns_list_length(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that _lpush() returns the list length after insertion."""
        # Arrange
        redis_key = "test:lpush:length"

        # Act
        length = await redis_repository._lpush(redis_key, "first")

        # Assert
        assert length == 1

    async def test_lpush_increments_length_on_multiple_inserts(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that successive _lpush() calls increment the list length."""
        # Arrange
        redis_key = "test:lpush:multi"

        # Act
        first_length = await redis_repository._lpush(redis_key, "a")
        second_length = await redis_repository._lpush(redis_key, "b")
        third_length = await redis_repository._lpush(redis_key, "c")

        # Assert
        assert first_length == 1
        assert second_length == 2
        assert third_length == 3

    async def test_lpush_creates_key_if_absent(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that _lpush() creates the key when it does not exist."""
        # Arrange
        redis_key = "test:lpush:create"

        # Act
        await redis_repository._lpush(redis_key, "value")

        # Assert
        assert await redis_repository.exists(redis_key) is True


class TestBaseRedisRepositoryBrpop:
    """Tests for BaseRedisRepository._brpop()."""

    async def test_brpop_returns_element_from_tail(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that _brpop() returns the tail element (FIFO with LPUSH)."""
        # Arrange
        redis_key = "test:brpop:tail"
        await redis_repository._lpush(redis_key, "first")
        await redis_repository._lpush(redis_key, "second")

        # Act
        popped = await redis_repository._brpop(redis_key, timeout=1)

        # Assert
        assert popped is not None
        assert popped == (redis_key, "first")

    async def test_brpop_removes_element_from_list(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that _brpop() removes the popped element."""
        # Arrange
        redis_key = "test:brpop:remove"
        await redis_repository._lpush(redis_key, "only_element")

        # Act
        await redis_repository._brpop(redis_key, timeout=1)

        # Assert
        assert await redis_repository._llen(redis_key) == 0

    async def test_brpop_returns_none_on_timeout(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that _brpop() returns None when the list is empty and timeout expires."""
        # Act
        popped = await redis_repository._brpop("test:brpop:empty", timeout=1)

        # Assert
        assert popped is None

    async def test_brpop_fifo_order_with_lpush(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify FIFO order: LPUSH + BRPOP pops the earliest pushed element."""
        # Arrange
        redis_key = "test:brpop:fifo"
        await redis_repository._lpush(redis_key, "first")
        await redis_repository._lpush(redis_key, "second")
        await redis_repository._lpush(redis_key, "third")

        # Act & Assert — pop order should be first, second, third
        first = await redis_repository._brpop(redis_key, timeout=1)
        second = await redis_repository._brpop(redis_key, timeout=1)
        third = await redis_repository._brpop(redis_key, timeout=1)

        assert first == (redis_key, "first")
        assert second == (redis_key, "second")
        assert third == (redis_key, "third")

    async def test_brpop_deletes_key_after_last_element(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that the key is removed after the last element is popped."""
        # Arrange
        redis_key = "test:brpop:autoremove"
        await redis_repository._lpush(redis_key, "sole")

        # Act
        await redis_repository._brpop(redis_key, timeout=1)

        # Assert
        assert await redis_repository.exists(redis_key) is False


class TestBaseRedisRepositoryLlen:
    """Tests for BaseRedisRepository._llen()."""

    async def test_llen_returns_zero_for_missing_key(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that _llen() returns 0 when the key does not exist."""
        # Act & Assert
        assert await redis_repository._llen("test:llen:missing") == 0

    async def test_llen_returns_correct_count(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that _llen() returns the actual number of elements."""
        # Arrange
        redis_key = "test:llen:count"
        await redis_repository._lpush(redis_key, "a")
        await redis_repository._lpush(redis_key, "b")
        await redis_repository._lpush(redis_key, "c")

        # Act
        length = await redis_repository._llen(redis_key)

        # Assert
        assert length == 3

    async def test_llen_reflects_pop(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that _llen() decreases after _brpop()."""
        # Arrange
        redis_key = "test:llen:pop"
        await redis_repository._lpush(redis_key, "a")
        await redis_repository._lpush(redis_key, "b")

        # Act
        await redis_repository._brpop(redis_key, timeout=1)

        # Assert
        assert await redis_repository._llen(redis_key) == 1


class TestBaseRedisRepositoryDelete:
    """Tests for BaseRedisRepository.delete()."""

    async def test_delete_removes_existing_key(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that delete() removes a key from Redis."""
        # Arrange
        redis_key = "test:delete:existing"
        await redis_repository._lpush(redis_key, "to_be_deleted")

        # Act
        await redis_repository.delete(redis_key)

        # Assert
        assert await redis_repository.exists(redis_key) is False

    async def test_delete_does_not_raise_for_missing_key(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that delete() is a no-op for a non-existent key."""
        # Act & Assert — should not raise
        await redis_repository.delete("test:delete:nonexistent")

    async def test_delete_removes_all_elements(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that delete() removes the entire list, not just one element."""
        # Arrange
        redis_key = "test:delete:full"
        await redis_repository._lpush(redis_key, "a")
        await redis_repository._lpush(redis_key, "b")
        await redis_repository._lpush(redis_key, "c")

        # Act
        await redis_repository.delete(redis_key)

        # Assert
        assert await redis_repository._llen(redis_key) == 0
        assert await redis_repository.exists(redis_key) is False


class TestBaseRedisRepositoryExists:
    """Tests for BaseRedisRepository.exists()."""

    async def test_exists_returns_false_for_missing_key(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that exists() returns False when the key is absent."""
        # Act & Assert
        assert await redis_repository.exists("test:exists:missing") is False

    async def test_exists_returns_true_for_present_key(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that exists() returns True when the key is present."""
        # Arrange
        redis_key = "test:exists:present"
        await redis_repository._lpush(redis_key, "some_value")

        # Act & Assert
        assert await redis_repository.exists(redis_key) is True

    async def test_exists_returns_false_after_delete(
        self,
        redis_repository: BaseRedisRepository,
    ) -> None:
        """Verify that exists() returns False after the key is deleted."""
        # Arrange
        redis_key = "test:exists:deleted"
        await redis_repository._lpush(redis_key, "temporary")
        await redis_repository.delete(redis_key)

        # Act & Assert
        assert await redis_repository.exists(redis_key) is False
