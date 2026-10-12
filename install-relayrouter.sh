#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  RelayRouter AI + Hermes Agent Installer
#
#  Pasang RelayRouter sebagai provider AI di Hermes Agent
#  388+ model tersedia (GPT-5, Claude, Grok, Gemini, DeepSeek, dll)
#
#  Cara pake:
#    curl -fsSL https://raw.githubusercontent.com/akunkhususjualanssh-create/vps-store-bot/main/install-relayrouter.sh -o install-relayrouter.sh && bash install-relayrouter.sh
# ═══════════════════════════════════════════════════════════════

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

RELAY_BASE_URL="https://api.relayrouter.ai/v1"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
HERMES_ENV="$HERMES_HOME/.env"
HERMES_CONFIG="$HERMES_HOME/config.yaml"

clear
echo -e "${CYAN}"
echo "======================================================"
echo "   RelayRouter AI + Hermes Agent Installer"
echo "======================================================"
echo -e "${NC}"

# ─── Check root ───
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Harus root! sudo bash install-relayrouter.sh${NC}"
    exit 1
fi

# ─── Parse argumen ───
ARG_KEY=""
ARG_MODEL=""
for arg in "$@"; do
    case $arg in
        --key=*)   ARG_KEY="${arg#*=}" ;;
        --model=*) ARG_MODEL="${arg#*=}" ;;
    esac
done

# ─── Step 1: Cek/install Hermes ───
echo -e "${CYAN}[1/5] Cek Hermes Agent...${NC}"

if command -v hermes &>/dev/null; then
    echo -e "${GREEN}[OK] Hermes sudah terinstall${NC}"
    HERMES_BIN=$(which hermes)
else
    echo -e "${YELLOW}Hermes belum ada. Installing...${NC}"
    curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
    export PATH="$HOME/.local/bin:$PATH"
    HERMES_BIN="$HOME/.local/bin/hermes"
    if ! command -v hermes &>/dev/null; then
        echo -e "${RED}Gagal install Hermes!${NC}"
        exit 1
    fi
    echo -e "${GREEN}[OK] Hermes terinstalled${NC}"
fi

# ─── Step 2: Input API Key ───
echo -e "${CYAN}[2/5] Konfigurasi API Key...${NC}"

if [ -n "$ARG_KEY" ]; then
    API_KEY="$ARG_KEY"
    echo -e "${GREEN}[OK] API Key dari argumen${NC}"
else
    # Cek apakah sudah ada di .env
    EXISTING_KEY=""
    if [ -f "$HERMES_ENV" ]; then
        EXISTING_KEY=$(grep "RELAYROUTER_API_KEY=" "$HERMES_ENV" 2>/dev/null | cut -d'=' -f2)
    fi

    if [ -n "$EXISTING_KEY" ]; then
        echo -e "${GREEN}[OK] API Key sudah ada di .env${NC}"
        API_KEY="$EXISTING_KEY"
    else
        echo ""
        echo -e "${YELLOW}Masukkan RelayRouter API Key lu:${NC}"
        echo -e "${YELLOW}(dari: console.relayrouter.ai -> API Tokens)${NC}"
        echo ""
        if [ -t 0 ]; then
            READ_FD=0
        else
            READ_FD=/dev/tty
        fi
        echo -ne "API Key (sk-xxx): "
        read -r API_KEY < "$READ_FD" 2>/dev/null || API_KEY=""

        if [ -z "$API_KEY" ]; then
            echo -e "${RED}API Key gak boleh kosong!${NC}"
            exit 1
        fi
    fi
fi

# Simpan ke .env
mkdir -p "$HERMES_HOME"
if [ -f "$HERMES_ENV" ]; then
    # Hapus key lama kalau ada, tambah yang baru
    sed -i '/^RELAYROUTER_API_KEY=/d' "$HERMES_ENV"
fi
echo "RELAYROUTER_API_KEY=$API_KEY" >> "$HERMES_ENV"
echo -e "${GREEN}[OK] API Key disimpan ke .env${NC}"

# ─── Step 3: Test koneksi ───
echo -e "${CYAN}[3/5] Test koneksi RelayRouter...${NC}"

MODELS_RESPONSE=$(curl -s -w "\n%{http_code}" "$RELAY_BASE_URL/models" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" 2>/dev/null)

HTTP_CODE=$(echo "$MODELS_RESPONSE" | tail -1)
BODY=$(echo "$MODELS_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" != "200" ]; then
    echo -e "${RED}Gagal koneksi! HTTP $HTTP_CODE${NC}"
    echo "Response: $BODY"
    echo ""
    echo "Cek API Key lu di console.relayrouter.ai"
    exit 1
fi

MODEL_COUNT=$(echo "$BODY" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('data',[])))" 2>/dev/null || echo "?")
echo -e "${GREEN}[OK] Koneksi berhasil! $MODEL_COUNT model tersedia${NC}"

# ─── Step 4: Pilih model ───
echo -e "${CYAN}[4/5] Pilih Model...${NC}"

if [ -n "$ARG_MODEL" ]; then
    SELECTED_MODEL="$ARG_MODEL"
    echo -e "${GREEN}[OK] Model dari argumen: $SELECTED_MODEL${NC}"
