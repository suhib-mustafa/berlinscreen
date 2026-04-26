#!/usr/bin/env bash
# One-shot installer: registers the BerlinScreen Flask service and the
# Chromium kiosk autostart entry. Idempotent — safe to re-run.
#
# Usage (on the Pi):
#   bash ~/berlinscreen/deploy/install.sh
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
USER_NAME="${SUDO_USER:-$(whoami)}"
HOME_DIR="$(getent passwd "$USER_NAME" | cut -d: -f6)"

echo "==> Installing systemd service"
sudo cp "$DIR/berlinscreen.service" /etc/systemd/system/berlinscreen.service
sudo systemctl daemon-reload
sudo systemctl enable berlinscreen
sudo systemctl restart berlinscreen
echo "    systemctl status berlinscreen   # to verify"

echo "==> Installing kiosk autostart entries"

# XDG autostart — picked up by GNOME, LXDE, Wayfire and most session managers.
mkdir -p "$HOME_DIR/.config/autostart"
cp "$DIR/kiosk.desktop" "$HOME_DIR/.config/autostart/berlinscreen-kiosk.desktop"
chown "$USER_NAME":"$USER_NAME" "$HOME_DIR/.config/autostart/berlinscreen-kiosk.desktop"

# labwc (default Wayland session on recent Bookworm Pi OS) — uses a shell
# script instead of .desktop files.
LABWC_DIR="$HOME_DIR/.config/labwc"
mkdir -p "$LABWC_DIR"
LABWC_AUTOSTART="$LABWC_DIR/autostart"
LINE='(sleep 8; chromium --kiosk --noerrdialogs --disable-infobars --no-first-run --disable-features=TranslateUI --disable-gcm http://localhost:5000) &'
if [ -f "$LABWC_AUTOSTART" ] && grep -qF "berlinscreen" "$LABWC_AUTOSTART" 2>/dev/null; then
  echo "    labwc autostart already references berlinscreen, skipping"
else
  printf '\n# berlinscreen kiosk\n%s\n' "$LINE" >> "$LABWC_AUTOSTART"
  chown "$USER_NAME":"$USER_NAME" "$LABWC_AUTOSTART"
fi

# LXDE-pi fallback (older Pi OS desktop). Only added if directory exists.
LX_DIR="$HOME_DIR/.config/lxsession/LXDE-pi"
if [ -d "$LX_DIR" ]; then
  LX_AUTOSTART="$LX_DIR/autostart"
  if [ -f "$LX_AUTOSTART" ] && grep -qF "berlinscreen" "$LX_AUTOSTART" 2>/dev/null; then
    echo "    LXDE-pi autostart already references berlinscreen, skipping"
  else
    printf '@bash -c "sleep 8 && chromium --kiosk --noerrdialogs --disable-infobars --no-first-run http://localhost:5000"\n' >> "$LX_AUTOSTART"
    chown "$USER_NAME":"$USER_NAME" "$LX_AUTOSTART"
  fi
fi

echo
echo "Done. Reboot to verify:"
echo "  sudo reboot"
echo
echo "After reboot, the dashboard should be live at http://localhost:5000 and"
echo "Chromium should open it fullscreen on the connected display within ~30s."
