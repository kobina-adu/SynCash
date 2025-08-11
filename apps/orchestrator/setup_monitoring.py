#!/usr/bin/env python3
"""
Setup script for SyncCash Orchestrator production monitoring
"""
import os
import subprocess
import sys
from pathlib import Path

def create_monitoring_directories():
    """Create necessary monitoring directories"""
    directories = [
        "monitoring/grafana/datasources",
        "monitoring/grafana/dashboards",
        "monitoring/prometheus",
        "monitoring/alertmanager"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_grafana_datasource():
    """Create Grafana datasource configuration"""
    datasource_config = """
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
"""
    
    with open("monitoring/grafana/datasources/prometheus.yml", "w") as f:
        f.write(datasource_config)
    print("✅ Created Grafana datasource configuration")

def create_grafana_dashboard_config():
    """Create Grafana dashboard provisioning configuration"""
    dashboard_config = """
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
"""
    
    with open("monitoring/grafana/dashboards/dashboard.yml", "w") as f:
        f.write(dashboard_config)
    print("✅ Created Grafana dashboard configuration")

def start_monitoring_stack():
    """Start the monitoring stack using Docker Compose"""
    try:
        print("🚀 Starting monitoring stack...")
        subprocess.run([
            "docker-compose", 
            "-f", "monitoring/docker-compose.monitoring.yml", 
            "up", "-d"
        ], check=True)
        print("✅ Monitoring stack started successfully!")
        
        print("\n📊 Monitoring Services:")
        print("- Prometheus: http://localhost:9090")
        print("- Grafana: http://localhost:3000 (admin/synccash2024)")
        print("- AlertManager: http://localhost:9093")
        print("- Node Exporter: http://localhost:9100")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start monitoring stack: {e}")
        return False
    
    return True

def check_orchestrator_metrics():
    """Check if orchestrator metrics endpoint is accessible"""
    try:
        import requests
        response = requests.get("http://localhost:8000/metrics", timeout=5)
        if response.status_code == 200:
            print("✅ Orchestrator metrics endpoint is accessible")
            return True
        else:
            print(f"⚠️ Orchestrator metrics endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ Could not reach orchestrator metrics endpoint: {e}")
        return False

def main():
    """Main setup function"""
    print("🔧 Setting up SyncCash Orchestrator Production Monitoring")
    print("=" * 60)
    
    # Create directories
    create_monitoring_directories()
    
    # Create Grafana configurations
    create_grafana_datasource()
    create_grafana_dashboard_config()
    
    # Check if orchestrator is running
    print("\n🔍 Checking orchestrator service...")
    if check_orchestrator_metrics():
        print("✅ Orchestrator is running and metrics are available")
    else:
        print("⚠️ Orchestrator may not be running. Start it first with:")
        print("   docker-compose up -d orchestrator")
    
    # Start monitoring stack
    print("\n🚀 Starting monitoring infrastructure...")
    if start_monitoring_stack():
        print("\n🎉 Monitoring setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Open Grafana at http://localhost:3000")
        print("2. Import the SyncCash dashboard")
        print("3. Configure alert notification channels")
        print("4. Set up Slack/email integrations in AlertManager")
        
        print("\n🔧 To stop monitoring stack:")
        print("   docker-compose -f monitoring/docker-compose.monitoring.yml down")
    else:
        print("❌ Monitoring setup failed. Check Docker and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
