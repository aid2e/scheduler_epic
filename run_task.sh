# SOURCING
echo "SOURCING SETUP NOW!!!"
setup_path=${1:-/opt/detector/setup.sh}
source $setup_path
echo "RUNNNING DD_WEB_DISPLAY NOW!!!!!"
dd_web_display -o epic_output.root --export ${DETECTOR_PATH}/${DETECTOR}.xml -k

python run_task.py