#!/usr/bin/env python3
"""
AceBuddy RAG - Deployment Validation Script
Validates local setup before production migration
"""

import subprocess
import json
import sys
import time
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def log_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")

def log_error(message):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")

def log_warning(message):
    print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")

def log_info(message):
    print(f"{Colors.BLUE}ℹ {message}{Colors.RESET}")

def run_command(cmd, shell=False, capture=True):
    """Run shell command and return result"""
    try:
        if capture:
            result = subprocess.run(cmd, shell=shell, capture_output=True, text=True, timeout=10)
            return result.returncode == 0, result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, shell=shell, timeout=10)
            return result.returncode == 0, "", ""
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_docker():
    """Verify Docker is installed and running"""
    log_info("Checking Docker installation...")
    success, stdout, stderr = run_command("docker --version")
    
    if success:
        log_success(f"Docker is installed: {stdout.strip()}")
    else:
        log_error("Docker not found. Please install Docker Desktop.")
        return False
    
    log_info("Checking Docker daemon...")
    success, stdout, stderr = run_command("docker ps")
    
    if success:
        log_success("Docker daemon is running")
        return True
    else:
        log_error("Docker daemon not running. Please start Docker Desktop.")
        return False

def check_ollama():
    """Verify Ollama is installed and model available"""
    log_info("Checking Ollama installation...")
    success, stdout, stderr = run_command("ollama --version")
    
    if success:
        log_success(f"Ollama is installed: {stdout.strip()}")
    else:
        log_error("Ollama not found. Please install Ollama.")
        return False
    
    log_info("Checking Ollama models...")
    success, stdout, stderr = run_command("ollama list")
    
    if success and "mistral" in stdout:
        log_success("Mistral model is available")
        return True
    elif success:
        log_warning("Ollama installed but mistral model not found. Pulling model...")
        success, _, _ = run_command("ollama pull mistral")
        if success:
            log_success("Mistral model pulled successfully")
            return True
        else:
            log_error("Failed to pull mistral model")
            return False
    else:
        log_error("Failed to check Ollama models")
        return False

def check_python():
    """Verify Python and required packages"""
    log_info("Checking Python installation...")
    success, stdout, stderr = run_command("python --version")
    
    if success:
        log_success(f"Python is installed: {stdout.strip()}")
    else:
        log_error("Python not found")
        return False
    
    log_info("Checking required Python packages...")
    required_packages = ["fastapi", "uvicorn", "chromadb", "sentence-transformers", "requests"]
    
    all_found = True
    for package in required_packages:
        cmd = f"python -c \"import {package}; print('{package}')\" 2>/dev/null"
        success, stdout, stderr = run_command(cmd, shell=True)
        
        if success:
            log_success(f"Package '{package}' is installed")
        else:
            log_warning(f"Package '{package}' might be missing")
            all_found = False
    
    return all_found

def check_project_structure():
    """Verify project directory structure"""
    log_info("Checking project structure...")
    
    required_files = [
        "app/main.py",
        "app/Dockerfile",
        "scripts/ingest_data.py",
        "docker-compose.yml",
        "requirements.txt",
        ".env",
        "README.md"
    ]
    
    required_dirs = [
        "app",
        "data",
        "scripts",
        "tests"
    ]
    
    all_good = True
    
    for directory in required_dirs:
        import os
        if os.path.isdir(directory):
            log_success(f"Directory exists: {directory}/")
        else:
            log_error(f"Directory missing: {directory}/")
            all_good = False
    
    for file in required_files:
        import os
        if os.path.isfile(file):
            log_success(f"File exists: {file}")
        else:
            log_error(f"File missing: {file}")
            all_good = False
    
    return all_good

def check_env_file():
    """Verify .env configuration"""
    log_info("Checking .env configuration...")
    
    import os
    if not os.path.isfile(".env"):
        log_error(".env file not found")
        return False
    
    with open(".env", "r") as f:
        content = f.read()
    
    required_vars = [
        "CHROMA_HOST",
        "OLLAMA_HOST",
        "FASTAPI_PORT"
    ]
    
    all_found = True
    for var in required_vars:
        if var in content:
            log_success(f"Environment variable '{var}' is configured")
        else:
            log_warning(f"Environment variable '{var}' might be missing")
            all_found = False
    
    return all_found

