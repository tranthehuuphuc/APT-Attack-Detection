#!/bin/bash
################################################################################
# One-Command Deploy to Existing GCP VM
# 
# Usage: bash deploy_to_vm.sh VM_NAME ZONE
# Example: bash deploy_to_vm.sh my-vm asia-southeast1-a
################################################################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 VM_NAME ZONE"
    echo "Example: $0 apt-vm asia-southeast1-a"
    exit 1
fi

VM_NAME=$1
ZONE=$2

echo -e "${BLUE}🚀 Deploying APT Attack Detection to $VM_NAME${NC}"
echo

# Check if we're in repo directory
if [ ! -f "README.md" ]; then
    echo -e "${YELLOW}Error: Not in APT-Attack-Detection directory${NC}"
    exit 1
fi

# Step 1: Compress code
echo -e "${GREEN}[1/4] Compressing code...${NC}"
tar -czf /tmp/apt-code.tar.gz \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.venv' \
    --exclude='runs' \
    .
echo "✅ Code compressed"

# Step 2: Upload
echo -e "${GREEN}[2/4] Uploading to VM...${NC}"
gcloud compute scp /tmp/apt-code.tar.gz $VM_NAME:/tmp/ --zone=$ZONE
rm /tmp/apt-code.tar.gz
echo "✅ Code uploaded"

# Step 3: Extract
echo -e "${GREEN}[3/4] Extracting on VM...${NC}"
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
  sudo mkdir -p /opt/apt-detection && \
  sudo chown \$USER:\$USER /opt/apt-detection && \
  cd /opt/apt-detection && \
  tar -xzf /tmp/apt-code.tar.gz && \
  rm /tmp/apt-code.tar.gz && \
  echo '✅ Code extracted to /opt/apt-detection'
"

# Step 4: Setup (optional - user can do manually)
echo -e "${GREEN}[4/4] Quick setup check...${NC}"
gcloud compute ssh $VM_NAME --zone=$ZONE --command="
  cd /opt/apt-detection && \
  if [ -f .venv/bin/activate ]; then
    echo '✅ Virtual environment already exists'
  else
    echo '⚠️  Virtual environment not found'
    echo 'Run setup: see DEPLOY_TO_EXISTING_VM.md Step 3'
  fi
"

echo
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo
echo "Next steps:"
echo "1. SSH to VM:"
echo "   gcloud compute ssh $VM_NAME --zone=$ZONE"
echo
echo "2. If first time, setup dependencies:"
echo "   cd /opt/apt-detection"
echo "   See DEPLOY_TO_EXISTING_VM.md - Step 3"
echo
echo "3. Run experiments:"
echo "   bash experiments/scenarios/quick_test.sh"
echo
