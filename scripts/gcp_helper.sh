#!/bin/bash
################################################################################
# GCP Quick Setup Script
# 
# Automates common GCP deployment tasks for APT Attack Detection
################################################################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
INSTANCE_NAME="apt-detection-vm"
ZONE="asia-southeast1-a"
MACHINE_TYPE="e2-standard-4"
DISK_SIZE="100GB"

echo -e "${BLUE}🚀 APT Detection - GCP Quick Setup${NC}"
echo

# Function to show menu
show_menu() {
    echo -e "${YELLOW}Select action:${NC}"
    echo "  1) Create VM Instance"
    echo "  2) SSH into VM"
    echo "  3) Upload code to VM"
    echo "  4) Download results from VM"
    echo "  5) Start VM"
    echo "  6) Stop VM"
    echo "  7) Delete VM"
    echo "  8) View VM status"
    echo "  9) Setup port forwarding (Jupyter)"
    echo "  0) Exit"
    echo
}

create_vm() {
    echo -e "${GREEN}Creating VM instance...${NC}"
    gcloud compute instances create $INSTANCE_NAME \
      --zone=$ZONE \
      --machine-type=$MACHINE_TYPE \
      --image-family=ubuntu-2204-lts \
      --image-project=ubuntu-os-cloud \
      --boot-disk-size=$DISK_SIZE \
      --boot-disk-type=pd-balanced \
      --tags=http-server,https-server
    
    echo -e "${GREEN}✅ VM created successfully!${NC}"
    echo
    echo "Next steps:"
    echo "1. SSH into VM (option 2)"
    echo "2. Follow GCP_DEPLOYMENT_GUIDE.md sections 3-4"
}

ssh_vm() {
    echo -e "${GREEN}Connecting to VM via SSH...${NC}"
    gcloud compute ssh $INSTANCE_NAME --zone=$ZONE
}

upload_code() {
    echo -e "${GREEN}Uploading code to VM...${NC}"
    
    # Check if we're in the repo directory
    if [ ! -f "README.md" ]; then
        echo -e "${RED}Error: Not in APT-Attack-Detection directory${NC}"
        echo "Please run this script from the repo root"
        return 1
    fi
    
    # Compress code
    echo "Compressing code..."
    tar -czf /tmp/apt-detection-code.tar.gz \
        --exclude='.git' \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.venv' \
        --exclude='runs' \
        .
    
    # Upload
    echo "Uploading to VM..."
    gcloud compute scp /tmp/apt-detection-code.tar.gz \
        $INSTANCE_NAME:/tmp/ \
        --zone=$ZONE
    
    # Extract on VM
    echo "Extracting on VM..."
    gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --command="\
        sudo mkdir -p /opt/apt-detection && \
        sudo chown \$USER:\$USER /opt/apt-detection && \
        cd /opt/apt-detection && \
        tar -xzf /tmp/apt-detection-code.tar.gz && \
        rm /tmp/apt-detection-code.tar.gz && \
        echo '✅ Code uploaded to /opt/apt-detection'"
    
    # Cleanup
    rm /tmp/apt-detection-code.tar.gz
    
    echo -e "${GREEN}✅ Code uploaded successfully!${NC}"
}

download_results() {
    echo -e "${GREEN}Downloading results from VM...${NC}"
    
    mkdir -p ~/Desktop/apt-results-$(date +%Y%m%d_%H%M%S)
    DEST=~/Desktop/apt-results-$(date +%Y%m%d_%H%M%S)
    
    echo "Downloading to: $DEST"
    
    gcloud compute scp --recurse \
        $INSTANCE_NAME:/opt/apt-detection/runs/scenario_results/ \
        $DEST/ \
        --zone=$ZONE || echo "No scenario results found"
    
    gcloud compute scp \
        $INSTANCE_NAME:/opt/apt-detection/runs/cti/seeds.json \
        $DEST/ \
        --zone=$ZONE || echo "No CTI seeds found"
    
    echo -e "${GREEN}✅ Results downloaded to: $DEST${NC}"
    open $DEST
}

start_vm() {
    echo -e "${GREEN}Starting VM...${NC}"
    gcloud compute instances start $INSTANCE_NAME --zone=$ZONE
    echo -e "${GREEN}✅ VM started${NC}"
}

stop_vm() {
    echo -e "${YELLOW}Stopping VM...${NC}"
    gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE
    echo -e "${GREEN}✅ VM stopped${NC}"
}

delete_vm() {
    echo -e "${RED}⚠️  This will permanently delete the VM!${NC}"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" = "yes" ]; then
        gcloud compute instances delete $INSTANCE_NAME --zone=$ZONE
        echo -e "${GREEN}✅ VM deleted${NC}"
    else
        echo "Cancelled"
    fi
}

view_status() {
    echo -e "${GREEN}VM Status:${NC}"
    gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE \
        --format="table(name,zone,machineType,status,networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP)"
}

port_forwarding() {
    echo -e "${GREEN}Setting up port forwarding for Jupyter...${NC}"
    echo "Local port 8888 will forward to VM port 8888"
    echo "After connecting, start Jupyter on VM with:"
    echo "  jupyter notebook --no-browser --port=8888"
    echo
    echo "Connecting..."
    gcloud compute ssh $INSTANCE_NAME --zone=$ZONE -- -L 8888:localhost:8888
}

# Main loop
while true; do
    show_menu
    read -p "Enter choice [0-9]: " choice
    
    case $choice in
        1) create_vm ;;
        2) ssh_vm ;;
        3) upload_code ;;
        4) download_results ;;
        5) start_vm ;;
        6) stop_vm ;;
        7) delete_vm ;;
        8) view_status ;;
        9) port_forwarding ;;
        0) echo "Goodbye!"; exit 0 ;;
        *) echo -e "${RED}Invalid choice${NC}" ;;
    esac
    
    echo
    read -p "Press Enter to continue..."
    clear
done
