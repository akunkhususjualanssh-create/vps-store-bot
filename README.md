# GEN SSH STORE - VPS Store Bot

Bot Telegram jualan VPS dengan payment manual QRIS.

## Install (Pilih 1 dari 3 cara)

### Cara 1 (RECOMMENDED)
```bash
curl -fsSL https://raw.githubusercontent.com/akunkhususjualanssh-create/vps-store-bot/main/install.sh -o install.sh && bash install.sh
```

### Cara 2 (Token via argumen, gak perlu ketik)
```bash
curl -fsSL https://raw.githubusercontent.com/akunkhususjualanssh-create/vps-store-bot/main/install.sh -o install.sh && bash install.sh --token=TOKEN_LU --owner=ID_LU
```

### Cara 3 (Manual)
```bash
git clone https://github.com/akunkhususjualanssh-create/vps-store-bot.git
cd vps-store-bot && bash install.sh
```

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
1. MENU OWNER -> BACKUP DB -> simpan file
2. Install di VPS baru (Cara 1 di atas)
3. MENU OWNER -> RESTORE DB -> kirim file backup
4. Restart: /opt/vps-store-bot/restart.sh
