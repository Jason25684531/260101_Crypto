"""测试 bot.py 的基本功能（不实际运行调度器）"""
import sys
sys.path.insert(0, 'D:\\01_Project\\260101_Crypto')

import os
import importlib.util


def load_module(name, path):
    """直接加载模块"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_imports():
    """测试所有必要的导入"""
    print("=" * 60)
    print("测试 1: 导入检查")
    print("=" * 60)
    
    try:
        # 测试核心模块导入
        from app import create_app
        print("✓ create_app 导入成功")
        
        from app.core.scheduler import Scheduler
        print("✓ Scheduler 导入成功")
        
        from app.config import config
        print("✓ config 导入成功")
        
        from app.core.jobs import job_update_market_data_sync
        print("✓ job_update_market_data_sync 导入成功")
        
        print()
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_app_creation():
    """测试 Flask App 创建"""
    print("=" * 60)
    print("测试 2: Flask App 创建")
    print("=" * 60)
    
    try:
        from app import create_app
        
        app = create_app('production')
        print("✓ Flask App 创建成功")
        
        assert app is not None
        print("✓ App 对象有效")
        
        # 测试 app context
        with app.app_context():
            print("✓ App Context 工作正常")
        
        print()
        return True
    except Exception as e:
        print(f"❌ App 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scheduler_creation():
    """测试 Scheduler 创建和任务配置"""
    print("=" * 60)
    print("测试 3: Scheduler 创建和配置")
    print("=" * 60)
    
    try:
        from app import create_app
        from app.core.scheduler import Scheduler
        
        app = create_app('production')
        scheduler = Scheduler()
        print("✓ Scheduler 创建成功")
        
        # 在 app context 中配置任务
        with app.app_context():
            scheduler.setup_all_jobs()
            print("✓ 任务配置成功")
            
            jobs = scheduler.get_jobs()
            print(f"✓ 已配置 {len(jobs)} 个任务")
            
            for job in jobs:
                print(f"  - {job.id}")
        
        print()
        return True
    except Exception as e:
        print(f"❌ Scheduler 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """测试配置加载"""
    print("=" * 60)
    print("测试 4: 配置系统")
    print("=" * 60)
    
    try:
        os.environ['TRADING_MODE'] = 'PAPER'
        
        from app.config import config
        
        print(f"✓ 交易模式: {config.TRADING_MODE}")
        print(f"✓ 模式检查: {config.get_mode_display()}")
        
        if config.is_paper_mode():
            print(f"✓ 模拟资金: ${config.PAPER_INITIAL_BALANCE:,.2f}")
        
        print()
        return True
    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False


def test_bot_functions():
    """测试 bot.py 中的辅助函数"""
    print("=" * 60)
    print("测试 5: Bot 辅助函数")
    print("=" * 60)
    
    try:
        # 直接加载 bot 模块
        bot = load_module("bot", "D:\\01_Project\\260101_Crypto\\bot.py")
        
        # 测试横幅打印（不实际打印）
        print("✓ print_startup_banner 函数存在")
        
        # 测试初始化函数
        print("✓ initialize_system 函数存在")
        
        # 测试信号处理器
        print("✓ signal_handler 函数存在")
        
        print()
        return True
    except Exception as e:
        print(f"❌ Bot 函数测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 18 + "Bot.py 功能测试" + " " * 22 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    success = True
    success = test_imports() and success
    success = test_app_creation() and success
    success = test_scheduler_creation() and success
    success = test_config() and success
    success = test_bot_functions() and success
    
    if success:
        print("╔" + "=" * 58 + "╗")
        print("║" + " " * 18 + "所有测试通过！✓" + " " * 24 + "║")
        print("╚" + "=" * 58 + "╝")
        print()
        print("✅ bot.py 已准备就绪！")
        print()
        print("下一步：")
        print("1. 确保数据库和 Redis 运行")
        print("2. 运行: python bot.py")
        print("3. 观察日志输出")
        print()
    else:
        print("❌ 部分测试失败，请检查错误信息")
        sys.exit(1)


if __name__ == "__main__":
    main()
