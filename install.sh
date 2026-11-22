#!/usr/bin/env bash
# =============================================================================
#  OCC · Instalador único del laboratorio (M2.12 · M2.14 · M2.15)
#  Operational Cyberintelligence Certificate
#
#  Uso (en la VM de Kali del alumno):
#     curl -fsSL https://raw.githubusercontent.com/kanjid/occ/main/install.sh | bash
#
#  Qué hace:
#    1. Comprueba el sistema (Debian/Kali) y la conexión.
#    2. Instala Docker + Docker Compose si faltan.
#    3. Clona/actualiza este repositorio en ~/occ.
#    4. Prepara un entorno Python (venv) para los scripts de M2.12 y M2.14.
#    5. Clona Watcher (fijado a una versión) y lo deja levantado y funcionando.
#    6. Crea un usuario administrador por defecto y siembra los feeds RSS.
#
#  Es idempotente: se puede relanzar sin romper nada.
# =============================================================================

set -Eeuo pipefail

# ----------------------------- Parámetros -----------------------------------
OCC_REPO_URL="https://github.com/kanjid/occ.git"
OCC_DIR="${OCC_DIR:-$HOME/occ}"

WATCHER_REPO_URL="https://github.com/thalesgroup-cert/watcher.git"
WATCHER_REF="${WATCHER_REF:-v3.7.0}"              # tag del repo de Watcher
WATCHER_IMAGE_VERSION="${WATCHER_IMAGE_VERSION:-v3.7.0}"  # tag de la imagen
WATCHER_DIR="$OCC_DIR/m215_cti/watcher"
WATCHER_PORT="9002"

# Credenciales por defecto del panel (cámbialas tras la primera entrada)
ADMIN_USER="${ADMIN_USER:-alumno}"
ADMIN_EMAIL="${ADMIN_EMAIL:-alumno@occ.local}"
ADMIN_PASS="${ADMIN_PASS:-OccWatcher2026!}"

# ----------------------------- Utilidades -----------------------------------
c_blue=$'\033[1;34m'; c_green=$'\033[1;32m'; c_yellow=$'\033[1;33m'
c_red=$'\033[1;31m';  c_reset=$'\033[0m'
step() { echo; echo "${c_blue}==>${c_reset} ${c_blue}$*${c_reset}"; }
ok()   { echo "    ${c_green}✓${c_reset} $*"; }
warn() { echo "    ${c_yellow}!${c_reset} $*"; }
die()  { echo; echo "${c_red}ERROR:${c_reset} $*" >&2; exit 1; }

trap 'die "Ha fallado el paso anterior (línea $LINENO). Revisa el mensaje de arriba."' ERR

# sudo solo si no somos root
if [ "$(id -u)" -eq 0 ]; then SUDO=""; else SUDO="sudo"; fi

# apt SIEMPRE en modo no interactivo. Usamos 'env' porque sudo no hereda
# las variables de entorno del shell (por eso debconf preguntaba por pantalla).
APT="$SUDO env DEBIAN_FRONTEND=noninteractive apt-get"

# -------------------------- 1. Comprobaciones -------------------------------
step "1/6 · Comprobando el sistema"

[ "$(uname -s)" = "Linux" ] || die "Este instalador es para Linux (Kali)."

if [ -r /etc/os-release ]; then
    . /etc/os-release
    case "${ID:-}:${ID_LIKE:-}" in
        *debian*|*kali*) ok "Distribución compatible: ${PRETTY_NAME:-$ID}";;
        *) warn "Distribución no probada (${PRETTY_NAME:-desconocida}); continúo igualmente.";;
    esac
fi

if [ -n "$SUDO" ]; then
    command -v sudo >/dev/null 2>&1 || die "Necesitas 'sudo' o ejecutar como root."
    sudo -n true 2>/dev/null || warn "Se te pedirá la contraseña de sudo durante la instalación."
fi

step "Comprobando la conexión a internet"
if command -v curl >/dev/null 2>&1; then
    curl -fsS --max-time 10 https://github.com >/dev/null 2>&1 \
        && ok "Hay salida a internet." \
        || die "Sin acceso a internet (github.com). La VM necesita red para instalarse."