def build_docker_containers():
    """Build Docker containers"""
    log_info("Building Docker containers (this may take a few minutes)...")
    
    success, stdout, stderr = run_command(
        "docker-compose build --no-cache",
        shell=True,
        capture=True
    )
    
    if success:
        log_success("Docker containers built successfully")
        return True
    else:
        log_error(f"Docker build failed: {stderr}")
        return False

def start_docker_containers():
    """Start Docker containers"""
    log_info("Starting Docker containers...")
    
    success, stdout, stderr = run_command(
        "docker-compose up -d",
        shell=True,
        capture=True
    )
    
    if success:
        log_success("Docker containers started")
        log_info("Waiting for services to become healthy (30 seconds)...")
        time.sleep(30)
        return True
    else:
        log_error(f"Failed to start containers: {stderr}")
        return False

def check_containers_running():
    """Verify containers are running"""
    log_info("Checking container status...")
    
    success, stdout, stderr = run_command("docker ps", shell=True)
    
    if success:
        if "acebuddy-api" in stdout and "chroma" in stdout:
            log_success("Both containers are running")
            
            # Extract status
            for line in stdout.split('\n'):
                if "acebuddy-api" in line or "chroma" in line:
                    log_info(f"  {line.strip()}")
            
            return True
        else:
            log_error("One or more containers are not running")
            return False
    else:
        log_error("Failed to check container status")
        return False

