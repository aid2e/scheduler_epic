# SOURCING
echo "SOURCING SETUP NOW!!!"
source /sciclone/home/hnayak/scheduler/epic/install/setup.sh
echo "RUNNNING DD_WEB_DISPLAY NOW!!!!!"
dd_web_display -o epic_output.root --export /sciclone/home/hnayak/scheduler/epic/build/epic_full.xml -k