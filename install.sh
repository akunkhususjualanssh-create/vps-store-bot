#!/bin/bash
# GEN SSH STORE - VPS Store Bot Installer
#
# CARA INSTALL (PILIH SALAH SATU):
#
# CARA 1 (RECOMMENDED):
#   curl -fsSL https://raw.githubusercontent.com/akunkhususjualanssh-create/vps-store-bot/main/install.sh -o install.sh && bash install.sh
#
# CARA 2 (token via argumen):
#   curl -fsSL https://raw.githubusercontent.com/akunkhususjualanssh-create/vps-store-bot/main/install.sh -o install.sh && bash install.sh --token=TOKEN --owner=ID
#
# CARA 3 (manual):
#   git clone https://github.com/akunkhususjualanssh-create/vps-store-bot.git && cd vps-store-bot && bash install.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${CYAN}"
echo "======================================================"
echo "   GEN SSH STORE - VPS Store Bot Installer"
echo "======================================================"
echo -e "${NC}"

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Harus root! sudo bash install.sh${NC}"
    exit 1
fi

INSTALL_DIR="/opt/vps-store-bot"

# Parse argumen
ARG_TOKEN=""
ARG_OWNER=""
for arg in "$@"; do
    case $arg in
        --token=*)  ARG_TOKEN="${arg#*=}" ;;
        --owner=*)  ARG_OWNER="${arg#*=}" ;;
    esac
done

# [1/6] Update system
echo -e "${CYAN}[1/6] Updating system...${NC}"
apt update -qq 2>/dev/null
apt install -y -qq python3 python3-pip python3-venv git curl 2>/dev/null
echo -e "${GREEN}[OK] System updated${NC}"

# [2/6] Download dari GitHub
echo -e "${CYAN}[2/6] Downloading from GitHub...${NC}"
rm -rf /tmp/vps-store-bot
git clone -q https://github.com/akunkhususjualanssh-create/vps-store-bot.git /tmp/vps-store-bot
echo -e "${GREEN}[OK] Downloaded${NC}"