else
    $APT update -qq && $APT install -y -qq curl \
        || die "No se pudo instalar 'curl'."
fi

# Paquetes base
step "Instalando utilidades base (git, curl, python3-venv)"
# Limpia un repositorio de Docker roto que pudiera haber dejado un intento
# anterior: get.docker.com añade 'kali-rolling', que Docker NO publica y
# hace fallar 'apt-get update'. En Kali usamos docker.io de sus propios repos.
if [ -f /etc/apt/sources.list.d/docker.list ] \
   && grep -q 'download.docker.com' /etc/apt/sources.list.d/docker.list 2>/dev/null; then
    $SUDO rm -f /etc/apt/sources.list.d/docker.list
    warn "Eliminado un repositorio de Docker incompatible de un intento previo."
fi
$APT update -qq
$APT install -y -qq git curl ca-certificates python3 python3-venv python3-pip openssl
ok "Utilidades base listas."

# -------------------------- 2. Docker ---------------------------------------
step "2/6 · Docker y Docker Compose"

# En Kali, Docker se instala desde sus propios repositorios (docker.io):
# el script oficial get.docker.com NO soporta 'kali-rolling' y falla.
if ! command -v docker >/dev/null 2>&1; then
    warn "Docker no está instalado. Instalando desde los repositorios de Kali..."
    if $APT install -y -qq docker.io; then
        ok "Docker instalado (docker.io)."
    else
        warn "No pude instalar 'docker.io'; probando el script oficial de Docker..."
        curl -fsSL https://get.docker.com | $SUDO sh
        ok "Docker instalado."
    fi
else
    ok "Docker ya está instalado."
fi

# Plugin de compose v2 (el subcomando 'docker compose').
# En Kali no existe el paquete apt, así que instalamos el plugin oficial de Docker.
if docker compose version >/dev/null 2>&1; then
    ok "Docker Compose disponible."
else
    warn "Instalando el plugin oficial 'docker compose'..."
    CLI_DIR="/usr/local/lib/docker/cli-plugins"
    $SUDO mkdir -p "$CLI_DIR"
    $SUDO curl -fsSL \
        "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
        -o "$CLI_DIR/docker-compose"
    $SUDO chmod +x "$CLI_DIR/docker-compose"
    if docker compose version >/dev/null 2>&1; then
        ok "Docker Compose disponible."
    else
        die "No se pudo habilitar 'docker compose'."
    fi
fi

# Arrancar el demonio
step "Arrancando el servicio de Docker"
$SUDO systemctl enable --now docker >/dev/null 2>&1 \
    || $SUDO service docker start >/dev/null 2>&1 \
    || warn "No pude gestionar el servicio por systemd/service; quizá ya esté en marcha."

# Grupo docker (para no necesitar sudo con docker)
if [ -n "$SUDO" ] && ! id -nG "$USER" 2>/dev/null | grep -qw docker; then
    $SUDO usermod -aG docker "$USER" || true
    warn "Te he añadido al grupo 'docker'. En esta instalación lo gestiono por ti;"
    warn "para usar 'docker' sin sudo en el futuro, cierra y abre sesión una vez."
fi

# Cómo ejecutaremos docker/make: directo, vía 'sg docker', o con sudo
if docker info >/dev/null 2>&1; then
    RUNMODE="direct"
elif sg docker -c 'docker info >/dev/null 2>&1' >/dev/null 2>&1; then
    RUNMODE="sg"
else
    RUNMODE="sudo"
fi
run() {  # run "<comando de shell>"
    case "$RUNMODE" in
        direct) bash -lc "$1" ;;
        sg)     sg docker -c "$1" ;;
        sudo)   $SUDO bash -lc "$1" ;;
    esac
}
ok "Docker operativo (modo de ejecución: $RUNMODE)."

# -------------------------- 3. Repositorio OCC ------------------------------
step "3/6 · Repositorio OCC en $OCC_DIR"

if [ -d "$OCC_DIR/.git" ]; then
    ok "Ya existe; actualizando (git pull)."
    git -C "$OCC_DIR" pull --ff-only || warn "No pude actualizar; sigo con lo que hay."
