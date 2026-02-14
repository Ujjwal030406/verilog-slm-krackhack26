import os
import re
import torch
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from transformers import AutoModelForCausalLM, AutoTokenizer

app = Flask(__name__, static_folder='static')
CORS(app)

# Model Configuration
MODEL_NAME = "smolify/smolified-krackhack26verilog"
DEVICE = "cpu"

print(f"⚡ Sovereign AI System Initializing...")
print(f"⚡ Device: {DEVICE}")
print(f"⚡ Loading Model: {MODEL_NAME} (This may take a while on first run)...")

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float32,
    )
    print("⚡ System Online. Waiting for inputs.")
except Exception as e:
    print(f"❌ CRITICAL ERROR: Failed to load model.\n{e}")
    model = None
    tokenizer = None

SYSTEM_PROMPT = (
    "The user will describe a digital circuit. Your task is to generate "
    "synthesizable Verilog code that implements the described circuit for "
    "FPGA synthesis. Ensure all code is synthesizable and follows good "
    "Verilog practices."
)

@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')

@app.route('/generate', methods=['POST'])
def generate_verilog():
    if not model or not tokenizer:
        return jsonify({"error": "Model failed to load. Check server logs."}), 500

    data = request.json
    prompt = data.get('prompt', '')

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    print(f"⚡ Received Prompt: {prompt}")

    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': prompt}
    ]

    try:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        if text.startswith('<bos>'):
            text = text[len('<bos>'):]

        inputs = tokenizer(text, return_tensors="pt")
        input_len = inputs['input_ids'].shape[1]

        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id if tokenizer.eos_token_id is not None else 0,
            )

        generated_ids = output_ids[0][input_len:]
        generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)
        generated_text = generated_text.strip()

        # Strip markdown code fences
        generated_text = re.sub(r'^```\w*\s*', '', generated_text)
        generated_text = re.sub(r'\s*```\s*$', '', generated_text)
        generated_text = generated_text.strip()

        # Format single-line Verilog into multi-line
        keywords_newline_before = [
            'module', 'input', 'output', 'wire', 'reg', 'assign',
            'always', 'initial', 'begin', 'end', 'endmodule',
            'if', 'else', 'case', 'endcase', 'parameter',
            'localparam', 'genvar', 'generate', 'endgenerate'
        ]
        for kw in keywords_newline_before:
            generated_text = re.sub(r'(?<!\n)\s+(' + kw + r'\b)', r'\n\1', generated_text)

        # Add indentation
        lines = generated_text.split('\n')
        formatted_lines = []
        indent_level = 0
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith('end') or line.startswith(');'):
                indent_level = max(0, indent_level - 1)
            formatted_lines.append('  ' * indent_level + line)
            if line.startswith('module') or line.startswith('begin') or line.startswith('always') or line.startswith('initial') or line.startswith('case') or line.startswith('generate'):
                indent_level += 1

        generated_text = '\n'.join(formatted_lines)

        print("⚡ Generation Complete.")
        return jsonify({"code": generated_text})

    except Exception as e:
        print(f"❌ Generation Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 7860))
    app.run(host='0.0.0.0', port=port, debug=False)
