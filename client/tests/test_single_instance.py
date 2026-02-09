from utils.single_instance import SingleInstance


class TestSingleInstance:
    def test_acquire_succeeds_first_time(self, tmp_path):
        lock = SingleInstance(lock_dir=tmp_path)
        assert lock.acquire() is True
        lock.release()

    def test_double_acquire_fails(self, tmp_path):
        lock1 = SingleInstance(lock_dir=tmp_path)
        lock2 = SingleInstance(lock_dir=tmp_path)
        assert lock1.acquire() is True
        assert lock2.acquire() is False
        lock1.release()

    def test_release_allows_reacquire(self, tmp_path):
        lock1 = SingleInstance(lock_dir=tmp_path)
        assert lock1.acquire() is True
        lock1.release()
        lock2 = SingleInstance(lock_dir=tmp_path)
        assert lock2.acquire() is True
        lock2.release()

    def test_context_manager(self, tmp_path):
        with SingleInstance(lock_dir=tmp_path) as acquired:
            assert acquired is True