elif [ -e "$OCC_DIR" ]; then
    warn "$OCC_DIR existe pero no es un clon git; lo uso tal cual."
else
    git clone --depth 1 "$OCC_REPO_URL" "$OCC_DIR"
    ok "Repositorio clonado."
fi

# -------------------------- 4. Entorno Python -------------------------------
step "4/6 · Entorno Python para M2.12 y M2.14"

if [ ! -d "$OCC_DIR/.venv" ]; then
    python3 -m venv "$OCC_DIR/.venv"
    ok "Entorno virtual creado en ~/occ/.venv"
fi
"$OCC_DIR/.venv/bin/pip" install -q --upgrade pip
if [ -f "$OCC_DIR/requirements.txt" ]; then
    "$OCC_DIR/.venv/bin/pip" install -q -r "$OCC_DIR/requirements.txt"
    ok "Dependencias de Python instaladas (Telethon, pandas, matplotlib…)."
else
    warn "No encuentro requirements.txt; me salto las dependencias de Python."
fi

# -------------------------- 5. Watcher (M2.15) ------------------------------
step "5/6 · Watcher (clonando versión $WATCHER_REF)"

mkdir -p "$OCC_DIR/m215_cti"
if [ -d "$WATCHER_DIR/.git" ]; then
    ok "Watcher ya está clonado."
else
    git clone --depth 1 --branch "$WATCHER_REF" "$WATCHER_REPO_URL" "$WATCHER_DIR"
    ok "Watcher $WATCHER_REF clonado."
fi

