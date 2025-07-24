# LM Studio configs – change the order of config_list to set the default model

llama3_8b_instruct_config = {
    "model": "llama-3-8b-instruct",
    "api_key": "not-needed",
    "api_type": "openai",
    "base_url": "http://localhost:1234/v1",
    "price": [0.0, 0.0],
}

mixtral_latest_config = {
    "model": "mixtral-latest",
    "api_key": "not-needed",
    "api_type": "openai",
    "base_url": "http://localhost:1234/v1",
    "price": [0.0, 0.0],
}

mistral_7b_config = {
    "model": "mistral-7b",
    "api_key": "not-needed",
    "api_type": "openai",
    "base_url": "http://localhost:1234/v1",
    "price": [0.0, 0.0],
}

phi3_latest_config = {
    "model": "phi3-latest",
    "api_key": "not-needed",
    "api_type": "openai",
    "base_url": "http://localhost:1234/v1",
    "price": [0.0, 0.0],
}

qwen_7b_k_m_config = {
    "model": "qwen-7b-k-m",
    "api_key": "not-needed",
    "api_type": "openai",
    "base_url": "http://localhost:1234/v1",
    "price": [0.0, 0.0],
}

cas_nous_hermes_2_mistral_7b_dpo_latest_config = {
    "model": "cas-nous-hermes-2-mistral-7b-dpo-latest",
    "api_key": "not-needed",
    "api_type": "openai",
    "base_url": "http://localhost:1234/v1",
    "price": [0.0, 0.0],
}

dolphin_mistral_latest_config = {
    "model": "dolphin-mistral-latest",
    "api_key": "not-needed",
    "api_type": "openai",
    "base_url": "http://localhost:1234/v1",
    "price": [0.0, 0.0],
}

lmstudio_config = {
    "model": "llama3.1-8b",
    "api_key": "not-needed",
    "api_type": "openai",
    "base_url": "http://localhost:1234/v1",
    "price": [0.0, 0.0],
}

abedalswaity7_flux_prompt_latest_config = {
    "model": "abedalswaity7-flux-prompt-latest",
    "api_key": "not-needed",
    "api_type": "openai",
    "base_url": "http://localhost:1234/v1",
    "price": [0.0, 0.0],
}

llama3_2_3b_config = {
    "model": "llama3.2-3b",
    "api_key": "not-needed",
    "api_type": "openai",
    "base_url": "http://localhost:1234/v1",
    "price": [0.0, 0.0],
}

gemma_3_12b_it_qat_config = {
    "model": "gemma-3-12b-it-qat",
    "api_key": "not-needed",
    "api_type": "openai",
    "base_url": "http://localhost:1234/v1",
    "price": [0.0, 0.0],
}

openai_config = {
    "model": "gpt-4",
    "api_key": "your-openai-api-key",
    "api_type": "openai",
    "base_url": "https://api.openai.com/v1",
    "price": [0.03, 0.06],
}

llm_config = {
    # The order of config_list determines the default model used in LM Studio.
    "config_list": [
        openai_config,
        mistral_7b_config,
        llama3_8b_instruct_config,
        lmstudio_config,
        mixtral_latest_config,
        phi3_latest_config,
        qwen_7b_k_m_config,
        cas_nous_hermes_2_mistral_7b_dpo_latest_config,
        dolphin_mistral_latest_config,
        abedalswaity7_flux_prompt_latest_config,
        llama3_2_3b_config,
        gemma_3_12b_it_qat_config,
    ],
    "cache_seed": None,
}