else
    echo ""
    echo -e "${YELLOW}Model populer yang tersedia:${NC}"
    echo ""
    echo "  1) gpt-5-mini          (OpenAI GPT-5 Mini - cepat & murah)"
    echo "  2) claude-sonnet-5     (Anthropic Claude Sonnet 5 - coding jago)"
    echo "  3) claude-opus-5       (Anthropic Claude Opus 5 - paling pintar)"
    echo "  4) grok-4-20-non-reasoning (xAI Grok 4 - cepat)"
    echo "  5) gemini-3.5-flash-lite   (Google Gemini 3.5 Flash)"
    echo "  6) deepseek-v3         (DeepSeek V3 - murah & bagus)"
    echo "  7) kimi-k2.6           (Moonshot Kimi K2.6)"
    echo "  8) glm-4.5             (Zhipu GLM 4.5)"
    echo "  9) qwen-max            (Alibaba Qwen Max)"
    echo " 10) gpt-4o-mini         (OpenAI GPT-4o Mini - murah)"
    echo ""
    echo "  0) Input model sendiri"
    echo ""

    if [ -t 0 ]; then
        READ_FD=0
    else
        READ_FD=/dev/tty
    fi

    echo -ne "Pilih nomor (1-10 atau 0): "
    read -r CHOICE < "$READ_FD" 2>/dev/null || CHOICE="1"

    case $CHOICE in
        1) SELECTED_MODEL="gpt-5-mini" ;;
        2) SELECTED_MODEL="claude-sonnet-5" ;;
        3) SELECTED_MODEL="claude-opus-5" ;;
        4) SELECTED_MODEL="grok-4-20-non-reasoning" ;;
        5) SELECTED_MODEL="gemini-3.5-flash-lite" ;;
        6) SELECTED_MODEL="deepseek-v3" ;;
        7) SELECTED_MODEL="kimi-k2.6" ;;
        8) SELECTED_MODEL="glm-4.5" ;;
        9) SELECTED_MODEL="qwen-max" ;;
        10) SELECTED_MODEL="gpt-4o-mini" ;;
        0)
            echo -ne "Masukkan model ID: "
            read -r SELECTED_MODEL < "$READ_FD" 2>/dev/null || SELECTED_MODEL=""
            if [ -z "$SELECTED_MODEL" ]; then
                echo -e "${RED}Model gak boleh kosong!${NC}"
                exit 1
            fi
            ;;
        *) SELECTED_MODEL="gpt-5-mini" ;;
    esac
    echo -e "${GREEN}[OK] Model dipilih: $SELECTED_MODEL${NC}"
fi

# ─── Step 5: Konfigurasi Hermes ───
echo -e "${CYAN}[5/5] Konfigurasi Hermes...${NC}"

# Set model default ke RelayRouter
$HERMES_BIN config set model.default "$SELECTED_MODEL" 2>/dev/null || true
$HERMES_BIN config set model.provider "custom" 2>/dev/null || true
$HERMES_BIN config set model.base_url "$RELAY_BASE_URL" 2>/dev/null || true
$HERMES_BIN config set model.api_key '${RELAYROUTER_API_KEY}' 2>/dev/null || true

echo -e "${GREEN}[OK] Hermes dikonfigurasi!${NC}"

# ─── Test model ───
echo ""
echo -e "${CYAN}Test model $SELECTED_MODEL...${NC}"

TEST_RESPONSE=$(curl -s "$RELAY_BASE_URL/chat/completions" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"$SELECTED_MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"Halo, jawab dengan 1 kata: OK\"}],\"max_tokens\":10}" 2>/dev/null)

TEST_OK=$(echo "$TEST_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('choices',[{}])[0].get('message',{}).get('content','FAIL'))" 2>/dev/null || echo "FAIL")

if [ "$TEST_OK" != "FAIL" ]; then
    echo -e "${GREEN}[OK] Model merespon: $TEST_OK${NC}"
else
    echo -e "${YELLOW}[!] Model tidak merespon test. Mungkin model ID salah atau gak ada akses.${NC}"
    echo "Response: $TEST_RESPONSE"
fi

# ─── Done ───
echo ""
echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}   INSTALL SELESAI!${NC}"
echo -e "${GREEN}======================================================${NC}"
echo ""
echo "  Provider:  RelayRouter (custom)"
echo "  Base URL:  $RELAY_BASE_URL"
echo "  Model:     $SELECTED_MODEL"
echo "  API Key:   ${API_KEY:0:10}..."
echo "  Models:    $MODEL_COUNT tersedia"
echo ""
echo -e "${YELLOW}Cara pake:${NC}"
echo ""
echo "  Jalankan Hermes:"
echo "    hermes"
echo ""
echo "  Ganti model kapan saja:"
echo "    hermes config set model.default <model_id>"
echo ""
echo "  Lihat semua model tersedia:"
echo "    curl -s $RELAY_BASE_URL/models -H 'Authorization: Bearer \$RELAYROUTER_API_KEY' | python3 -m json.tool"
echo ""
echo -e "${YELLOW}Model populer lain:${NC}"
echo "  gpt-5-mini, claude-sonnet-5, claude-opus-5, grok-4-20,"
echo "  gemini-3.5-flash-lite, deepseek-v3, kimi-k2.6, glm-4.5"
echo ""
echo -e "${GREEN}Gas jalanin: hermes${NC}"
