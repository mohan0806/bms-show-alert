#!/data/data/com.termux/files/usr/bin/bash
# One-time setup for BMS Show Alert on Android (Termux).
# Run from inside the bms-show-alert folder:   bash setup_termux.sh
set -e

echo "== 1/4 Updating Termux packages (this can take a few minutes)"
apt update
apt full-upgrade -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold"

echo "== 2/4 Installing Python, Termux:API tools and git"
pkg install -y python termux-api git nano

echo "== 3/4 Installing Chromium (large download, please wait)"
pkg install -y x11-repo
pkg install -y chromium

echo "== 4/4 Creating your settings file"
if [ ! -f config.env ]; then
  cp config.example.env config.env
  echo "Created config.env. Edit it next with:  nano config.env"
else
  echo "config.env already exists, left unchanged."
fi

echo
echo "Setup done. Next steps:"
echo "  nano config.env              # fill in your movie, cinema, date and Telegram details"
echo "  python bms_watch.py --list   # check the movie / language / format names"
echo "  python bms_watch.py --test   # test Telegram + alarm"
echo "  python bms_watch.py          # start watching"
