# GEN SSH STORE - VPS Store Bot

Bot Telegram jualan VPS dengan payment manual QRIS.

## Install 1-Klik

```bash
curl -fsSL https://raw.githubusercontent.com/akunkhususjualanssh-create/vps-store-bot/main/install.sh | bash
```

Saat install, bot akan minta:
- Bot Token (dari @BotFather)
- Owner ID (Telegram ID lu)

## Command

```bash
Start:   /opt/vps-store-bot/start.sh
Stop:    /opt/vps-store-bot/stop.sh
Restart: /opt/vps-store-bot/restart.sh
Logs:    /opt/vps-store-bot/logs.sh
Status:  /opt/vps-store-bot/status.sh
```

## Fix Error

### Bot tidak respon?
```bash
/opt/vps-store-bot/status.sh
/opt/vps-store-bot/restart.sh
/opt/vps-store-bot/logs.sh
```

### 409 Conflict?
```bash
pkill -f "python bot.py"
sleep 3
/opt/vps-store-bot/start.sh
```

### Pindah VPS baru?
1. MENU OWNER → BACKUP DB → simpan file
2. Install di VPS baru: bash install.sh
3. MENU OWNER → RESTORE DB → kirim file backup
4. Restart: /opt/vps-store-bot/restart.sh
