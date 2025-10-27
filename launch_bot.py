
import os
import sys
import subprocess
import traceback

def check_requirements():
    try:
        print("🔍 Checking requirements...")
        
        required_packages = [
            'torch',
            'pyautogui', 
            'psutil',
            'pynput',
            'opencv-python',
            'numpy',
            'pillow',
            'python-dotenv',
            'inference-sdk'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                if package == 'opencv-python':
                    import cv2
                elif package == 'python-dotenv':
                    import dotenv
                elif package == 'inference-sdk':
                    import inference_sdk
                else:
                    __import__(package)
                print(f"✅ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package} - MISSING")
        
        if missing_packages:
            print(f"\n❌ Missing packages: {missing_packages}")
            print("📦 Install missing packages with:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
        
        print("✅ All required packages are installed!")
        return True
        
    except Exception as e:
        print(f"❌ Error checking requirements: {e}")
        return False

def check_environment_file():
    try:
        print("🔍 Checking .env file...")
        
        env_file = ".env"
        if not os.path.exists(env_file):
            print("❌ .env file not found!")
            print("📝 Please create a .env file with the following variables:")
            print("   ROBOFLOW_API_KEY=your_api_key_here")
            print("   WORKSPACE_TROOP_DETECTION=your_workspace_name")
            print("   WORKSPACE_CARD_DETECTION=your_workspace_name")
            print("   INFERENCE_API_URL=http://localhost:9001")
            return False
        
        # Try to load and check .env file
        from dotenv import load_dotenv
        load_dotenv()
        
        required_vars = [
            'ROBOFLOW_API_KEY',
            'WORKSPACE_TROOP_DETECTION',
            'WORKSPACE_CARD_DETECTION'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Missing environment variables: {missing_vars}")
            print("📝 Please add these to your .env file")
            return False
        
        print("✅ .env file configured correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Error checking .env file: {e}")
        return False

def check_directories():
    try:
        print("🔍 Checking directories...")
        
        directories = [
            "models",
            "logs", 
            "screenshots",
            "main_images",
            "images/buttons"
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                print(f"📁 Created directory: {directory}")
            else:
                print(f"✅ Directory exists: {directory}")
        
        print("✅ All directories ready!")
        return True
        
    except Exception as e:
        print(f"❌ Error checking directories: {e}")
        return False

def launch_bot():
    try:
        print("🚀 Launching Automated Clash Royale AI Bot...")
        print("=" * 60)
        
        from automated_clash_bot import main
        main()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot launch interrupted by user")
    except Exception as e:
        print(f"❌ Error launching bot: {e}")
        print("\n🔍 Full error traceback:")
        traceback.print_exc()

def main():
    print("🤖 CLASH ROYALE AI BOT LAUNCHER")
    print("=" * 50)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📁 Working directory: {script_dir}")
    print("\n🔧 Running pre-flight checks...")
    
    if not check_requirements():
        print("❌ Requirements check failed!")
        input("Press Enter to exit...")
        return
    
    if not check_environment_file():
        print("❌ Environment check failed!")
        input("Press Enter to exit...")
        return
    
    if not check_directories():
        print("❌ Directory check failed!")
        input("Press Enter to exit...")
        return
    
    print("\n✅ All pre-flight checks passed!")
    print("🎯 Ready to launch bot!")
    response = input("\n🚀 Launch the bot? (y/N): ").lower().strip()
    if response in ['y', 'yes']:
        launch_bot()
    else:
        print("👋 Launch cancelled by user")

if __name__ == "__main__":
    main()