#!/bin/zsh

conda run --no-capture-output -n web3-agent \
python app/run_svc.py \
  --debug-mode=true \
  --host="0.0.0.0" \
  --port=8105 \
  --model-config=".config/model.json" \
  --chain-config=".config/chain.json"