DEP="$WATCHER_DIR/deployment"
[ -d "$DEP" ] || die "No encuentro el directorio de despliegue de Watcher."
# Los scripts del Makefile de Watcher vienen sin permiso de ejecución en el
# repositorio; se lo damos para que 'make down/up' funcionen más adelante.
chmod +x "$DEP"/scripts/*.sh 2>/dev/null || true

# Preparar .env (solo la primera vez, para no pisar secretos ya generados)
if [ ! -f "$DEP/.env" ]; then
    cp "$DEP/.env.example" "$DEP/.env"
    SECRET="$(openssl rand -hex 32)"
    DBPASS="$(openssl rand -hex 12)"
    DBROOT="$(openssl rand -hex 12)"
    # Ajustes para uso local en el aula
    sed -i \
        -e "s|^WATCHER_VERSION=.*|WATCHER_VERSION=${WATCHER_IMAGE_VERSION}|" \
        -e "s|^WATCHER_PORT=.*|WATCHER_PORT=${WATCHER_PORT}|" \
        -e "s|^DOMAIN_CORP=.*|DOMAIN_CORP=localhost|" \
        -e "s|^DJANGO_SECRET_KEY=.*|DJANGO_SECRET_KEY=${SECRET}|" \
        -e "s|^DB_PASSWORD=.*|DB_PASSWORD=\"${DBPASS}\"|" \
        -e "s|^DB_ROOT_PASSWORD=.*|DB_ROOT_PASSWORD=\"${DBROOT}\"|" \
        "$DEP/.env"
    ok "Configuración (.env) generada con secretos propios de esta VM."
else
    ok "Configuración (.env) ya existente; la respeto."
fi

# Intento fijar la imagen a la versión; si no existe, caigo a 'latest'
step "Descargando la imagen de Watcher"
if ! run "docker pull ghcr.io/thalesgroup-cert/watcher:${WATCHER_IMAGE_VERSION}" >/dev/null 2>&1; then
    warn "No encontré la imagen ${WATCHER_IMAGE_VERSION}; uso 'latest'."
    sed -i "s|^WATCHER_VERSION=.*|WATCHER_VERSION=latest|" "$DEP/.env"
fi
ok "Imagen lista."

step "Inicializando y levantando Watcher (esto tarda un poco la primera vez)"
run "cd '$DEP' && make init"
# 'make up' puede devolver error si MySQL tarda en inicializar: el contenedor
# 'watcher' no arranca hasta que la BD pasa su healthcheck, y el PRIMER arranque
# de MySQL puede superar ese margen. No es fatal: esperamos a la BD y reintentamos.
run "cd '$DEP' && make up" || warn "Arranque parcial (la BD aún inicializa); espero y reintento."

# Esperar a que MySQL esté SANO. Migrar antes de que la BD esté lista deja el
# esquema a medias (origen de los fallos). El primer arranque puede tardar 1-2 min.
step "Esperando a que la base de datos esté lista (su primer arranque tarda)"
DB_OK=0
for _ in $(seq 1 60); do   # hasta ~5 min
    if run "cd '$DEP' && docker compose ps db_watcher" 2>/dev/null | grep -q healthy; then
        DB_OK=1; break
    fi
    sleep 5
done
[ "$DB_OK" -eq 1 ] && ok "Base de datos lista." || warn "La BD tardó mucho; continúo igualmente."

# Reintento idempotente: ahora que la BD está sana, arranca 'watcher' si 'make up'
# no llegó a hacerlo por el race anterior.
run "cd '$DEP' && docker compose up -d" >/dev/null 2>&1 || true

# Esperar a que el contenedor de la aplicación esté en marcha.
step "Esperando a que la aplicación arranque"
for _ in $(seq 1 30); do
    run "cd '$DEP' && docker compose ps --status running" 2>/dev/null | grep -q '\bwatcher\b' && break
    sleep 5
done
sleep 5

# Migraciones: exec directo (los scripts del Makefile no traen permiso +x). Sobre
# una BD limpia se aplican completas. Pueden aparecer trazas de tareas internas
# que se disparan mientras se crean las tablas: son inofensivas.
step "Aplicando migraciones de la base de datos"
run "cd '$DEP' && docker compose exec -T watcher python manage.py migrate --no-input" \
    && ok "Base de datos migrada." \
    || warn "La migración devolvió un aviso; revisa la salida de arriba."

# Usuario administrador: por el shell de Django, rellenando 'last_login'
# explícitamente para evitar el error 'last_login cannot be null'.
step "Creando el usuario administrador por defecto"
PY="from django.contrib.auth import get_user_model; from django.utils import timezone; U=get_user_model(); U.objects.filter(username='${ADMIN_USER}').delete(); u=U(username='${ADMIN_USER}', email='${ADMIN_EMAIL}', is_staff=True, is_superuser=True, is_active=True, last_login=timezone.now()); u.set_password('${ADMIN_PASS}'); u.save(); print('SUPERUSER_OK')"
if run "cd '$DEP' && docker compose exec -T watcher python manage.py shell -c \"$PY\"" 2>/dev/null | grep -q 'SUPERUSER_OK'; then
    ok "Usuario '$ADMIN_USER' listo."
else
    warn "No pude crear el usuario automáticamente; créalo luego (ver README)."
fi

# Poblar la base de datos (incluye 218 fuentes RSS, con varios CERT).
step "Sembrando fuentes RSS y datos iniciales (Práctica 3 lista)"
run "cd '$DEP' && docker compose exec -T watcher python manage.py populate_db" >/dev/null 2>&1 \
    && ok "Fuentes RSS cargadas (CERT-FR, US-CERT/CISA, INCIBE-CERT, CCN-CERT…)." \
    || warn "No pude ejecutar populate_db ahora; puedes relanzar el instalador."

# -------------------------- 6. Resumen --------------------------------------
cat <<RESUMEN

${c_green}============================================================${c_reset}
${c_green}  INSTALACIÓN COMPLETADA${c_reset}
${c_green}============================================================${c_reset}

  ${c_blue}Watcher (M2.15):${c_reset}  http://localhost:${WATCHER_PORT}
      Usuario:   ${ADMIN_USER}
      Password:  ${ADMIN_PASS}   ${c_yellow}(cámbialo tras entrar)${c_reset}

  ${c_blue}Scripts (M2.12 / M2.14):${c_reset}  ${OCC_DIR}
      Activa el entorno Python con:
          source ~/occ/.venv/bin/activate

  ${c_blue}Gestión de Watcher${c_reset} (desde ${WATCHER_DIR}/deployment):
          make down      # parar
          make up        # arrancar

  Si 'docker' te pide permisos en el futuro, cierra sesión y
  vuelve a entrar una vez (para activar el grupo 'docker').

${c_green}============================================================${c_reset}
RESUMEN