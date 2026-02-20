import time
from crayon import CrayonVocab

vocab = CrayonVocab(device="auto")
vocab.load_profile("lite")

# Longer text for more accurate speed measurement
long_text = "CRAYON is a hyper-fast tokenizer designed for modern AI. It offers unparalleled speed and efficiency in processing large volumes of text data. This advanced tokenization library supports various hardware accelerators, including AVX2 on CPUs, CUDA on NVIDIA GPUs, and ROCm on AMD GPUs, ensuring optimal performance across different computing environments. Its highly optimized algorithms and efficient memory management make it an ideal choice for applications requiring rapid text processing, such as natural language understanding, machine translation, and large-scale data analysis. The 'lite' profile provides a balanced vocabulary size suitable for many common tasks, delivering quick results without compromising accuracy significantly. Users can expect consistent and reliable performance, making CRAYON a robust solution for cutting-edge AI development. " * 100 # Repeat 100 times to make it significantly longer
text = long_text

start_time = time.time()
tokens = vocab.tokenize(text)
end_time = time.time()

decoded = vocab.decode(tokens)

print(f"Original text (first 100 chars): {text[:100]}...")
print(f"Tokens (first 10): {tokens[:10]}...")
print(f"Decoded text (first 100 chars): {decoded[:100]}...")
print(f"Number of tokens: {len(tokens)}")
print(f"Time taken for tokenization: {end_time - start_time:.4f} seconds")

# Calculate and print tokens per second
num_tokens = len(tokens)
time_taken = end_time - start_time
if time_taken > 0:
    tokens_per_second = num_tokens / time_taken
    million_tokens_per_second = tokens_per_second / 1_000_000
    print(f"Tokenization speed: {million_tokens_per_second:.2f} Mn toks/s")
else:
    print("Time taken was too short to calculate a meaningful tokens per second rate.")