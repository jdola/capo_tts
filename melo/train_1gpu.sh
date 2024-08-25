CONFIG=$1
GPUS=$2
MODEL_NAME=$(basename "$(dirname $CONFIG)")

python train.py --c $CONFIG --model $MODEL_NAME 