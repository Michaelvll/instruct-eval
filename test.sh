#for model_name in llama-7b alpaca-7b vicuna-7b-abl-all vicuna-7b-abl-gpt4 vicuna-7b-abl-single; do
for model_name in llama-13b alpaca-13b vicuna-13b-v1.2-b128l2 vicuna-13b-v1.2-gpt4-only vicuna-7b-abl-selected-cp329 vicuna-7b-abl-selected-cp376; do
#for model_name in vicuna-7b-abl-selected-cp188 ; do
    load_option=""
    if [[ ${model_name} == *"13b"* ]]; then
	load_option="--load_float16"
    fi
    mkdir -p models/$model_name
    gsutil -m rsync -r gs://model-weights/$model_name models/$model_name
    python main.py mmlu --model_name llama --model_path models/${model_name}  ${load_option}
done
