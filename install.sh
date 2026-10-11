#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  GEN SSH STORE - VPS Store Bot Installer
#  Install 1-klik: tinggal jalankan, masukin token, bot langsung jalan
#
#  Cara pake:
#    bash install.sh
#
#  Atau install langsung dari GitHub:
#    curl -fsSL https://raw.githubusercontent.com/akunkhususjualanssh-create/vps-store-bot/main/install.sh | bash
# ═══════════════════════════════════════════════════════════════

set -e

# ─── Fix: kalau di-pipe (curl | bash), re-download & run dari file ───
# Supaya read (input token) bisa jalan normal
if [ ! -t 0 ]; then
    curl -fsSL "https://raw.githubusercontent.com/akunkhususjualanssh-create/vps-store-bot/main/install.sh" -o /tmp/vps_install.sh
    exec bash /tmp/vps_install.sh </dev/tty
fi

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║   GEN SSH STORE - VPS Store Bot Installer                    ║"
echo "║   Install 1-klik: masukin token, bot jalan                   ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ─── Check root ───
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Harus jalankan sebagai root!${NC}"
    echo "Usage: sudo bash install.sh"
    exit 1
fi

INSTALL_DIR="/opt/vps-store-bot"

# ─── Step 1: Update system ───
echo -e "${CYAN}[1/6] Updating system...${NC}"
apt update -qq && apt install -y -qq python3 python3-pip python3-venv git curl 2>/dev/null
echo -e "${GREEN}✅ System updated!${NC}"

# ─── Step 2: Download from GitHub ───
echo -e "${CYAN}[2/6] Downloading bot from GitHub...${NC}"
rm -rf /tmp/vps-store-bot
git clone -q https://github.com/akunkhususjualanssh-create/vps-store-bot.git /tmp/vps-store-bot
echo -e "${GREEN}✅ Downloaded!${NC}"

# ─── Step 3: Setup directory ───
echo -e "${CYAN}[3/6] Setting up directory...${NC}"
mkdir -p $INSTALL_DIR/database $INSTALL_DIR/assets $INSTALL_DIR/logs
cp -r /tmp/vps-store-bot/* $INSTALL_DIR/ 2>/dev/null || true
rm -rf /tmp/vps-store-bot
echo -e "${GREEN}✅ Directory ready: $INSTALL_DIR${NC}"

# ─── Step 4: Install Python dependencies ───
echo -e "${CYAN}[4/6] Installing Python dependencies...${NC}"
cd $INSTALL_DIR
python3 -m venv venv
./venv/bin/pip install -q python-telegram-bot python-dotenv 2>&1 | tail -1
echo -e "${GREEN}✅ Dependencies installed!${NC}"

# ─── Step 5: Input bot token & owner ID ───
echo -e "${CYAN}[5/6] Konfigurasi Bot${NC}"
echo ""
echo -e "${YELLOW}Silakan masukkan data bot lu:${NC}"
echo ""

# Cek apakah .env sudah ada
if [ -f "$INSTALL_DIR/.env" ]; then
    source $INSTALL_DIR/.env
    DEFAULT_TOKEN="${BOT_TOKEN:-}"
    DEFAULT_OWNER="${OWNER_ID:-}"
else
    DEFAULT_TOKEN=""
    DEFAULT_OWNER=""
fi

read -p "Bot Token: " BOT_TOKEN
BOT_TOKEN=${BOT_TOKEN:-$DEFAULT_TOKEN}

read -p "Owner ID (Telegram ID lu): " OWNER_ID
OWNER_ID=${OWNER_ID:-$DEFAULT_OWNER}

# Simpan .env
cat > $INSTALL_DIR/.env << EOF
BOT_TOKEN=$BOT_TOKEN
OWNER_ID=$OWNER_ID
DB_PATH=database/vps_store.db
QRIS_DIR=assets
EOF

echo -e "${GREEN}✅ Konfigurasi disimpan!${NC}"

# ─── Step 6: Start bot ───
echo -e "${CYAN}[6/6] Starting bot...${NC}"

# Kill bot lama kalau ada
pkill -f "venv/bin/python bot.py" 2>/dev/null || true
sleep 2

# Test syntax
$INSTALL_DIR/venv/bin/python -m py_compile $INSTALL_DIR/bot.py $INSTALL_DIR/config.py $INSTALL_DIR/database.py
echo -e "${GREEN}✅ Syntax OK!${NC}"

# Coba systemd, kalau gak ada fallback ke nohup
if command -v systemctl &>/dev/null && [ -f /run/systemd/system ]; then
    cat > /etc/systemd/system/vps-store-bot.service << EOF
[Unit]
Description=VPS Store Bot - GEN SSH STORE
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/python bot.py
Restart=always
RestartSec=5
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF
    systemctl daemon-reload
    systemctl enable vps-store-bot
    systemctl start vps-store-bot
    sleep 3
    STATUS=$(systemctl is-active vps-store-bot)
    echo -e "${GREEN}✅ Bot started via systemd (status: $STATUS)${NC}"
else
    # Fallback: nohup
    cd $INSTALL_DIR
    nohup ./venv/bin/python bot.py > logs/bot.log 2>&1 &
    echo $! > $INSTALL_DIR/bot.pid
    sleep 3
    echo -e "${GREEN}✅ Bot started via nohup (PID: $(cat $INSTALL_DIR/bot.pid))${NC}"
fi

# ─── Buat helper scripts ───
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
echo "Stopping bot..."
pkill -f "venv/bin/python bot.py" 2>/dev/null
sleep 2
echo "Starting bot..."
nohup ./venv/bin/python bot.py > logs/bot.log 2>&1 &
echo $! > bot.pid
echo "Bot restarted. PID: $(cat bot.pid)"
echo "Cek log: ./logs.sh"
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

# ─── Done ───
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅ INSTALLATION COMPLETE!                                  ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Install dir:${NC} $INSTALL_DIR"
echo -e "${CYAN}Bot Token:${NC} ${BOT_TOKEN:0:15}..."
echo -e "${CYAN}Owner ID:${NC} $OWNER_ID"
echo ""
echo -e "${YELLOW}COMMANDS:${NC}"
echo ""
echo "  Start:    $INSTALL_DIR/start.sh"
echo "  Stop:     $INSTALL_DIR/stop.sh"
echo "  Restart:  $INSTALL_DIR/restart.sh"
echo "  Logs:     $INSTALL_DIR/logs.sh"
echo "  Status:   $INSTALL_DIR/status.sh"
echo ""
echo -e "${YELLOW}FIX ERROR & RESTART:${NC}"
echo ""
echo "  Kalau bot error/crash:"
echo "    1. Restart:  $INSTALL_DIR/restart.sh"
echo "    2. Cek log:  $INSTALL_DIR/logs.sh"
echo "    3. Stop:     $INSTALL_DIR/stop.sh"
echo "    4. Start:    $INSTALL_DIR/start.sh"
echo ""
echo -e "${GREEN}Buka bot lu di Telegram dan ketik /start${NC}"
echo ""
