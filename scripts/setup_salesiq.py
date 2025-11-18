#!/usr/bin/env python3
"""
Zoho SalesIQ Integration Setup
Configures AceBuddy RAG chatbot for SalesIQ webhook integration
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

def setup_salesiq_integration():
    """Setup SalesIQ integration"""
    
    print("\n" + "="*60)
    print("🚀 Zoho SalesIQ Integration Setup")
    print("="*60 + "\n")
    
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Configuration
    config = {
        "salesiq": {
            "enabled": True,
            "webhook_path": "/salesiq/webhook",
            "chat_endpoint": "/salesiq/chat",
            "min_confidence_threshold": 0.7,
            "min_quality_threshold": 0.6,
            "max_response_time_ms": 5000
        },
        "integration": {
            "escalation_enabled": True,
            "conversation_history": True,
            "query_enhancement": True,
            "analytics_tracking": True
        }
    }
    
    # Step 1: Update .env file
    print("📝 Step 1: Updating .env configuration...")
    env_file = project_root / ".env"
    
    env_vars = {
        "SALESIQ_ENABLED": "true",
        "SALESIQ_API_KEY": input("Enter your SalesIQ API key (or press Enter to skip): ").strip() or "your-api-key-here",
        "SALESIQ_WEBHOOK_SECRET": input("Enter webhook secret (or press Enter to skip): ").strip() or "your-secret-here",
        "MIN_CONFIDENCE_THRESHOLD": "0.7",
        "MIN_QUALITY_THRESHOLD": "0.6"
    }
    
    # Read existing .env
    existing_vars = {}
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    existing_vars[key] = value
    
    # Merge and write
    all_vars = {**existing_vars, **env_vars}
    with open(env_file, 'w') as f:
        f.write("# AceBuddy RAG Configuration\n")
        f.write(f"# Updated: {datetime.now().isoformat()}\n\n")
        for key, value in all_vars.items():
            f.write(f"{key}={value}\n")
    
    print(f"✅ .env file updated: {env_file}\n")
    
    # Step 2: Create integration config
    print("📋 Step 2: Creating SalesIQ integration config...")
    config_file = project_root / "data" / "salesiq_config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Config file created: {config_file}\n")
    
    # Step 3: Display webhook URLs
    print("🔗 Step 3: Webhook Configuration\n")
    
    server_url = input("Enter your server URL (e.g., https://your-server.com or http://localhost:8000): ").strip()
    
    webhook_urls = {
        "webhook_endpoint": f"{server_url}/salesiq/webhook",
        "chat_endpoint": f"{server_url}/salesiq/chat",
        "status_endpoint": f"{server_url}/salesiq/status",
        "test_endpoint": f"{server_url}/salesiq/test"
    }
    
    print("\n📌 Add these URLs to Zoho SalesIQ Webhook Configuration:\n")
    for endpoint_type, url in webhook_urls.items():
        print(f"  {endpoint_type}:")
        print(f"    URL: {url}")
        print(f"    Method: POST")
        print(f"    Content-Type: application/json\n")
    
    # Save webhook URLs
    webhook_file = project_root / "data" / "salesiq_webhooks.json"
    with open(webhook_file, 'w') as f:
        json.dump(webhook_urls, f, indent=2)
    
    print(f"✅ Webhook URLs saved to: {webhook_file}\n")
    
    # Step 4: Integration code
    print("🔧 Step 4: Integration Code Status\n")
    
    integration_file = project_root / "app" / "salesiq_integration.py"
    if integration_file.exists():
        print(f"✅ SalesIQ integration module found: {integration_file}")
        print("   Functions available:")
        print("   - /salesiq/webhook: Incoming webhook handler")
        print("   - /salesiq/chat: Direct chat endpoint")
        print("   - /salesiq/status: Health check")
        print("   - /salesiq/test: Test endpoint")
        print("   - /salesiq/analytics: Analytics data\n")
    else:
        print(f"❌ Integration module not found: {integration_file}\n")
    
    # Step 5: Update main.py
    print("⚙️  Step 5: Updating main.py to include SalesIQ routes...\n")
    
    main_file = project_root / "app" / "main.py"
    if main_file.exists():
        with open(main_file, 'r') as f:
            main_content = f.read()
        
        if "salesiq_integration" in main_content:
            print("✅ SalesIQ routes already integrated in main.py\n")
        else:
            print("⚠️  Need to add SalesIQ integration to main.py")
            print("   Add this to app/main.py after FastAPI initialization:\n")
            print("   from app.salesiq_integration import add_salesiq_routes")
            print("   add_salesiq_routes(app)\n")
    
    # Step 6: Testing
    print("🧪 Step 6: Testing Your Integration\n")
    
    print("Run these commands to test:\n")
    print("1. Health check:")
    print(f"   curl {server_url}/salesiq/status\n")
    
    print("2. Test chat endpoint:")
    print(f"""   curl -X POST {server_url}/salesiq/chat \\
     -H "Content-Type: application/json" \\
     -d '{{"query": "How do I reset my password?", "visitor_id": "test", "chat_id": "test"}}'
\n""")
    
    print("3. View analytics:")
    print(f"   curl {server_url}/salesiq/analytics\n")
    
    # Step 7: SalesIQ Configuration Summary
    print("📋 Step 7: Configuration Summary\n")
    
    summary = f"""
ZOHO SALESIQ INTEGRATION SETUP COMPLETE
========================================

Server URL: {server_url}
Webhook Path: /salesiq/webhook
Chat Endpoint: /salesiq/chat

Thresholds:
- Min Confidence: {config['salesiq']['min_confidence_threshold']}
- Min Quality: {config['salesiq']['min_quality_threshold']}
- Max Response Time: {config['salesiq']['max_response_time_ms']}ms

Features Enabled:
✓ Escalation to human agents
✓ Conversation history
✓ Query enhancement
✓ Analytics tracking

Next Steps:
1. Start your API server:
   python app/main.py

2. Configure webhook in Zoho SalesIQ:
   - Go to Settings → Integrations → Webhooks
   - Add webhook URL: {webhook_urls['webhook_endpoint']}
   - Set method to POST
   - Test connection

3. Create bot flow in SalesIQ:
   - Create new bot
   - Add webhook action
   - Test with sample query

4. Monitor integration:
   - Check /salesiq/analytics for metrics
   - Monitor logs for errors
   - Track escalation rates

Documentation: See ZOHO_SALESIQ_INTEGRATION.md
"""
    
    print(summary)
    
    # Save summary
    summary_file = project_root / "SALESIQ_SETUP_SUMMARY.txt"
    with open(summary_file, 'w') as f:
        f.write(summary)
    
    print(f"✅ Setup summary saved to: {summary_file}\n")
    
    print("="*60)
    print("✨ SalesIQ Integration Setup Complete!")
    print("="*60 + "\n")


def verify_installation():
    """Verify all required files are in place"""
    
    print("🔍 Verifying installation...\n")
    
    project_root = Path(__file__).parent.parent
    required_files = [
        "app/salesiq_integration.py",
        "ZOHO_SALESIQ_INTEGRATION.md",
        ".env"
    ]
    
    all_exist = True
    for file in required_files:
        file_path = project_root / file
        if file_path.exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (missing)")
            all_exist = False
    
    return all_exist


if __name__ == "__main__":
    try:
        if verify_installation():
            setup_salesiq_integration()
        else:
            print("\n⚠️  Some files are missing. Please check installation.\n")
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user.\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during setup: {e}\n")
        sys.exit(1)
