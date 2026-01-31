"""
系统排程器 - 自动化的心跳
System Scheduler - The Heartbeat of Automation

负责：
1. 定时触发数据爬取任务
2. 定时触发策略扫描任务
3. 管理所有后台定时任务的生命周期
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from pytz import utc
import logging


logger = logging.getLogger(__name__)


class Scheduler:
    """
    系统排程器封装类
    
    基于 APScheduler，提供便捷的任务管理接口
    默认使用 UTC 时区，确保跨时区部署的一致性
    """

    def __init__(self):
        """初始化排程器配置"""
        jobstores = {
            'default': MemoryJobStore()
        }
        
        executors = {
            'default': ThreadPoolExecutor(max_workers=10)
        }
        
        job_defaults = {
            'coalesce': True,  # 合并错过的执行
            'max_instances': 1,  # 同一任务不允许并发执行
            'misfire_grace_time': 30  # 错过执行的宽限时间（秒）
        }
        
        self._scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=utc
        )
        
        logger.info("Scheduler initialized with UTC timezone")

    def start(self):
        """启动排程器"""
        if not self._scheduler.running:
            self._scheduler.start()
            logger.info("Scheduler started successfully")
        else:
            logger.warning("Scheduler is already running")

    def shutdown(self, wait=True):
        """
        关闭排程器
        
        Args:
            wait: 是否等待正在执行的任务完成（默认为 True，确保优雅关闭）
        """
        if self._scheduler.running:
            self._scheduler.shutdown(wait=wait)
            logger.info("Scheduler shutdown successfully")
        else:
            logger.warning("Scheduler is not running")

    def is_running(self):
        """检查排程器是否正在运行"""
        return self._scheduler.running

    def get_timezone(self):
        """获取排程器的时区配置"""
        return self._scheduler.timezone

    def add_job(self, func, trigger, **kwargs):
        """
        添加一个定时任务
        
        Args:
            func: 要执行的函数
            trigger: 触发器类型 ('interval', 'cron', 'date')
            **kwargs: 传递给 APScheduler 的其他参数
        
        Returns:
            Job 对象
        """
        job = self._scheduler.add_job(func, trigger, **kwargs)
        logger.info(f"Job '{kwargs.get('id', 'unnamed')}' added with trigger '{trigger}'")
        return job

    def remove_job(self, job_id):
        """
        移除一个定时任务
        
        Args:
            job_id: 任务的唯一标识符
        """
        try:
            self._scheduler.remove_job(job_id)
            logger.info(f"Job '{job_id}' removed successfully")
        except Exception as e:
            logger.error(f"Failed to remove job '{job_id}': {e}")

    def get_jobs(self):
        """获取所有已排程的任务列表"""
        return self._scheduler.get_jobs()

    def print_jobs(self):
        """打印所有已排程的任务（用于调试）"""
        jobs = self.get_jobs()
        if not jobs:
            logger.info("No jobs scheduled")
            return
        
        logger.info(f"Total {len(jobs)} job(s) scheduled:")
        for job in jobs:
            # APScheduler 的 Job 对象使用 next_run_time 属性
            next_run = getattr(job, 'next_run_time', 'N/A')
            logger.info(f"  - {job.id}: next run at {next_run}")

    def setup_market_data_jobs(self):
        """
        设置市场数据更新任务
        Setup Market Data Update Jobs
        
        功能：每 1 分钟在第 5 秒执行数据更新
        作用：自动从交易所获取最新 K 线数据
        """
        from app.core.jobs import job_update_market_data_sync
        
        self.add_job(
            func=job_update_market_data_sync,
            trigger='cron',
            second=5,  # 每分钟的第 5 秒执行
            id='job_update_market_data',
            replace_existing=True
        )
        logger.info("✅ Market data update job scheduled (every minute at :05)")

    def setup_signal_scan_jobs(self):
        """
        设置策略信号扫描任务
        Setup Signal Scanning Jobs
        
        功能：每 1 分钟在第 10 秒执行策略扫描
        作用：自动检测交易信号并执行交易
        """
        from app.core.jobs import job_scan_signals_sync
        
        self.add_job(
            func=job_scan_signals_sync,
            trigger='cron',
            second=10,  # 每分钟的第 10 秒执行（确保数据已更新）
            id='job_scan_signals',
            replace_existing=True
        )
        logger.info("✅ Signal scan job scheduled (every minute at :10)")

    def setup_all_jobs(self):
        """
        一键设置所有定时任务
        Setup All Scheduled Jobs
        
        包含：
        1. 市场数据更新（每分钟 :05）
        2. 策略信号扫描（每分钟 :10）
        """
        logger.info("🔧 Setting up all scheduled jobs...")
        
        self.setup_market_data_jobs()
        self.setup_signal_scan_jobs()
        
        logger.info("✅ All jobs setup complete")
        self.print_jobs()
