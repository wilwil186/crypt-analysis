#!/bin/bash

sudo apt-get update
sudo apt-get install -y wget build-essential python3-dev python3-pip

cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
sudo ldconfig

pip3 install --break-system-packages numpy pandas matplotlib plotly mplfinance yfinance TA-Lib

cd ~
rm -rf /tmp/ta-lib*

echo "Instalación completada. Ejecuta: python3 test_talib.py"   