# [3/6] Setup directory
echo -e "${CYAN}[3/6] Setting up directory...${NC}"
mkdir -p $INSTALL_DIR/database $INSTALL_DIR/assets $INSTALL_DIR/logs
cp -r /tmp/vps-store-bot/* $INSTALL_DIR/ 2>/dev/null || true
rm -rf /tmp/vps-store-bot
echo -e "${GREEN}[OK] Directory: $INSTALL_DIR${NC}"

# [4/6] Install dependencies
echo -e "${CYAN}[4/6] Installing Python dependencies...${NC}"
cd $INSTALL_DIR
python3 -m venv venv
./venv/bin/pip install -q python-telegram-bot python-dotenv 2>&1 | tail -1
echo -e "${GREEN}[OK] Dependencies installed${NC}"

# [5/6] Input token & owner ID
echo -e "${CYAN}[5/6] Konfigurasi Bot${NC}"

if [ -n "$ARG_TOKEN" ] && [ -n "$ARG_OWNER" ]; then
    BOT_TOKEN="$ARG_TOKEN"
    OWNER_ID="$ARG_OWNER"
    echo -e "${GREEN}[OK] Token & Owner dari argumen${NC}"
else
    DEFAULT_TOKEN=""
    DEFAULT_OWNER=""
    if [ -f "$INSTALL_DIR/.env" ]; then
        source "$INSTALL_DIR/.env" 2>/dev/null
        DEFAULT_TOKEN="${BOT_TOKEN:-}"
        DEFAULT_OWNER="${OWNER_ID:-}"
    fi

    echo ""
    echo -e "${YELLOW}Masukkan data bot lu:${NC}"
    echo ""

    if [ -t 0 ]; then
        READ_FD=0
    else
        READ_FD=/dev/tty
    fi

    if [ -n "$DEFAULT_TOKEN" ]; then
        echo -ne "Bot Token [enter=akhir lama]: "
    else
        echo -ne "Bot Token: "
    fi
    read -r INPUT_TOKEN < "$READ_FD" 2>/dev/null || INPUT_TOKEN=""
    BOT_TOKEN="${INPUT_TOKEN:-$DEFAULT_TOKEN}"

    if [ -z "$BOT_TOKEN" ]; then
        echo -e "${RED}Token gak boleh kosong!${NC}"
        exit 1
    fi

    if [ -n "$DEFAULT_OWNER" ]; then
        echo -ne "Owner ID [enter=akhir lama]: "
    else
        echo -ne "Owner ID: "
    fi
    read -r INPUT_OWNER < "$READ_FD" 2>/dev/null || INPUT_OWNER=""
    OWNER_ID="${INPUT_OWNER:-$DEFAULT_OWNER}"

    if [ -z "$OWNER_ID" ]; then
        echo -e "${RED}Owner ID gak boleh kosong!${NC}"
        exit 1
    fi
fi

cat > "$INSTALL_DIR/.env" << EOF
BOT_TOKEN=$BOT_TOKEN
OWNER_ID=$OWNER_ID
DB_PATH=database/vps_store.db
QRIS_DIR=assets
EOF

echo -e "${GREEN}[OK] Config disimpan${NC}"

# [6/6] Start bot
echo -e "${CYAN}[6/6] Starting bot...${NC}"

pkill -f "venv/bin/python bot.py" 2>/dev/null || true
sleep 2

$INSTALL_DIR/venv/bin/python -m py_compile $INSTALL_DIR/bot.py $INSTALL_DIR/config.py $INSTALL_DIR/database.py
echo -e "${GREEN}[OK] Syntax OK${NC}"

# Helper scripts
cat > $INSTALL_DIR/start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
pkill -f "venv/bin/python bot.py" 2>/dev/null
sleep 2
nohup ./venv/bin/python bot.py > logs/bot.log 2>&1 &
echo $! > bot.pid
echo "Bot started. PID: $(cat bot.pid)"
EOF

cat > $INSTALL_DIR/stop.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
pkill -f "venv/bin/python bot.py" 2>/dev/null
if [ -f bot.pid ]; then
    kill $(cat bot.pid) 2>/dev/null
    rm -f bot.pid
fi
echo "Bot stopped."
EOF

cat > $INSTALL_DIR/restart.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "Stopping..."
pkill -f "venv/bin/python bot.py" 2>/dev/null
sleep 2
echo "Starting..."
nohup ./venv/bin/python bot.py > logs/bot.log 2>&1 &
echo $! > bot.pid
echo "Bot restarted. PID: $(cat bot.pid)"
EOF

cat > $INSTALL_DIR/logs.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
tail -50 logs/bot.log
EOF

cat > $INSTALL_DIR/status.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
if pgrep -f "venv/bin/python bot.py" > /dev/null; then
    echo "Bot: RUNNING (PID: $(pgrep -f 'venv/bin/python bot.py'))"
else
    echo "Bot: NOT RUNNING"
    echo "Start: ./start.sh"
fi
EOF

chmod +x $INSTALL_DIR/*.sh

# Start
cd $INSTALL_DIR
nohup ./venv/bin/python bot.py > logs/bot.log 2>&1 &
echo $! > bot.pid
sleep 4

if pgrep -f "venv/bin/python bot.py" > /dev/null; then
    echo -e "${GREEN}[OK] Bot jalan! PID: $(cat bot.pid)${NC}"
else
    echo -e "${RED}[!] Bot gagal start. Cek log:${NC}"
    tail -5 logs/bot.log
fi

echo ""
echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}   INSTALL SELESAI!${NC}"
echo -e "${GREEN}======================================================${NC}"
echo ""
echo "  Dir: $INSTALL_DIR"
echo "  Token: ${BOT_TOKEN:0:15}..."
echo "  Owner: $OWNER_ID"
echo ""
echo -e "${YELLOW}COMMANDS:${NC}"
echo "  Start:   $INSTALL_DIR/start.sh"
echo "  Stop:    $INSTALL_DIR/stop.sh"
echo "  Restart: $INSTALL_DIR/restart.sh"
echo "  Logs:    $INSTALL_DIR/logs.sh"
echo "  Status:  $INSTALL_DIR/status.sh"
echo ""
echo -e "${GREEN}Buka bot di Telegram, ketik /start${NC}"