def test_health_endpoint():
    """Test API health endpoint"""
    log_info("Testing health endpoint...")
    
    import requests
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            log_success(f"Health check passed: {data.get('status', 'unknown')}")
            
            if data.get('services'):
                log_info(f"  Services: {data['services']}")
            
            return True
        else:
            log_error(f"Health check failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        log_error("Could not connect to API. Is Docker running?")
        return False
    except Exception as e:
        log_error(f"Health check error: {str(e)}")
        return False

def test_chat_endpoint():
    """Test chat endpoint with sample query"""
    log_info("Testing chat endpoint...")
    
    import requests
    
    try:
        payload = {
            "query": "How do I reset my password?",
            "user_id": "test_user"
        }
        
        response = requests.post(
            "http://localhost:8000/chat",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            log_success("Chat endpoint working")
            log_info(f"  Answer preview: {data.get('answer', 'N/A')[:100]}...")
            
            if data.get('context'):
                log_info(f"  Retrieved {len(data['context'])} context items")
            
            return True
        else:
            log_error(f"Chat endpoint failed with status {response.status_code}")
            log_info(f"  Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        log_warning("Chat request timed out. This may happen if Ollama is busy.")
        return False
    except requests.exceptions.ConnectionError:
        log_error("Could not connect to API")
        return False
    except Exception as e:
        log_error(f"Chat test error: {str(e)}")
        return False

def check_container_logs():
    """Display container logs"""
    log_info("Retrieving container logs (last 20 lines)...")
    
    success, stdout, stderr = run_command(
        "docker logs --tail=20 acebuddy-api",
        shell=True
    )
    
    if success:
        log_info("API Logs:")
        for line in stdout.split('\n')[-10:]:
            if line.strip():
                print(f"  {line}")
    else:
        log_warning("Could not retrieve API logs")

def cleanup_containers():
    """Stop and remove containers"""
    log_info("Stopping Docker containers...")
    
    success, stdout, stderr = run_command(
        "docker-compose down",
        shell=True
    )
    
    if success:
        log_success("Containers stopped and removed")
    else:
        log_warning("Failed to stop containers")

def generate_report(results):
    """Generate validation report"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
╔═══════════════════════════════════════════════════════════════╗
║         AceBuddy RAG Deployment Validation Report            ║
╚═══════════════════════════════════════════════════════════════╝

Generated: {timestamp}

PRE-DEPLOYMENT CHECKS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Docker installed          : {results['docker_installed']}
✓ Docker running            : {results['docker_running']}
✓ Ollama installed          : {results['ollama_installed']}
✓ Ollama model available    : {results['ollama_model']}
✓ Python installed          : {results['python_installed']}
✓ Python packages           : {results['python_packages']}
✓ Project structure         : {results['project_structure']}
✓ .env configured           : {results['env_configured']}

BUILD & DEPLOYMENT CHECKS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Docker build successful   : {results['docker_build']}
✓ Containers started        : {results['containers_started']}
✓ Containers running        : {results['containers_running']}

FUNCTIONAL TESTS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Health endpoint           : {results['health_endpoint']}
✓ Chat endpoint             : {results['chat_endpoint']}

OVERALL STATUS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    # Count passes and failures
    total = len(results)
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    
    report += f"Total Checks: {total} | Passed: {passed} | Failed: {failed}\n"
    
    if failed == 0:
        report += f"\n{Colors.GREEN}✓ ALL CHECKS PASSED! System is ready for deployment.{Colors.RESET}\n"
    else:
        report += f"\n{Colors.RED}✗ Some checks failed. Please review the issues above.{Colors.RESET}\n"
    
    report += """
NEXT STEPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Review any failed checks above
2. Fix issues as recommended
3. Re-run this validation script
4. Once all checks pass, proceed with production migration
5. Follow SETUP_CHECKLIST.md Phase 3 for server deployment

SUPPORT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Refer to:
  - SETUP_CHECKLIST.md for detailed setup instructions
  - QUICK_REFERENCE.md for common commands
  - docker logs <container> for debugging

═══════════════════════════════════════════════════════════════════
"""
    
    return report

def main():
    """Run all validation checks"""
    print(f"\n{Colors.BLUE}╔══════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BLUE}║  AceBuddy RAG - Deployment Validation Script    ║{Colors.RESET}")
    print(f"{Colors.BLUE}╚══════════════════════════════════════════════════╝{Colors.RESET}\n")
    
    results = {}
    
    # Phase 1: Pre-deployment checks
    print(f"{Colors.BLUE}Phase 1: Pre-Deployment Checks{Colors.RESET}")
    print("=" * 60)
    
    results['docker_installed'] = check_docker()
    if not results['docker_installed']:
        print("\nDocker is required. Exiting.")
        sys.exit(1)
    
    results['docker_running'] = results['docker_installed']  # If installed, we checked it's running
    results['ollama_installed'] = check_ollama()
    results['ollama_model'] = results['ollama_installed']
    results['python_installed'] = check_python()
    results['python_packages'] = results['python_installed']
    results['project_structure'] = check_project_structure()
    results['env_configured'] = check_env_file()
    
    print("\n" + "=" * 60)
    
    # Phase 2: Build and deploy
    print(f"\n{Colors.BLUE}Phase 2: Build & Deployment{Colors.RESET}")
    print("=" * 60)
    
    results['docker_build'] = build_docker_containers()
    if not results['docker_build']:
        print("\nDocker build failed. Check logs above.")
        sys.exit(1)
    
    results['containers_started'] = start_docker_containers()
    if not results['containers_started']:
        print("\nFailed to start containers.")
        sys.exit(1)
    
    results['containers_running'] = check_containers_running()
    
    print("\n" + "=" * 60)
    
    # Phase 3: Functional tests
    print(f"\n{Colors.BLUE}Phase 3: Functional Tests{Colors.RESET}")
    print("=" * 60)
    
    results['health_endpoint'] = test_health_endpoint()
    results['chat_endpoint'] = test_chat_endpoint()
    
    print("\n" + "=" * 60)
    
    # Display logs
    print(f"\n{Colors.BLUE}Container Logs{Colors.RESET}")
    print("=" * 60)
    check_container_logs()
    
    # Cleanup
    print(f"\n{Colors.BLUE}Cleanup{Colors.RESET}")
    print("=" * 60)
    cleanup_containers()
    
    # Generate and display report
    report = generate_report(results)
    print(report)
    
    # Save report
    import os
    report_file = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    log_info(f"Report saved to: {report_file}")
    
    # Exit with appropriate code
    failed = sum(1 for v in results.values() if v is False)
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()
