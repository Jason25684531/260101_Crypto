"""手动测试 Scheduler 功能"""
import time
import sys
sys.path.insert(0, 'D:\\01_Project\\260101_Crypto')

from app.core.scheduler import Scheduler


def test_basic_functionality():
    """测试基本功能"""
    print("=" * 60)
    print("测试 1: 基本启动和关闭")
    print("=" * 60)
    
    scheduler = Scheduler()
    scheduler.start()
    assert scheduler.is_running(), "❌ Scheduler 应该在运行中"
    print("✓ Scheduler 启动成功")
    
    assert str(scheduler.get_timezone()) == "UTC", "❌ 时区应该是 UTC"
    print("✓ 时区设置正确: UTC")
    
    scheduler.shutdown()
    assert not scheduler.is_running(), "❌ Scheduler 应该已停止"
    print("✓ Scheduler 关闭成功")
    print()


def test_job_execution():
    """测试任务执行"""
    print("=" * 60)
    print("测试 2: 任务执行")
    print("=" * 60)
    
    scheduler = Scheduler()
    execution_log = []
    
    def test_job():
        execution_log.append(time.time())
        print(f"  → 任务执行 #{len(execution_log)}")
    
    scheduler.start()
    scheduler.add_job(
        func=test_job,
        trigger='interval',
        seconds=1,
        id='test_job'
    )
    print("✓ 任务已添加，每 1 秒执行一次")
    
    print("等待任务执行 3 次...")
    time.sleep(3.5)
    
    assert len(execution_log) >= 3, f"❌ 任务应该至少执行 3 次，实际: {len(execution_log)}"
    print(f"✓ 任务成功执行了 {len(execution_log)} 次")
    
    scheduler.shutdown()
    print()


def test_multiple_jobs():
    """测试多任务隔离"""
    print("=" * 60)
    print("测试 3: 多任务隔离")
    print("=" * 60)
    
    scheduler = Scheduler()
    job1_count = []
    job2_count = []
    
    def job1():
        job1_count.append(1)
        print(f"  → Job 1 执行 #{len(job1_count)}")
    
    def job2():
        job2_count.append(1)
        print(f"  → Job 2 执行 #{len(job2_count)}")
    
    scheduler.start()
    scheduler.add_job(func=job1, trigger='interval', seconds=1, id='job1')
    scheduler.add_job(func=job2, trigger='interval', seconds=1, id='job2')
    print("✓ 已添加 2 个任务")
    
    print("等待任务执行...")
    time.sleep(2.5)
    
    assert len(job1_count) >= 2, f"❌ Job 1 应该至少执行 2 次，实际: {len(job1_count)}"
    assert len(job2_count) >= 2, f"❌ Job 2 应该至少执行 2 次，实际: {len(job2_count)}"
    print(f"✓ Job 1 执行了 {len(job1_count)} 次")
    print(f"✓ Job 2 执行了 {len(job2_count)} 次")
    
    scheduler.shutdown()
    print()


def test_graceful_shutdown():
    """测试优雅关闭"""
    print("=" * 60)
    print("测试 4: 优雅关闭")
    print("=" * 60)
    
    scheduler = Scheduler()
    started = []
    finished = []
    
    def slow_job():
        started.append(True)
        print("  → 慢任务开始执行...")
        time.sleep(0.5)
        finished.append(True)
        print("  → 慢任务执行完成")
    
    scheduler.start()
    scheduler.add_job(func=slow_job, trigger='interval', seconds=2, id='slow_job')
    print("✓ 已添加慢任务（每 2 秒执行一次，耗时 0.5 秒）")
    
    time.sleep(0.3)  # 让任务开始
    print("请求关闭 Scheduler...")
    scheduler.shutdown(wait=True)
    
    if started:
        assert len(finished) > 0, "❌ 已开始的任务应该能完成"
        print(f"✓ 优雅关闭成功：已开始的任务完成了")
    else:
        print("✓ 优雅关闭成功（任务尚未开始）")
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "Scheduler 功能测试" + " " * 23 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    try:
        test_basic_functionality()
        test_job_execution()
        test_multiple_jobs()
        test_graceful_shutdown()
        
        print("╔" + "=" * 58 + "╗")
        print("║" + " " * 18 + "所有测试通过！✓" + " " * 24 + "║")
        print("╚" + "=" * 58 + "╝")
        print()
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
