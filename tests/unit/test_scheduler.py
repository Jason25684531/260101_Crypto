"""
测试排程器核心功能
Test Scheduler Core Functionality

验证：
1. Scheduler 能正常启动
2. 能添加和执行 Job
3. 能优雅关闭
"""
import time
import pytest
from app.core.scheduler import Scheduler


class TestScheduler:
    """测试排程器的生命周期与基本功能"""

    def test_scheduler_start_and_shutdown(self):
        """测试排程器能正常启动并关闭"""
        scheduler = Scheduler()
        
        # 启动排程器
        scheduler.start()
        assert scheduler.is_running() is True
        
        # 关闭排程器
        scheduler.shutdown()
        assert scheduler.is_running() is False

    def test_scheduler_executes_job(self):
        """测试排程器能执行已排程的任务"""
        scheduler = Scheduler()
        execution_log = []

        def dummy_job():
            """测试用的虚拟任务"""
            execution_log.append(time.time())

        scheduler.start()
        
        # 添加一个每秒执行的任务
        scheduler.add_job(
            func=dummy_job,
            trigger='interval',
            seconds=1,
            id='test_job'
        )
        
        # 等待任务执行至少 2 次
        time.sleep(2.5)
        
        # 验证任务确实被执行了
        assert len(execution_log) >= 2, "任务应该至少执行 2 次"
        
        scheduler.shutdown()

    def test_scheduler_job_isolation(self):
        """测试多个任务之间互不干扰"""
        scheduler = Scheduler()
        job1_log = []
        job2_log = []

        def job1():
            job1_log.append('job1')

        def job2():
            job2_log.append('job2')

        scheduler.start()
        
        scheduler.add_job(func=job1, trigger='interval', seconds=1, id='job1')
        scheduler.add_job(func=job2, trigger='interval', seconds=1, id='job2')
        
        time.sleep(2.5)
        
        # 两个任务都应该被执行
        assert len(job1_log) >= 2
        assert len(job2_log) >= 2
        
        scheduler.shutdown()

    def test_scheduler_timezone_is_utc(self):
        """测试排程器使用 UTC 时区"""
        scheduler = Scheduler()
        scheduler.start()
        
        # 检查时区配置
        timezone = scheduler.get_timezone()
        assert str(timezone) == 'UTC', "排程器应该使用 UTC 时区"
        
        scheduler.shutdown()

    def test_scheduler_graceful_shutdown(self):
        """测试优雅关闭：确保正在执行的任务不会被强制中断"""
        scheduler = Scheduler()
        execution_started = []
        execution_finished = []

        def slow_job():
            """模拟慢任务"""
            execution_started.append(True)
            time.sleep(1)  # 模拟耗时操作
            execution_finished.append(True)

        scheduler.start()
        scheduler.add_job(func=slow_job, trigger='interval', seconds=2, id='slow_job')
        
        time.sleep(0.5)  # 让任务开始执行
        
        # 请求关闭
        scheduler.shutdown(wait=True)
        
        # 如果任务已开始，应该能完成
        if execution_started:
            assert len(execution_finished) > 0, "已开始的任务应该能完成"
